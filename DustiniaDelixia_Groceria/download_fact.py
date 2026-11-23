"""
Export the dbt gold fact table to CSV for the public Streamlit dashboard.

Usage:
    python download_fact.py
    python download_fact.py --output fact_operational_delivery.csv

Connection values come from environment variables, with local defaults:
    CLICKHOUSE_HOST=localhost
    CLICKHOUSE_NATIVE_PORT=9000
    CLICKHOUSE_USER=default
    CLICKHOUSE_PASSWORD=
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from clickhouse_driver import Client

DEFAULT_TABLE = os.getenv("FACT_TABLE", "gold.fct_operational_delivery")
BASE_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--table",
        default=DEFAULT_TABLE,
        help=f"ClickHouse table to export (default: {DEFAULT_TABLE})",
    )
    parser.add_argument(
        "--output",
        default=str(BASE_DIR / "fact_operational_delivery.csv"),
        help="Destination CSV path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = Client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_NATIVE_PORT", "9000")),
        user=os.getenv("CLICKHOUSE_USER", "default"),
        password=os.getenv("CLICKHOUSE_PASSWORD", ""),
    )

    try:
        rows, columns = client.execute(
            f"SELECT * FROM {args.table}", with_column_types=True
        )
    except Exception as exc:  # noqa: BLE001 - surface a clear operator message
        print(f"Failed to read {args.table}: {exc}", file=sys.stderr)
        print(
            "Is ClickHouse running and has `dbt run` created the gold layer?",
            file=sys.stderr,
        )
        return 1

    frame = pd.DataFrame(rows, columns=[column[0] for column in columns])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False, encoding="utf-8")

    print(f"Exported {len(frame):,} rows from {args.table} -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
