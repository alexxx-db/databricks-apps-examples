import logging

import base64
import io
import datetime
import uuid
import time
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import dash_mantine_components as dmc
from dash import Input, Output, State, callback, clientside_callback, callback_context
from flask import request

from ..database_operations import bulk_insert, check_table_exists, execute_sql, query_df
from ..config import db_config
from ..sample_data import INITIAL_DATA
from ..components.input import (
    CSV_TO_GRID_COL_MAP,
    get_null_description,
)

logger = logging.getLogger(__name__)


# 1. Initialize store on load
@callback(
    Output("grid-data-store", "data"),
    Input("page-load", "id"),  # Triggers when component mounts
    State("grid-data-store", "data"),  # Check existing data
    prevent_initial_call=False,
)
def initialize_store(
    _: str, existing_data: Optional[List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    logger.info("CALLBACK: initialize_store")
    logger.info(f"Triggered by: {callback_context.triggered}")
    logger.info(f"Existing data: {len(existing_data) if existing_data else 0} records")

    # Always check the database on app start to ensure we have the latest data
    # You can change this behavior if you prefer to use local storage when available

    if existing_data:
        logger.info("Using existing local storage data")
        return existing_data

    try:
        table_name = db_config.get_full_table_name("layout_data")
        logger.info(f"Full table name: {table_name}")

        # Check if table exists
        table_exists = check_table_exists(table_name)
        logger.info(f"Table exists: {table_exists}")

        # If table doesn't exist or is empty, initialize it with sample data
        if not table_exists:
            logger.info(f"Table {table_name} doesn't exist, initializing with sample data")
            df = pd.DataFrame(INITIAL_DATA)
            result = bulk_insert(table_name, df, overwrite=False)
            logger.info(f"Initialize table result: {result}")

        # Return empty - the update_grid_by_category callback will load the data
        logger.info("Successfully initialized, data will be loaded by category callback")
        return []
    except Exception as e:
        logger.exception(f"Error initializing store: {type(e).__name__}: {e}")

        # If we have existing data in local storage and database fails, use it
        if existing_data:
            logger.info(
                f"Using existing local storage data with {len(existing_data)} records"
            )
            return existing_data

        logger.info("Falling back to initial data")
        return []


# 2. Export CSV
@callback(
    Output("ag-grid-table", "exportDataAsCsv"),
    Input("csv-button", "n_clicks"),
)
def export_data_as_csv(n_clicks: Optional[int]) -> bool:
    logger.info(f"CALLBACK: export_data_as_csv - n_clicks: {n_clicks}")
    if n_clicks:
        logger.info("Triggering CSV export")
        return True
    return False


# 3. Upload data to UC
@callback(
    Output("submit-button", "disabled"),
    Output("null-description-box", "children", allow_duplicate=True),
    Output("data-load-overlay", "visible", allow_duplicate=True),
    Input("submit-button", "n_clicks"),
    Input("grid-data-store", "data"),
    Input("upload-data", "contents"),
    prevent_initial_call=True,
)
def upload_data_to_uc(
    n_clicks: Optional[int],
    store_data: List[Dict[str, Any]],
    upload_clicks: Optional[str],
) -> Tuple[bool, List[dmc.Alert], bool]:
    logger.info(
        f"CALLBACK: upload_data_to_uc - n_clicks: {n_clicks}, has_upload: {upload_clicks is not None}"
    )
    logger.info(f"Store data: {len(store_data) if store_data else 0} records")

    # Get validation alerts from the existing function
    alerts = get_null_description(store_data).children
    logger.info(f"Current alerts: {alerts}")

    # Only disable if there are critical errors (red alerts)
    has_critical_errors = any(alert.color not in ["green"] for alert in alerts)
    logger.info(f"Has critical errors: {has_critical_errors}")

    if has_critical_errors:
        # Disable if critical errors
        logger.info("Disabling submit button due to errors")
        return True, alerts, False

    if n_clicks:
        logger.info("Processing forecast submission")
        forecast_id = (
            f"FCST-{datetime.datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        )
        logger.info(f"Generated forecast ID: {forecast_id}")

        df = pd.DataFrame(store_data)
        timestamp = datetime.datetime.now().isoformat()
        df["FORECAST_ID"] = forecast_id
        df["SUBMISSION_TIMESTAMP"] = timestamp
        df["ROW_ID"] = [f"{forecast_id}-{i+1:04d}" for i in range(len(df))]
        # Signed-in user from the Databricks Apps proxy, so submissions stay attributable
        df["SUBMITTED_BY"] = request.headers.get("X-Forwarded-Email", "local-dev")

        table_name = db_config.get_full_table_name("forecast_submissions")
        logger.info(f"Writing to table: {table_name}")
        # Tables created before SUBMITTED_BY existed get the column; no-op otherwise
        execute_sql(f'ALTER TABLE IF EXISTS {table_name} ADD COLUMN IF NOT EXISTS "SUBMITTED_BY" TEXT')

        try:
            bulk_insert(table_name, df)
        except Exception as e:
            error_alert = dmc.Alert(
                title="Forecast was not submitted",
                color="red",
                radius="md",
                children=[f"Saving to the database failed: {e}"],
                style={"marginBottom": "8px"},
            )
            return False, [error_alert], False

        time.sleep(1)

        success_alert = dmc.Alert(
            title="Congrats - Forecast is submitted",
            color="green",
            radius="md",
            children=[
                f"Your forecast is now being processed. You will receive an email when it is ready. Forecast ID: {forecast_id}"
            ],
            style={"marginBottom": "8px"},
        )
        logger.info("Forecast submitted successfully")
        return True, [success_alert], False
    return False, alerts, False


# 4. Update null description when store changes
@callback(
    Output("null-description-box", "children", allow_duplicate=True),
    Input("grid-data-store", "data"),
    prevent_initial_call=True,
)
def update_null_desc_box(store_data: List[Dict[str, Any]]) -> dmc.Stack:
    logger.info(
        f"CALLBACK: update_null_desc_box - {len(store_data) if store_data else 0} records"
    )
    return get_null_description(store_data)


# 5. Grid rowData from store
@callback(Output("ag-grid-table", "rowData"), Input("grid-data-store", "data"))
def update_grid_from_store(store_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    logger.info(
        f"CALLBACK: update_grid_from_store - {len(store_data) if store_data else 0} records"
    )
    return store_data if store_data is not None else []


# 6. Handle CSV upload
@callback(
    Output("grid-data-store", "data", allow_duplicate=True),
    Output("upload-data", "contents"),
    Input("upload-data", "contents"),
    State("grid-data-store", "data"),
    State("enable-overwrite", "checked"),
    prevent_initial_call=True,
)
def update_data(
    contents: Optional[str], current_data: List[Dict[str, Any]], overwrite: bool
) -> Tuple[List[Dict[str, Any]], None]:
    logger.info(
        f"CALLBACK: update_data - has_contents: {contents is not None}, overwrite: {overwrite}"
    )
    logger.info(f"Current data: {len(current_data) if current_data else 0} records")

    if contents is None:
        return current_data, None

    logger.info("Processing CSV upload")
    _, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    try:
        df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        logger.info(f"Read CSV with {len(df)} rows, {len(df.columns)} columns")

        df = df.rename(columns=CSV_TO_GRID_COL_MAP).dropna(how="all")
        new_data = df.to_dict("records")
        logger.info(f"Processed {len(new_data)} valid records")

        if overwrite:
            logger.info("Overwriting existing data")
            return new_data, None
        else:
            logger.info("Appending to existing data")
            return current_data + new_data, None
    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")
        return current_data, None


# 7. Filter by category
@callback(
    Output("grid-data-store", "data", allow_duplicate=True),
    Input("category-select", "value"),
    State("grid-data-store", "data"),
    prevent_initial_call="initial_duplicate",
)
def update_grid_by_category(
    selected_category: Optional[str], current_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    logger.info(f"CALLBACK: update_grid_by_category - category: {selected_category}")

    if not selected_category:
        logger.info("No category selected, returning current data")
        return current_data

    try:
        
        table_name = db_config.get_full_table_name("layout_data")
        logger.info(f"Table name: {table_name}")
        
        # Use parameterized query to prevent SQL injection
        # Note: PostgreSQL column names are case-sensitive, columns are uppercase
        if selected_category != "All":
            query = f'SELECT * FROM {table_name} WHERE "CATEGORY_NAME" = %s'
            params = (selected_category,)
            logger.info(f"Executing filtered query: {query}")
            logger.info(f"With params: {params}")
            filtered = query_df(query, params)
            logger.info(f"Query returned {len(filtered)} rows")
        else:
            query = f"SELECT * FROM {table_name}"
            logger.info(f"Executing query for all categories: {query}")
            filtered = query_df(query)
            logger.info(f"Query returned {len(filtered)} rows")

        if filtered.empty:
            logger.warning(f"No data found for category: {selected_category}")
            logger.warning(f"Returning current data with {len(current_data)} records")
            return current_data
        
        result = filtered.to_dict("records")
        logger.info(f"Successfully filtered to {len(result)} records for category: {selected_category}")
        return result
    except Exception as e:
        logger.exception(f"Error filtering data: {e}")
        logger.info(f"Returning current data with {len(current_data)} records")
        return current_data


# 8. Update store on cell edit
@callback(
    Output("grid-data-store", "data", allow_duplicate=True),
    Input("ag-grid-table", "cellValueChanged"),
    State("ag-grid-table", "rowData"),
    prevent_initial_call=True,
)
def update_store_on_cell_change(
    cell_changed: Dict[str, Any], row_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    if cell_changed:
        logger.info("CALLBACK: update_store_on_cell_change")
        logger.info(f"Cell changed: {cell_changed}")
        logger.info(f"Row data: {len(row_data) if row_data else 0} records")
    return row_data


# 9. Reset button
@callback(
    Output("grid-data-store", "data", allow_duplicate=True),
    Output("category-select", "value"),
    Input("reset-button", "n_clicks"),
    prevent_initial_call=True,
)
def reset_data(_: int) -> Tuple[None, None]:
    logger.info(f"CALLBACK: reset_data - n_clicks: {_}")
    logger.info("Clearing data and category selection")
    return None, []


# 10. Delete selected rows
@callback(
    Output("grid-data-store", "data", allow_duplicate=True),
    Input("delete-button", "n_clicks"),
    State("ag-grid-table", "selectedRows"),
    State("grid-data-store", "data"),
    prevent_initial_call=True,
)
def delete_selected_rows(
    _: int, selected_rows: List[Dict[str, Any]], current_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Delete selected rows from the grid data store.
    https://dash.plotly.com/dash-ag-grid/row-selection
    """
    logger.info(f"CALLBACK: delete_selected_rows - n_clicks: {_}")
    logger.info(f"Selected rows: {len(selected_rows) if selected_rows else 0} records")

    if not selected_rows or not current_data:
        return current_data

    # Filter out selected rows by comparing all key-value pairs
    filtered_data = [
        row
        for row in current_data
        if not any(
            all(row.get(k) == selected.get(k) for k in row.keys() & selected.keys())
            for selected in selected_rows
        )
    ]

    logger.info(f"Removed {len(current_data) - len(filtered_data)} rows")
    return filtered_data


clientside_callback(
    """
    function(n_clicks) {
        return (function(n_clicks) {
            if (n_clicks === null || n_clicks === undefined) {
                return false;
            }
            const timestamp = new Date().toISOString();
            console.log(`[${timestamp}] CLIENTSIDE CALLBACK: updateLoadingState - n_clicks:`, n_clicks);
            return true;
        })(n_clicks);
    }
    """,
    Output("data-load-overlay", "visible", allow_duplicate=True),
    Input("submit-button", "n_clicks"),
    prevent_initial_call=True,
)
