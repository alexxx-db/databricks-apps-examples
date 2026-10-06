# Databricks Apps: Dash multi-page shell

A starting skeleton for a multi-page Dash app. Pages in `components/` register themselves with `dash.register_page(...)`, and the navbar groups them by their `category`. It ships with a home page and a "Read a table" page. The table name is bound with `IDENTIFIER(:table_name)` and runs on the app's SQL warehouse. The "Edit a table" page is an empty placeholder.

## Deploy

```bash
databricks auth login --host https://<workspace> --profile <PROFILE>
databricks bundle deploy -t dev --var warehouse_id=<WAREHOUSE_ID> --profile <PROFILE>
databricks bundle open apps_shell -t dev --profile <PROFILE>
```

**Permissions.** The bundle grants the app's service principal `CAN_USE` on the warehouse. Grant it `USE CATALOG`, `USE SCHEMA` and `SELECT` on the tables it should read. Queries run as the service principal; see [PATTERNS.md](../PATTERNS.md) for when to switch to on-behalf-of-user auth.

## Run locally

```bash
export DATABRICKS_CONFIG_PROFILE=<PROFILE> DATABRICKS_SQL_WAREHOUSE_ID=<WAREHOUSE_ID>
uv run --no-project --python 3.11 --with-requirements requirements.txt python app.py   # http://localhost:8050
```

Deployed, the app runs under gunicorn (`app.yaml`). Set `DASH_DEBUG=true` locally for Dash dev tools.

---

&copy; 2025 Databricks, Inc. All rights reserved. The source in this example is provided subject to the Databricks License [https://databricks.com/db-license-source]. All included or referenced third party libraries are subject to the licenses set forth below.

| library | description | license | source |
|---|---|---|---|
| dash | Framework for building analytical web applications | MIT | https://github.com/plotly/dash |
| dash_mantine_components | Mantine components for Dash | MIT | https://github.com/snehilvj/dash-mantine-components |
| dash-iconify | Icon components for Dash apps | MIT | https://github.com/snehilvj/dash-iconify |
| databricks-sdk | Databricks SDK for Python | Apache 2.0 | https://github.com/databricks/databricks-sdk-py |
| databricks-sql-connector | Databricks SQL Connector for Python | Apache 2.0 | https://github.com/databricks/databricks-sql-python |
| gunicorn | WSGI HTTP server | MIT | https://github.com/benoitc/gunicorn |
