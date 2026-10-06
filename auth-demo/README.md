# Databricks Apps: Service Principal and OBO Authorization Demo

This code sample demonstrates how to use different authorization methods within a [Databricks App](https://docs.databricks.com/en/dev-tools/databricks-apps/index.html) to query data from a Databricks SQL Warehouse via Unity Catalog.

It showcases two authorization patterns:

1.  **Service Principal (SP) Authorization:** Uses the app's own configured Service Principal credentials (via `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET`) to connect and run queries.
2.  **On-Behalf-Of (OBO) Authorization:** Uses the accessing user's identity by leveraging the `X-Forwarded-Access-Token` header provided by Databricks when OBO is enabled for the app.

![Databricks Apps: Service Principal and OBO Authorization Demo](assets/screenshot.png "Databricks Apps: Service Principal and OBO Authorization Demo")

## Deploy

```bash
databricks auth login --host https://<workspace> --profile <PROFILE>
databricks bundle deploy -t dev --var warehouse_id=<WAREHOUSE_ID> --profile <PROFILE>
databricks bundle open auth_demo -t dev --profile <PROFILE>
```

| Variable | Meaning |
|---|---|
| `warehouse_id` | SQL warehouse the app's service principal may use |

**Permissions.** The bundle grants the service principal `CAN_USE` on the warehouse and requests the `sql` user API scope (on-behalf-of-user). For the service-principal path, also grant the principal `USE CATALOG`, `USE SCHEMA` and `SELECT` on the tables you want to query. The on-behalf-of-user path needs nothing extra: it uses the signed-in user's own grants.

## Running Locally

1. Clone this repo to your local machine and switch into the `auth-demo` folder:
   ```bash
   git clone https://github.com/databricks-solutions/databricks-apps-examples.git
   cd databricks-apps-examples/auth-demo
   ```
1. Install [uv](https://docs.astral.sh/uv/) if you haven't already.
1. Install the [Databricks CLI](https://docs.databricks.com/en/dev-tools/cli/index.html) and authenticate with your Databricks workspace using [OAuth U2M](https://docs.databricks.com/en/dev-tools/auth/oauth-u2m.html), for example:
   ```bash
   databricks auth login --host https://my-workspace.cloud.databricks.com/
   ```
1. Run the app (uv will automatically create a virtual environment and install dependencies):
   ```bash
   uv run python app.py
   ```

> [!NOTE]
>
> - When running locally, on-behalf-of-user authorization will not work due to the missing `X-Forwarded-Access-Token` header.
> - The service principal authorization section of the app will instead use your user credentials as configured with the CLI.

---

&copy; 2025 Databricks, Inc. All rights reserved. The source in this repository is provided subject to the Databricks License [https://databricks.com/db-license-source]. All included or referenced third party libraries are subject to the licenses set forth below.

| library                  | description                                        | license      | source                                              |
| ------------------------ | -------------------------------------------------- | ------------ | --------------------------------------------------- |
| dash                     | Framework for building analytical web applications | MIT          | https://github.com/plotly/dash                      |
| dash-iconify             | Icon components for Dash apps                      | MIT          | https://github.com/snehilvj/dash-iconify            |
| dash_mantine_components  | Mantine components for Dash                        | MIT          | https://github.com/snehilvj/dash-mantine-components |
| gunicorn                 | WSGI HTTP server                                   | MIT          | https://github.com/benoitc/gunicorn                 |
| databricks-sdk           | Databricks SDK for Python                          | Apache 2.0   | https://github.com/databricks/databricks-sdk-py     |
| databricks-sql-connector | Databricks SQL Connector for Python                | Apache 2.0   | https://github.com/databricks/databricks-sql-python |
| Flask                    | Lightweight WSGI web application framework         | BSD 3-Clause | https://github.com/pallets/flask                    |
| pandas                   | Data analysis and manipulation library             | BSD 3-Clause | https://github.com/pandas-dev/pandas                |
| pyarrow                  | Python library for Apache Arrow                    | Apache 2.0   | https://github.com/apache/arrow/tree/main/python    |

Databricks support doesn't cover this content. For questions or bugs, please open a github issue and the team will help on a best effort basis.

---

## Questions and issues

Please file an issue on this repository when and if you run into errors with the deployed applications. Thanks!
