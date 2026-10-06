# Databricks Apps: FastAPI on-behalf-of-user example

A minimal Python JSON backend for Databricks Apps. Every query runs **as the signed-in user** (on-behalf-of-user auth), so Unity Catalog permissions, row filters, column masks and audit logs apply to that person, not to the app.

| Route | Returns |
|---|---|
| `GET /api/health` | `{"status": "ok"}` |
| `GET /api/whoami` | The signed-in user's email (from `X-Forwarded-Email`) |
| `GET /api/tables/{catalog.schema.table}?limit=100` | Up to 1000 rows, read with the user's token |
| `GET /docs` | Interactive OpenAPI docs |

What it shows (see [PATTERNS.md](../PATTERNS.md)):
- The user token comes from `X-Forwarded-Access-Token`. When deployed, a missing token returns 401; the app never falls back to its service principal.
- The table name is bound with `IDENTIFIER(:table_name)` and `limit` is a validated integer, so neither can inject SQL.
- The warehouse comes from an app resource via `valueFrom`, and the app is served by uvicorn on port 8000.

## Deploy

```bash
databricks auth login --host https://<workspace> --profile <PROFILE>
databricks bundle deploy -t dev --var warehouse_id=<WAREHOUSE_ID> --profile <PROFILE>
databricks bundle open fastapi_obo -t dev --profile <PROFILE>
```

**Permissions.** The bundle grants the app's service principal `CAN_USE` on the warehouse and requests the `sql` user API scope. Users need their own `SELECT` grants on whatever they query.

## Run locally

Locally there is no proxy header, so queries use your Databricks CLI credentials:

```bash
export DATABRICKS_CONFIG_PROFILE=<PROFILE> DATABRICKS_WAREHOUSE_ID=<WAREHOUSE_ID>
uv run --no-project --with-requirements requirements.txt uvicorn app:app --reload
curl "localhost:8000/api/tables/samples.nyctaxi.trips?limit=5"
```

Test: `uv run --no-project --with-requirements requirements.txt --with pytest --with httpx python -m pytest`

---

&copy; 2026 Databricks, Inc. All rights reserved. The source in this example is provided subject to the Databricks License [https://databricks.com/db-license-source]. All included or referenced third party libraries are subject to the licenses set forth below.

| library | description | license | source |
|---|---|---|---|
| fastapi | Modern, fast web framework for building APIs with Python | MIT | https://github.com/tiangolo/fastapi |
| uvicorn | Lightning-fast ASGI server | BSD 3-Clause | https://github.com/encode/uvicorn |
| databricks-sdk | Databricks SDK for Python | Apache 2.0 | https://github.com/databricks/databricks-sdk-py |
| databricks-sql-connector | Databricks SQL Connector for Python | Apache 2.0 | https://github.com/databricks/databricks-sql-python |
