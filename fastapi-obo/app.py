import os

from databricks import sql
from databricks.sdk.core import Config
from databricks.sql.exc import ServerOperationError
from fastapi import FastAPI, Header, HTTPException, Query

cfg = Config()
WAREHOUSE_HTTP_PATH = f"/sql/1.0/warehouses/{os.getenv('DATABRICKS_WAREHOUSE_ID')}"
DEPLOYED = os.getenv("DATABRICKS_APP_NAME") is not None

app = FastAPI(title="Databricks Apps FastAPI example")


def connect(user_token: str | None):
    """Query as the signed-in user (on-behalf-of-user auth), so UC permissions and audit apply to them."""
    if user_token:
        return sql.connect(server_hostname=cfg.host, http_path=WAREHOUSE_HTTP_PATH, access_token=user_token)
    if DEPLOYED:
        # Never fall back to the app's service principal for user requests
        raise HTTPException(401, "Missing user token; is `sql` in the app's user_api_scopes?")
    # Local dev: no proxy header, so use your CLI credentials
    return sql.connect(server_hostname=cfg.host, http_path=WAREHOUSE_HTTP_PATH, credentials_provider=lambda: cfg.authenticate)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/whoami")
def whoami(x_forwarded_email: str | None = Header(None)):
    return {"user": x_forwarded_email}


@app.get("/api/tables/{table_name}")
def read_table(
    table_name: str,
    limit: int = Query(100, ge=1, le=1000),
    x_forwarded_access_token: str | None = Header(None),
):
    with connect(x_forwarded_access_token) as conn, conn.cursor() as cursor:
        try:
            # IDENTIFIER() binds the name as a parameter; limit is a validated int
            cursor.execute(f"SELECT * FROM IDENTIFIER(:table_name) LIMIT {limit}", {"table_name": table_name})
        except ServerOperationError as e:  # bad name or no permission for this user
            raise HTTPException(400, str(e).strip().splitlines()[0]) from e
        columns = [c[0] for c in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
