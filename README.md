# Databricks Apps Examples

Deployable reference apps for [Databricks Apps](https://docs.databricks.com/dev-tools/databricks-apps/). Each folder is a self-contained app with its own bundle (`databricks.yml`) and `dev` / `prod` targets.

| Example | Stack | Shows |
|---|---|---|
| [`appkit-analytics`](appkit-analytics/) | AppKit (TypeScript/React) | Typed SQL queries run on behalf of the user. **Recommended starting point for new apps** |
| [`fastapi-obo`](fastapi-obo/) | FastAPI | Python JSON backend querying Unity Catalog as the signed-in user |
| [`auth-demo`](auth-demo/) | Dash | Service principal vs on-behalf-of-user authorization, side by side |
| [`apps-write-back`](apps-write-back/) | Dash + AG Grid | Form, grid-edit and Excel writeback to Unity Catalog and Lakebase |
| [`dash-dbx-writeback`](dash-dbx-writeback/) | Dash + AG Grid | Excel-like writeback to Lakebase with OAuth token rotation and tests |
| [`vector-search`](vector-search/) | Gradio | PDF ingestion and search over a Vector Search index |
| [`apps-shell`](apps-shell/) | Dash | Multi-page app skeleton |

**Read [PATTERNS.md](PATTERNS.md) first.** It covers the auth, SQL-safety, resource, data-path and serving conventions every example follows.

### Deploy any example

```bash
cd <example>
databricks auth login --host https://<workspace> --profile <PROFILE>
databricks bundle deploy -t dev --var <name>=<value> --profile <PROFILE>   # variables are listed in each databricks.yml
```

Each example's README lists its variables, required permissions and local-run steps. [A video walkthrough of Databricks Apps](https://www.youtube.com/watch?v=Equ7PBeM-Mw) is also available.

## Important notices

This repository can _only_ accept contributions directly from Databricks field personnel. If you are a customer looking to contribute, please reach out to your Databricks representative, or to **cal.reynolds@databricks.com** if you don't have a representative. They will ensure that your submission meets our acceptance criteria, and will publish the contribution for you (_crediting you for your work of course_). 

#### Acceptance criteria:
1. All Databricks Apps submitted _must use either synthetic data or fully-open sourced datasets (with proper licensing notices included)_.
2. All Databricks Apps submitted _must include a notice in their README files with any and all third-party, open-sourced packages that they utilized._ Third-party packages should be credited in the following format:

---
&copy; 2024 Databricks, Inc. All rights reserved. The source in this notebook is provided subject to the Databricks License [https://databricks.com/db-license-source].  All included or referenced third party libraries are subject to the licenses set forth below.

| library | description | license | source |
|----------------------------------------|-------------------------|------------|-----------------------------------------------------|
| gradio | Python library for creating customizable UI components for ML models | Apache 2.0 | https://github.com/gradio-app/gradio |
| dash | Framework for building analytical web applications | MIT | https://github.com/plotly/dash |
| streamlit | Framework for creating data apps with minimal code | Apache 2.0 | https://github.com/streamlit/streamlit |
| plotly | Interactive graphing library for Python | MIT | https://github.com/plotly/plotly.py |
| flask | Lightweight WSGI web application framework | BSD 3-Clause | https://github.com/pallets/flask |
| fastapi | Modern, fast web framework for building APIs with Python | MIT | https://github.com/tiangolo/fastapi |
| langchain | Framework for developing applications powered by language models | MIT | https://github.com/langchain-ai/langchain |
| langgraph | Library for building stateful applications with LLMs | MIT | https://github.com/langchain-ai/langgraph |
| werkzeug | WSGI web application library (Flask dependency) | BSD 3-Clause | https://github.com/pallets/werkzeug |
| jinja2 | Template engine for Python (Flask dependency) | BSD 3-Clause | https://github.com/pallets/jinja |
| pydantic | Data validation using Python type annotations (FastAPI dependency) | MIT | https://github.com/pydantic/pydantic |
| starlette | Lightweight ASGI framework (FastAPI dependency) | BSD 3-Clause | https://github.com/encode/starlette |
| httpx | Modern HTTP client for Python (FastAPI dependency) | BSD 3-Clause | https://github.com/encode/httpx |
| uvicorn | Lightning-fast ASGI server (FastAPI dependency) | BSD 3-Clause | https://github.com/encode/uvicorn |

Databricks support doesn't cover this content. For questions or bugs, please open a github issue and the team will help on a best effort basis.

---

## Questions and issues

Please file an issue on this repository when and if you run into errors with the deployed applications. Thanks!
