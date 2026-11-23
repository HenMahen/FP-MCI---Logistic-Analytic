# DustiniaDelixia Groceria — custom Airflow image
# Airflow runtime and dbt runtime are isolated in two Python environments:
#   /home/airflow/.local  -> Airflow + ingestion dependencies
#   /opt/dbt-venv         -> dbt-core + dbt-clickhouse (on PATH)
# This prevents dbt upgrades from destabilising the Airflow scheduler.
FROM apache/airflow:2.10.5-python3.11

LABEL maintainer="DustiniaDelixia Groceria Team"
LABEL description="Airflow 2.10.5 + ClickHouse drivers + isolated dbt-clickhouse runtime"

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dbt.txt /tmp/

# Dedicated dbt environment, owned by root but readable/executable by airflow.
RUN python -m venv /opt/dbt-venv \
    && /opt/dbt-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/dbt-venv/bin/pip install --no-cache-dir -r /tmp/requirements-dbt.txt

ENV PATH="/opt/dbt-venv/bin:${PATH}"

# Airflow runtime dependencies.
USER airflow
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt /tmp/requirements-dbt.txt
