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

The interactive setup scripts seed the example tables and grant the app's service principal (the `service_principal_client_id` from step 2) access to them:

```bash
uv run python setup/setup_delta_tables.py
uv run python setup/setup_postgres_tables.py
```

## Local development

To run the application locally for development:

1. **Authenticate with Databricks:**

   ```bash
   databricks auth login --host <databricks-workspace-url> --profile <my-profile>
   ```

2. **Start the application** (set `DATABRICKS_WAREHOUSE_ID` and `PGHOST` in `.env` first; these are injected automatically when deployed):

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
