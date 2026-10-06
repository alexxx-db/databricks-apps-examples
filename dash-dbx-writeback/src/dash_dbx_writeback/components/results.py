from typing import List, Dict, Any

import dash_ag_grid as dag
import dash_mantine_components as dmc
from dash import html, dcc


# Placeholder column definitions. These will be dynamically generated once data is loaded.
DEFAULT_COLUMN_DEFS: List[Dict[str, Any]] = [
    {"field": "SELL_ID", "headerName": "Sell ID", "filter": "agTextColumnFilter"},
    {"field": "PREDICTED_UNITS", "headerName": "Predicted Units", "filter": "agNumberColumnFilter"},
    {"field": "PREDICTED_REVENUE", "headerName": "Predicted Revenue", "filter": "agNumberColumnFilter"},
]


def render_results_grid() -> html.Div:
    """Renders the results grid layout."""

    # Components
    forecast_select = dmc.Select(
        id="results-forecast-select",
        label="Select Forecast Run",
        data=[],  # filled on page load by populate_forecast_dropdown (callbacks/results_callbacks.py)
        searchable=True,
        clearable=True,
        persistence=True,
        persistence_type="local",
        w=400,
    )

    download_button = dmc.Button(
        "Download CSV", id="results-csv-button", variant="gradient", n_clicks=0
    )

    grid = dag.AgGrid(
        id="results-grid",
        rowData=[],
        columnDefs=DEFAULT_COLUMN_DEFS,
        columnSize="autoSize",
        className="ag-theme-quartz",
        dashGridOptions={
            "rowSelection": "multiple",
            "suppressRowClickSelection": True,
        },
        defaultColDef={
            "editable": False,
            "sortable": True,
            "filter": True,
            "floatingFilter": True,
            "resizable": True,
            "minWidth": 150,
        },
        csvExportParams={
            "fileName": "forecast_results.csv",
            "skipColumnGroupHeaders": True,
        },
        rowClassRules={"ag-row-hover": "true"},
        style={"--ag-row-hover-color": "#f5f5f5"},
    )

    store = dcc.Store(id="results-data-store", storage_type="local")

    description_box = dmc.Alert(
        "Select a forecast run to view results.",
        title="Results Viewer",
        color="blue",
        radius="md",
        id="results-description-box",
    )

    return html.Div(
        [
            html.Div(id="results-page-load", style={"display": "none"}),  # init trigger
            store,
            dmc.Space(h=10),
            forecast_select,
            dmc.Space(h=10),
            description_box,
            grid,
            dmc.Space(h=10),
            dmc.Group([download_button]),
        ]
    ) 