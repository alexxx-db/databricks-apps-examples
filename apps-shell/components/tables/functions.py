import os
from databricks import sql
from databricks.sdk.core import Config

# Injected by the sql-warehouse resource; set it in your shell locally
DATABRICKS_SQL_WAREHOUSE_ID = os.environ["DATABRICKS_SQL_WAREHOUSE_ID"]

cfg = Config()


def get_connection():
    return sql.connect(
        server_hostname=cfg.host,
        http_path=f"/sql/1.0/warehouses/{DATABRICKS_SQL_WAREHOUSE_ID}",
        credentials_provider=lambda: cfg.authenticate,
    )


def read_table(table_name, conn):
    with conn.cursor() as cursor:
        # IDENTIFIER() binds the user-supplied name as a parameter, never as SQL text
        cursor.execute(
            "SELECT * FROM IDENTIFIER(:table_name) LIMIT 100", {"table_name": table_name}
        )
        df = cursor.fetchall_arrow().to_pandas()
        return df
