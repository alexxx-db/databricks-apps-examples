import datetime
from typing import List, Dict, Any

import pandas as pd
import dash_mantine_components as dmc
from dash import Input, Output, callback

from ..database_operations import query_df
from ..config import db_config


def log(message: str) -> None:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {message}")


@callback(
    Output("results-forecast-select", "data"),
    Input("results-page-load", "id"),  # Trigger on page load
    prevent_initial_call=False,
)
def populate_forecast_dropdown(_: str):
    log("CALLBACK: populate_forecast_dropdown")
    table_name = db_config.get_full_table_name("forecast_submissions")
    # Columns are created quoted-uppercase by bulk_insert; latest 50 runs, newest first.
    # query_df returns an empty frame on error (e.g. no submissions table yet).
    df = query_df(
        f'SELECT "FORECAST_ID" FROM {table_name} '
        'GROUP BY "FORECAST_ID" ORDER BY MAX("SUBMISSION_TIMESTAMP") DESC LIMIT 50'
    )
    return [{"value": fid, "label": fid} for fid in df.get("FORECAST_ID", [])]


@callback(
    Output("results-data-store", "data"),
    Output("results-description-box", "children"),
    Input("results-forecast-select", "value"),
    prevent_initial_call=True,
)
def load_forecast_results(forecast_id: str):
    log(f"CALLBACK: load_forecast_results - forecast_id: {forecast_id}")
    if not forecast_id:
        return [], "Select a forecast run to view results."
    try:
        table_name = db_config.get_full_table_name("forecast_results")
        
        # Use parameterized query to prevent SQL injection
        # Note: PostgreSQL column names are case-sensitive, columns are uppercase
        query = f'SELECT * FROM {table_name} WHERE "FORECAST_ID" = %s'
        log(f"→ Executing query: {query} with params: ({forecast_id},)")
        
        df = query_df(query, (forecast_id,))
        data = df.to_dict("records")
        msg = dmc.Text(f"Loaded {len(data)} rows for forecast {forecast_id}")
        return data, msg
    except Exception as e:
        log(f"Error loading forecast results: {e}")
        return [], dmc.Text("Error loading results.")


@callback(
    Output("results-grid", "rowData"),
    Input("results-data-store", "data"),
)
def update_grid(row_data: List[Dict[str, Any]]):
    log(f"CALLBACK: update_grid - rows: {len(row_data) if row_data else 0}")
    return row_data or []


@callback(
    Output("results-grid", "exportDataAsCsv"),
    Input("results-csv-button", "n_clicks"),
)
def export_results_csv(n_clicks):
    log(f"CALLBACK: export_results_csv - n_clicks: {n_clicks}")
    if n_clicks:
        return True
    return False 