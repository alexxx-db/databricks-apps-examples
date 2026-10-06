# Databricks Apps patterns

The conventions every example in this repo follows. Copy these, not the quirks of any single app.

## Pick a stack

| Need | Start from |
|---|---|
| New app, no strong language preference | [`appkit-analytics`](appkit-analytics/) (AppKit: TypeScript/React, typed SQL queries) |
| Python backend / JSON API | [`fastapi-obo`](fastapi-obo/) (FastAPI + uvicorn) |
| Python team that wants a dashboard-style UI | [`apps-shell`](apps-shell/), [`dash-dbx-writeback`](dash-dbx-writeback/) (Dash) |
| ML demo / document UI | [`vector-search`](vector-search/) (Gradio) |

A plain read-only dashboard usually doesn't need an app at all; use an AI/BI dashboard.

## Auth: who does the query run as?

| | Service principal (app auth) | On-behalf-of-user (user auth) |
|---|---|---|
| Credentials | `Config()` / `WorkspaceClient()`, injected automatically | `X-Forwarded-Access-Token` request header |
| UC permissions, row filters, column masks | The app's | The signed-in user's |
| Audit log shows | The service principal | The user |
| Enable with | Nothing | `user_api_scopes: [sql]` on the app in `databricks.yml` |
| Use for | Shared reference data, background work, Lakebase | Reading or writing governed UC data |

Rules:
- Default to on-behalf-of-user for Unity Catalog reads and writes so governance applies to the person using the app. See `fastapi-obo/app.py`, `auth-demo/auth.py`, and AppKit's `*.obo.sql` queries.
- Never fall back to the service principal when a user token is missing in a deployed app; return 401 (`fastapi-obo/app.py`).
- When writes do run as the service principal (e.g. Lakebase), store the user from `X-Forwarded-Email` in a server-set column (`created_by` / `updated_by` in `apps-write-back`, `SUBMITTED_BY` in `dash-dbx-writeback`). Ignore any value the browser sends for it.
- The header doesn't exist locally, so local runs use your CLI credentials.

## Never build SQL from user input

- Table names: `SELECT * FROM IDENTIFIER(:table_name)` with a named parameter (`auth-demo/sql.py`).
- Values: always parameters (`?` / `:name` for the SQL connector, `%s` for psycopg).
- Column names from a grid: reject anything not in an explicit editable-column allowlist (`EDITABLE_COLUMNS` in `apps-write-back/src/pages/table_edit.py`). A regex stops injection but still lets a tampered request write hidden columns.
- Column names from a CSV upload, which become new columns: escape them with `quote_ident` (`dash-dbx-writeback/.../database_operations.py`). Quoting with backticks or double quotes alone is not enough.
- Required config (`DATABRICKS_WAREHOUSE_ID`, `PGHOST`): read with `os.environ[...]` so a missing value fails at startup with its name, not later as host `None`.

## Resources, not IDs

Declare every warehouse, database, endpoint and index as an app resource in `databricks.yml`, with the least permission that works. Read it in `app.yaml` via `valueFrom`:

```yaml
# databricks.yml
resources:
  - name: sql-warehouse
    sql_warehouse: { id: ${var.warehouse_id}, permission: CAN_USE }

# app.yaml
env:
  - name: DATABRICKS_WAREHOUSE_ID
    valueFrom: sql-warehouse
```

Deploying grants the permission to the app's service principal. A Lakebase `database` resource injects `PGHOST`, `PGDATABASE`, `PGUSER` and `PGPORT` itself, so there's nothing to hardcode. Workspace hosts belong in your CLI profile, not in `databricks.yml`.

## Data path

| Workload | Use |
|---|---|
| Analytical reads, aggregations, charts | SQL warehouse |
| Transactional writes, forms, grid edits, low-latency lookups | Lakebase (Postgres) |
| Lakebase data needed for analytics | Synced tables / scheduled MERGE into Unity Catalog |

Avoid bulk `INSERT ... VALUES (?, ?, …)` through the warehouse for app writes. It hits parameter and statement limits and rewrites the table on every save.

## Lakebase connections

- Use the workspace OAuth token as the password, fetched per connection with `WorkspaceClient().config.oauth_token().access_token` (`RotatingTokenConnection` in `dash-dbx-writeback`). The SDK refreshes it before its 1-hour expiry, so never store one for the pool's lifetime.
- Don't derive the instance name from `PGHOST`. Hostnames look like `ep-jolly-river-….database…` and don't contain the name, so `generate_database_credential(instance_names=[...])` fails with "instance not found".
- Keep pools small (around 5). An app has 2 vCPUs, and Lakebase connections are a shared, limited resource.
- `psycopg` is not preinstalled, so list it in `requirements.txt`.

## Serving

- Bind to `0.0.0.0` on `DATABRICKS_APP_PORT` (8000). Never use 8080.
- Use a production server: `gunicorn app:server` for Dash/Flask, `uvicorn` for FastAPI. Never the framework's dev server or `debug=True`.
- The Apps proxy cuts requests at 120s, so set `gunicorn --timeout=120`. The 30s default kills queries on a cold warehouse.
- Pass `__name__` to `Dash(...)` so assets and pages resolve under gunicorn.
- Don't open connections or run DDL at import time. Run schema setup once before workers start (`dash-dbx-writeback/app.yml`) or in a setup script.
- Only stdout/stderr are kept. Log with `logging`, and don't log tokens or user data.

## Deploy

Every app is a bundle with `dev` (default) and `prod` targets:

```bash
databricks auth login --host https://<workspace> --profile <PROFILE>
databricks bundle deploy -t dev --var warehouse_id=<ID> --profile <PROFILE>
databricks bundle open <app_key> -t dev --profile <PROFILE>
```

`lifecycle.started: true` starts the app on deploy. Deploy `prod` from CI as a service principal. CI (`.github/workflows/ci.yml`) lints, runs the offline tests, checks each `requirements.txt` resolves on Python 3.11 (the Apps runtime), and, when workspace secrets are configured, runs `bundle validate --strict` on every app.
