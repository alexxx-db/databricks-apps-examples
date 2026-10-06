# Databricks Apps Writeback Example Application

![Screenshot of the Databricks Apps Writeback Example Application](screenshot.png)

## Overview

This example [Dash](https://dash.plotly.com/) application demonstrates **three writeback scenarios** from [Databricks Apps](https://www.databricks.com/product/databricks-apps) into [Unity Catalog](https://www.databricks.com/product/unity-catalog) tables and [Lakehouse](https://www.databricks.com/product/lakehouse) PostgreSQL tables.

### Features

1. **Form Data Collection** - Collect data through a form interface and write to a table
2. **Table Editing** - Modify existing tables using an editable grid component
3. **Excel Upload** - Replace table contents with data from uploaded Excel files

### Technologies used

- [Databricks SQL Connector for Python](https://docs.databricks.com/en/dev-tools/python-sql-connector.html) - Read and write Unity Catalog tables
- [SQLAlchemy Core](https://docs.sqlalchemy.org/en/20/core/) - Read and write Lakehouse PostgreSQL tables
- [Dash Mantine Components](https://www.dash-mantine-components.com/) - Modern UI styling
- [Dash AG Grid](https://dash.plotly.com/dash-ag-grid) - Interactive data grid component

## Prerequisites

- Python 3.11.0 or later
- [Databricks CLI](https://docs.databricks.com/en/dev-tools/cli/index.html) (latest version)
- [uv](https://docs.astral.sh/uv/) (latest version)
- Access to a [Lakehouse database instance](https://docs.databricks.com/en/lakehouse-platform/lakehouse/index.html) with `databricks_superuser` role
- Unity Catalog permissions:
  - Catalog and schema access
  - `CREATE TABLE` privilege on the schema
  - `USAGE` grant capability on catalog and schema
  - `SELECT` and `MODIFY` grant capability on tables

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/databricks-solutions/databricks-apps-examples.git
cd databricks-apps-examples/apps-write-back
```

### 2. Deploy the app

```bash
databricks auth login --host https://<workspace> --profile <PROFILE>
databricks bundle deploy -t dev --profile <PROFILE> \
  --var warehouse_id=<WAREHOUSE_ID> --var lakebase_instance=<LAKEBASE_INSTANCE>
databricks apps get apps-write-back-dev --profile <PROFILE>   # note service_principal_client_id
```

| Variable | Meaning |
|---|---|
| `warehouse_id` | SQL warehouse used for Unity Catalog reads and writes |
| `lakebase_instance` | Lakebase database instance name |
| `lakebase_database` | Database in that instance (default `databricks_postgres`) |

The bundle grants the app's service principal `CAN_USE` on the warehouse and `CAN_CONNECT_AND_CREATE` on the Lakebase database. Lakebase connection details (`PGHOST`, `PGDATABASE`, `PGUSER`, `PGPORT`) are injected automatically. Catalog, schema and Postgres schema names are plain values in `app.yaml` (`main` / `default` / `public`); change them there if you use different ones.

### 3. Database setup

The interactive setup scripts seed the example tables and grant the app's service principal (the `service_principal_client_id` from step 2) access to them. The Delta script also creates the `excel_staging` Volume in the same catalog and schema. The Excel upload stages its rows there as a Parquet file and loads them with one `INSERT OVERWRITE … FROM read_files(…)`, so the service principal gets `READ VOLUME` and `WRITE VOLUME` on it:

```bash
uv run python setup/setup_delta_tables.py
uv run python setup/setup_postgres_tables.py
```

Every write records the signed-in user (from the `X-Forwarded-Email` header the Apps proxy adds): `created_by` on form submissions and `updated_by` on grid edits. Tables created before these columns existed need them added once:

```sql
ALTER TABLE <catalog>.<schema>.form_service_calls ADD COLUMN created_by STRING;          -- Delta
ALTER TABLE <catalog>.<schema>.table_regional_compliance ADD COLUMN updated_by STRING;
ALTER TABLE <schema>.form_service_calls ADD COLUMN created_by VARCHAR(255);              -- Postgres
ALTER TABLE <schema>.table_regional_compliance ADD COLUMN updated_by VARCHAR(255);
```

## Local development

To run the application locally for development:

1. **Authenticate with Databricks:**

   ```bash
   databricks auth login --host <databricks-workspace-url> --profile <my-profile>
   ```

2. **Start the application** (set `DATABRICKS_WAREHOUSE_ID` and `PGHOST` in `.env` first; they replace the old `WAREHOUSE_HTTP_PATH` / `POSTGRES_HOST` and are injected automatically when deployed):

   ```bash
   databricks apps run-local --prepare-environment --profile <my-profile>
   ```

   The `--prepare-environment` flag sets up a Python virtual environment and installs dependencies. Use this flag on first run or after dependency changes.

## Project Structure

```
apps-write-back/
├── src/
│   ├── app.py                # Main Dash application
│   ├── pages/                # Page components
│   │   ├── form.py           # Form data entry page
│   │   ├── table_edit.py     # Table editing page
│   │   └── excel_upload.py   # Excel upload page
│   ├── database_delta.py     # Unity Catalog operations
│   ├── database_postgres.py  # PostgreSQL operations
│   └── utilities.py          # Helper functions
├── setup/                    # Database setup scripts
├── app.yaml                  # Application configuration
├── databricks.yml            # Bundle: app, resources, dev/prod targets
└── requirements.txt          # Python dependencies
```

---

&copy; 2025 Databricks, Inc. All rights reserved. The source in this example is provided subject to the Databricks License [https://databricks.com/db-license-source]. All included or referenced third party libraries are subject to the licenses set forth below.

| library | description | license | source |
|---|---|---|---|
| dash | Framework for building analytical web applications | MIT | https://github.com/plotly/dash |
| dash-ag-grid | AG Grid component for Dash | MIT | https://github.com/plotly/dash-ag-grid |
| dash_mantine_components | Mantine components for Dash | MIT | https://github.com/snehilvj/dash-mantine-components |
| dash-iconify | Icon components for Dash apps | MIT | https://github.com/snehilvj/dash-iconify |
| databricks-sdk | Databricks SDK for Python | Apache 2.0 | https://github.com/databricks/databricks-sdk-py |
| databricks-sql-connector | Databricks SQL Connector for Python | Apache 2.0 | https://github.com/databricks/databricks-sql-python |
| SQLAlchemy | SQL toolkit and ORM | MIT | https://github.com/sqlalchemy/sqlalchemy |
| psycopg | PostgreSQL adapter for Python | LGPL 3.0 | https://github.com/psycopg/psycopg |
| pandas | Data analysis and manipulation library | BSD 3-Clause | https://github.com/pandas-dev/pandas |
| pyarrow | Python library for Apache Arrow | Apache 2.0 | https://github.com/apache/arrow |
| openpyxl | Excel file reading | MIT | https://foss.heptapod.net/openpyxl/openpyxl |
| python-dotenv | .env file loading | BSD 3-Clause | https://github.com/theskumar/python-dotenv |
| gunicorn | WSGI HTTP server | MIT | https://github.com/benoitc/gunicorn |
