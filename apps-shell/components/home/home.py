import dash
from dash import dcc, html
import dash_mantine_components as dmc

dash.register_page(__name__, path="/", name="Getting started", icon="lucide:home")

layout = html.Div(
    [
        html.Div(
            [
                dmc.Title("Welcome to Databricks Apps Examples", order=1),
                dcc.Markdown(
                    """
            This application demonstrates how to integrate Databricks 
            functionality into your Dash applications.
            """
                ),
                dmc.Title("Getting Started", order=2),
                dcc.Markdown(
                    """
            To enable all features, configure your Databricks 
            SQL warehouse as an app resource (see `databricks.yml`).
            """
                ),
                dmc.CodeHighlight(
                    language="yaml",
                    code="""env:
  - name: DATABRICKS_SQL_WAREHOUSE_ID
    valueFrom: sql-warehouse
""",
                ),
            ]
        )
    ],
    style={"padding": "20px"},
)
