# Writeback Application with Dash AG-Grid and PostgreSQL

Author: [David O'Keeffe](https://www.linkedin.com/in/dgokeeffe/)

This is an example of reading and writing tables to a PostgreSQL database using Dash AG-Grid, one of the most powerful Javascript libraries for Tabular visualization on the market.

It includes the ability to add validation steps and show warnings for duplicate keys and missing inputs, and disable submitting the table if the validations aren't acceptable. It provides an "Microsoft Excel" like experience for users to do things like submit a request for a forecast.

It's a complete example for building sophisticated multi-page apps using the latest libraries in the Python ecosystem. This includes tools like `uv`, `pytest` (for TDD and automated unit tests), and modern PostgreSQL database patterns.

> **Note**: This application was migrated from Databricks Unity Catalog to PostgreSQL (Lakebase).


## 🚀 Quick Start

### Run Locally (3 commands)

```bash
# 1. Copy and configure environment
cp example.env .env
# Edit .env: Set LAKEBASE_INSTANCE_NAME=your-instance-name

# 2. Run the application
export $(grep -v '^#' .env | xargs) && uv run python -m src.dash_dbx_writeback

# 3. Open browser
# Navigate to http://localhost:8050
```

**Prerequisites:**
- Python 3.11+, `uv` package manager
- Databricks CLI configured: `databricks configure --token`
- Lakebase instance name

**That's it!** Everything else (username, host, OAuth tokens) auto-populates via WorkspaceClient.

---

### Deploy (3 commands)

```bash
databricks auth login --host https://<workspace> --profile <PROFILE>
databricks bundle deploy -t dev --var instance_name=<LAKEBASE_INSTANCE> --profile <PROFILE>
databricks bundle open excel_the_dash_way -t dev --profile <PROFILE>
```

| Variable | Meaning |
|---|---|
| `instance_name` | Lakebase database instance name |
| `database` | Database in that instance (default `databricks_postgres`) |

The bundle grants the app's service principal `CAN_CONNECT_AND_CREATE` on the database; `PGHOST`, `PGDATABASE`, `PGUSER` and `PGPORT` are injected automatically. On each start, `app.yml` runs `initialize_app` once (create and seed tables) and then serves the app with gunicorn.

## Prerequisites

1. **Databricks Lakebase PostgreSQL**
   - Access to a Databricks workspace with Lakebase enabled
   - A Lakebase PostgreSQL instance created in your workspace
   - Databricks personal access token for authentication
   - Connection details (hostname, database name, username)

2. **Python 3.11+** and **uv** package manager
   ```bash
   # Install uv if you don't have it
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Databricks CLI** (for authentication)
   ```bash
   # Install Databricks CLI
   pip install databricks-cli
   
   # Configure authentication
   databricks configure --token
   ```

## Features

- 📊 **Excel-like Grid**: Edit data with AG-Grid's powerful interface
- 💾 **Database Writeback**: Persist changes directly to PostgreSQL
- 📈 **Forecast Management**: Submit and track forecast requests
- 🔄 **Real-time Updates**: Changes reflected immediately
- 📁 **CSV Upload**: Bulk import data from CSV files
- 🎨 **Modern UI**: Built with Dash Mantine Components

## Running Locally

### Architecture Overview

This application **always connects to Databricks Lakebase PostgreSQL** - both when running locally and when deployed to Databricks Apps. The only difference is how credentials are provided:

- **Local Development**: You manually set environment variables in a `.env` file
- **Databricks Deployment**: Environment variables are automatically injected from the database resource

### Environment Configuration

The application uses **standard PostgreSQL environment variables** (`PGHOST`, `PGPORT`, etc.) that point to your Databricks Lakebase instance.

### Setup Steps

1. Clone this repo to your local machine:
   ```bash
   git clone https://github.com/databricks-solutions/databricks-apps-examples.git
   cd databricks-apps-examples/dash-dbx-writeback
   ```

2. Create and activate a Python virtual environment:
   ```bash
   uv venv --python 3.11
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   # Or for development with testing dependencies
   uv pip install -e ".[dev]"
   ```

4. Configure Databricks CLI authentication:
   ```bash
   # Install Databricks CLI if not already installed
   pip install databricks-cli
   
   # Configure authentication with your workspace
   databricks configure --token
   # Enter your workspace URL and personal access token when prompted
   ```

5. Get your Lakebase instance name:
   
   Navigate to your Databricks workspace:
   1. Go to **SQL** → **Databases** (or check your Lakebase configuration)
   2. Find your Lakebase database instance name
   3. Note down the instance name (e.g., `daveok`, `my-instance`)

6. Configure environment variables:
   ```bash
   # Copy the example environment file
   cp example.env .env
   ```
   
   Edit `.env` and set your instance name:
   ```bash
   LAKEBASE_INSTANCE_NAME=your-instance-name
   ```
   
   That's it! Everything else is auto-populated via WorkspaceClient.

7. **Run the application:**
   ```bash
   export $(grep -v '^#' .env | xargs) && uv run python -m src.dash_dbx_writeback
   ```

8. Open your browser and navigate to: `http://localhost:8050`

> **What happens automatically:**
> - Username populated from `w.current_user.me().user_name`
> - Host populated from `w.database.get_database_instance(name).read_write_dns`
> - OAuth tokens generated and rotated automatically
> 
> See `example.env` for advanced configuration options.

### How It Works

**Local Development (Simplified):**
- You only set `LAKEBASE_INSTANCE_NAME` in your `.env` file
- WorkspaceClient automatically populates:
  - `PGUSER` from `w.current_user.me().user_name`
  - `PGHOST` from `w.database.get_database_instance(name=instance_name).read_write_dns`
  - `PGDATABASE` defaults to `databricks_postgres`
- OAuth tokens are automatically generated and rotated via `RotatingTokenConnection`
- Databricks CLI handles authentication (set up via `databricks configure --token`)

**Databricks Deployment:**
- The `app.yml` references the `postgres-database` resource
- Databricks automatically injects `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`
- The config detects these variables and uses them directly
- OAuth tokens are generated using the app's service principal
- No need to set `LAKEBASE_INSTANCE_NAME` in production

### Important Notes

- **Single Source of Truth**: The application always uses the same Databricks Lakebase instance
- **No Local PostgreSQL Needed**: You don't need to run PostgreSQL locally - just connect to Lakebase
- **OAuth Authentication**: The app uses OAuth tokens instead of passwords for secure authentication
- **Automatic Token Rotation**: Tokens are generated fresh for each connection and automatically rotated
- **Development/Production Parity**: Same database in both environments ensures consistency

> [!NOTE]
> - Tables are created and seeded once per app start (`python -m src.dash_dbx_writeback.initialize_app` in `app.yml`; the local `python -m src.dash_dbx_writeback` does the same)
> - Uploaded CSV headers become column names; they are quoted with `quote_ident` so a header can't inject SQL

## 📂 Project Structure

```
dash-dbx-writeback/
├── app.yml                       # Apps runtime: init tables, then gunicorn
├── databricks.yml                # Bundle: variables, dev/prod targets
├── resources/excel_the_dash_way.yml  # App + Lakebase resource
├── example.env                   # Local configuration template
├── src/dash_dbx_writeback/
│   ├── app.py                    # Dash app (exposes `server` for gunicorn)
│   ├── initialize_app.py         # Create/seed tables
│   ├── config.py                 # Lakebase connection settings
│   ├── database_operations.py    # Connection pool, OAuth token rotation, SQL helpers
│   ├── callbacks/ components/ pages/
│   └── sample_data.py
└── tests/                        # `-m "not integration"` runs without a database
```

## 🆘 Troubleshooting

### Running the Application

**Command to run:**
```bash
export $(grep -v '^#' .env | xargs) && uv run python -m src.dash_dbx_writeback
```

**Common Issues:**

**`PGHOST not set` error?**
- Create `.env` file: `cp example.env .env`
- Set `LAKEBASE_INSTANCE_NAME=your-instance-name` in `.env`
- Ensure you run the export command before running the app

**`Module not found` error?**
- Verify you're using the correct module path: `src.dash_dbx_writeback`
- Run from project root directory
- Ensure dependencies installed: `uv pip install -e .`

**Connection issues?**
- Verify Databricks CLI is configured: `databricks configure --token`
- Check Lakebase instance is running in your workspace
- Test WorkspaceClient: `uv run python -c "from databricks.sdk import WorkspaceClient; print(WorkspaceClient().current_user.me().user_name)"`

**OAuth/Authentication errors?**
- Run `databricks configure --token` to authenticate
- Verify your Databricks token is valid
- Check your user has access to the Lakebase instance

**Permission denied?**
- Ensure your Databricks user has `CAN_CONNECT_AND_CREATE` permission
- Check schema permissions for `LAKEBASE_SCHEMA`

**Database instance not found?**
- Verify instance name is correct: Check in Databricks SQL → Databases
- Ensure instance is running and accessible

---

&copy; 2025 Databricks, Inc. All rights reserved. The source in this repository is provided subject to the Databricks License [https://databricks.com/db-license-source]. All included or referenced third party libraries are subject to the licenses set forth below.

| library                  | description                                        | license      | source                                              |
| ------------------------ | -------------------------------------------------- | ------------ | --------------------------------------------------- |
| dash                     | Framework for building analytical web applications | MIT          | https://github.com/plotly/dash                      |
| dash-ag-grid             | AG Grid Plugin for Dash apps                       | MIT          | https://github.com/plotly/dash-ag-grid              |
| dash_mantine_components  | Mantine components for Dash                        | MIT          | https://github.com/snehilvj/dash-mantine-components |
| gunicorn                 | WSGI HTTP server                                   | MIT          | https://github.com/benoitc/gunicorn                 |
| pandas                   | Data analysis and manipulation library             | BSD 3-Clause | https://github.com/pandas-dev/pandas                |
| psycopg2-binary          | PostgreSQL adapter for Python                      | LGPL         | https://github.com/psycopg/psycopg2                 |
| SQLAlchemy               | SQL toolkit and ORM for Python                     | MIT          | https://github.com/sqlalchemy/sqlalchemy            |

Databricks support doesn't cover this content. For questions or bugs, please open a github issue and the team will help on a best effort basis.

---

## Questions and issues
Please file an issue on this repository when and if you run into errors with the deployed applications. Thanks!
