import pandas as pd
from clickhouse_driver import Client

# Hubungkan ke ClickHouse lokal (port 9000)
client = Client(host='localhost', port=9000)

# Tarik data dari fact table
query = "SELECT * FROM fact_operational_delivery"
data, columns = client.execute(query, with_column_types=True)

# Simpan ke CSV
df = pd.DataFrame(data, columns=[col[0] for col in columns])
df.to_csv('fact_operational_delivery.csv', index=False)
print("Berhasil mengunduh fact_operational_delivery.csv")
