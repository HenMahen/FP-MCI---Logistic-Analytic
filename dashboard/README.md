# Delivery Operations Dashboard

Streamlit + Plotly app for the DustiniaDelixia gold mart.

## Run locally

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

The app resolves the mart automatically:

1. `DustiniaDelixia_Groceria/fact_operational_delivery.csv`
2. `fact_operational_delivery.csv` at the repository root
3. `dashboard/data/fact_operational_delivery.csv`

Refresh the CSV from ClickHouse after a dbt run:

```bash
python DustiniaDelixia_Groceria/download_fact.py
```

## Deploy to Streamlit Community Cloud

1. Push the repository to GitHub.
2. Go to <https://share.streamlit.io> -> **New app**.
3. Repository: `Mahendra-TC24/FP-MCI---Logistic-Analytic`
4. Main file path: `dashboard/app.py`
5. Python dependencies are read from `dashboard/requirements.txt`.

No secrets, database connection, or API key is required: the dashboard reads the
committed gold mart CSV, so the public demo is free and always available.
