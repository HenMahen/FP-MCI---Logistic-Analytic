"""
DAG: operational_analyst_dag.py

Modern ELT pipeline for DustiniaDelixia Groceria.

    Extract + Load (Airflow)          Transform + Test (dbt)
    ------------------------          ------------------------
    CSV -> ClickHouse Bronze   ->     Silver staging/intermediate
                                      Gold marts + data quality tests

The DAG intentionally contains no business transformations and no custom
data-quality checks: `dbt run` and `dbt test` own that contract.

Connections:
    clickhouse_default (host clickhouse, native port 9000)
    dbt profile        (HTTP port 8123, DBT_PROFILES_DIR=/opt/airflow/dbt_dustinia)
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

import pandas as pd
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from clickhouse_driver import Client

# ---------------------------------------------------------------------------
# Configuration (environment overrides, no hard-coded credentials)
# ---------------------------------------------------------------------------
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_NATIVE_PORT = int(os.getenv("CLICKHOUSE_NATIVE_PORT", "9000"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "default")

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_DIR, "include", "data")
SQL_DIR = os.path.join(PROJECT_DIR, "sql")
DBT_PROJECT_DIR = os.getenv("DBT_PROJECT_DIR", "/opt/airflow/dbt_dustinia")
DBT_TARGET = os.getenv("DBT_TARGET", "dev")

DEFAULT_ARGS = {
    "owner": "analytics_engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_client() -> Client:
    return Client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_NATIVE_PORT,
        user=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD,
        database=CLICKHOUSE_DB,
    )


def execute_sql_file(path: str) -> None:
    """Execute a semicolon-separated DDL file one statement at a time."""
    client = get_client()
    with open(path, encoding="utf-8") as handle:
        statements = [part.strip() for part in handle.read().split(";") if part.strip()]

    for statement in statements:
        executable_lines = [
            line
            for line in statement.splitlines()
            if line.strip() and not line.strip().startswith("--")
        ]
        sql = "\n".join(executable_lines).strip()
        if sql:
            client.execute(sql)
            logging.info("Executed: %s...", sql[:80])


def load_dataframe(table: str, dataframe: pd.DataFrame, columns: list[str]) -> None:
    """Truncate a Bronze table and insert a DataFrame with NULL-safe values."""
    client = get_client()
    client.execute(f"TRUNCATE TABLE IF EXISTS {table}")

    records = []
    for row in dataframe[columns].itertuples(index=False, name=None):
        safe_row = []
        for value in row:
            if pd.isna(value):
                safe_row.append(None)
            elif isinstance(value, pd.Timestamp):
                safe_row.append(value.to_pydatetime())
            elif hasattr(value, "item"):
                safe_row.append(value.item())
            else:
                safe_row.append(value)
        records.append(safe_row)

    client.execute(f"INSERT INTO {table} ({', '.join(columns)}) VALUES", records)
    logging.info("%s loaded: %s rows", table, f"{len(records):,}")


def read_csv(filename: str) -> pd.DataFrame:
    path = os.path.join(DATA_DIR, filename)
    dataframe = pd.read_csv(path)
    logging.info("Extracted %s: %s rows", filename, f"{len(dataframe):,}")
    return dataframe


def parse_datetimes(dataframe: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        dataframe[column] = pd.to_datetime(dataframe[column], errors="coerce")


def parse_numbers(dataframe: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")


def normalise_zip(dataframe: pd.DataFrame, column: str) -> None:
    dataframe[column] = dataframe[column].astype(str).str.replace(r"\.0$", "", regex=True)


# ---------------------------------------------------------------------------
# Bronze ingestion tasks
# ---------------------------------------------------------------------------
def create_raw_tables() -> None:
    execute_sql_file(os.path.join(SQL_DIR, "create_raw_tables.sql"))


def load_orders() -> None:
    dataframe = read_csv("orders.csv")
    parse_datetimes(
        dataframe,
        [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )
    load_dataframe(
        "raw_orders",
        dataframe,
        [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )


def load_order_items() -> None:
    dataframe = read_csv("order_items.csv")
    parse_datetimes(dataframe, ["shipping_limit_date"])
    parse_numbers(dataframe, ["price", "freight_value"])
    dataframe["order_item_id"] = pd.to_numeric(
        dataframe["order_item_id"], errors="coerce"
    ).astype("Int64")
    load_dataframe(
        "raw_order_items",
        dataframe,
        [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
    )


def load_customers() -> None:
    dataframe = read_csv("customers.csv")
    normalise_zip(dataframe, "customer_zip_code_prefix")
    load_dataframe(
        "raw_customers",
        dataframe,
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
    )


def load_sellers() -> None:
    dataframe = read_csv("sellers.csv")
    normalise_zip(dataframe, "seller_zip_code_prefix")
    load_dataframe(
        "raw_sellers",
        dataframe,
        ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"],
    )


def load_geolocation() -> None:
    dataframe = read_csv("geolocation.csv")
    normalise_zip(dataframe, "geolocation_zip_code_prefix")
    parse_numbers(dataframe, ["geolocation_lat", "geolocation_lng"])
    load_dataframe(
        "raw_geolocation",
        dataframe,
        [
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
            "geolocation_state",
        ],
    )


def load_products() -> None:
    dataframe = read_csv("products.csv")
    parse_numbers(
        dataframe,
        [
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
    )
    for column in [
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
    ]:
        dataframe[column] = dataframe[column].astype("Int64")
    load_dataframe(
        "raw_products",
        dataframe,
        [
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
    )


def load_order_reviews() -> None:
    dataframe = read_csv("order_reviews.csv")
    parse_datetimes(dataframe, ["review_creation_date", "review_answer_timestamp"])
    parse_numbers(dataframe, ["review_score"])
    dataframe["review_score"] = dataframe["review_score"].astype("Int64")
    load_dataframe(
        "raw_order_reviews",
        dataframe,
        [
            "review_id",
            "order_id",
            "review_score",
            "review_creation_date",
            "review_answer_timestamp",
        ],
    )


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="operational_analyst_dag",
    default_args=DEFAULT_ARGS,
    description="ELT: CSV -> ClickHouse Bronze -> dbt Silver/Gold -> dbt tests",
    schedule="@once",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["elt", "dbt", "clickhouse", "operational"],
) as dag:

    start = EmptyOperator(task_id="start")

    t_create_raw = PythonOperator(
        task_id="create_raw_tables",
        python_callable=create_raw_tables,
    )

    load_tasks = [
        PythonOperator(task_id="load_orders", python_callable=load_orders),
        PythonOperator(task_id="load_order_items", python_callable=load_order_items),
        PythonOperator(task_id="load_customers", python_callable=load_customers),
        PythonOperator(task_id="load_sellers", python_callable=load_sellers),
        PythonOperator(task_id="load_geolocation", python_callable=load_geolocation),
        PythonOperator(task_id="load_products", python_callable=load_products),
        PythonOperator(task_id="load_order_reviews", python_callable=load_order_reviews),
    ]

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"dbt run --profiles-dir . --target {DBT_TARGET}",
        cwd=DBT_PROJECT_DIR,
        append_env=True,
        env={"DBT_TARGET": DBT_TARGET},
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"dbt test --profiles-dir . --target {DBT_TARGET}",
        cwd=DBT_PROJECT_DIR,
        append_env=True,
        env={"DBT_TARGET": DBT_TARGET},
    )

    end = EmptyOperator(task_id="end")

    # start -> create Bronze -> parallel CSV loads -> dbt run -> dbt test -> end
    start >> t_create_raw >> load_tasks >> dbt_run >> dbt_test >> end
