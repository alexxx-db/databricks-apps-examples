import dash
import dash_mantine_components as dmc
from dash import Dash, Input, Output, State, callback, dcc, html
import jwt
import json

from auth import (
    cfg,
    fetch_sp_details,
    get_connection_obo,
    get_connection_sp,
    get_user_token,
)
from sql import (
    fetch_warehouses,
    run_query,
)
from utils import create_data_table, get_icon

app = Dash(__name__, external_stylesheets=[dmc.styles.ALL])
server = app.server  # WSGI entrypoint for gunicorn (see app.yml)
app.title = "Databricks Auth Demo"

app.layout = dmc.MantineProvider(
    theme={
        "fontFamily": "DM Sans, sans-serif",
        "primaryColor": "lava",
        "colors": {
            "lava": [
                "#ffe9e6",
                "#ffd2cd",
                "#ffa49a",
                "#ff7264",
                "#ff4936",
                "#ff2e18",
                "#ff1e07",
                "#e40f00",
                "#cc0500",
                "#b20000",
            ]
        },
    },
    children=dmc.AppShell(
        header={"height": 60},
        padding="md",
        children=[
            dmc.AppShellHeader(
                style={"backgroundColor": "#F9F7F4"},
                children=[
                    dmc.Container(
                        children=[
                            dmc.Group(
                                justify="space-between",
                                align="center",
                                h="100%",
                                children=[
                                    dmc.Group(
                                        gap="sm",
                                        align="center",
                                        children=[
                                            html.Img(
                                                src=app.get_asset_url("logo.svg"),
                                                height=28,
                                            ),
                                            dmc.Title(
                                                "Databricks Apps Authorization Demo",
                                                order=2,
                                            ),
                                        ],
                                    ),
                                    dmc.Badge(
                                        id="header-username",
                                        variant="outline",
                                        leftSection=get_icon(
                                            "material-symbols:person-outline"
                                        ),
                                    ),
                                ],
                            )
                        ],
                        fluid=False,
                        h="100%",
                        px=0,
                    )
                ],
            ),
            dmc.AppShellMain(
                style={"backgroundColor": "#F9F7F4"},
                children=dmc.Container(
                    [
                        dmc.Grid(
                            [
                                dmc.GridCol(
                                    dmc.Select(
                                        id="sql-http-path",
                                        label="Select SQL Warehouse",
                                        description="Choose a running SQL warehouse.",
                                        data=[],
                                        value=None,
                                        required=True,
                                        style={"width": "100%"},
                                        searchable=True,
                                        nothingFoundMessage="No warehouses found",
                                        leftSection=get_icon(
                                            "material-symbols:database-outline"
                                        ),
                                    ),
                                    span=6,
                                ),
                                dmc.GridCol(
                                    dmc.TextInput(
                                        id="table-name-input",
                                        label="Unity Catalog Table Name",
                                        description="Format: catalog.schema.table",
                                        placeholder="main.sandbox.my_table",
                                        value="samples.nyctaxi.trips",
                                        required=True,
                                        style={"width": "100%"},
                                        leftSection=get_icon(
                                            "material-symbols:table-outline"
                                        ),
                                    ),
                                    span=6,
                                ),
                            ],
                            mb="lg",
                            gutter="xl",
                        ),
                        dmc.Stack(
                            [
                                dmc.Paper(
                                    [
                                        dmc.Title(
                                            "Service Principal (SP) Authorization",
                                            order=3,
                                            mb="md",
                                        ),
                                        dmc.Text(
                                            [
                                                "Uses this app's SP credentials via the ",
                                                dmc.InlineCodeHighlight(
                                                    code="DATABRICKS_CLIENT_ID"
                                                ),
                                                " and ",
                                                dmc.InlineCodeHighlight(
                                                    code="DATABRICKS_CLIENT_SECRET"
                                                ),
                                                " headers.",
                                            ],
                                            size="sm",
                                            mb="xs",
                                        ),
                                        dmc.Text(
                                            [
                                                "Service principal: ",
                                                html.B(id="sp-name-display"),
                                            ],
                                            size="sm",
                                            mb="md",
                                        ),
                                        dmc.Button(
                                            "Run Query (SP)",
                                            id="run-query-sp",
                                            variant="outline",
                                            leftSection=get_icon(
                                                "material-symbols:play-arrow-outline"
                                            ),
                                            mb="md",
                                            loading=False,
                                            loaderProps={
                                                "variant": "dots",
                                                "size": "sm",
                                            },
                                        ),
                                        dmc.Alert(
                                            id="alert-sp",
                                            children="Status will appear here.",
                                            title="Status",
                                            color="gray",
                                            withCloseButton=True,
                                            hide=True,
                                            radius="sm",
                                        ),
                                        html.Div(
                                            create_data_table("table-output-sp"),
                                            id="table-container-sp",
                                            style={"display": "none"},
                                        ),
                                        dmc.LoadingOverlay(
                                            id="loading-overlay-sp",
                                            visible=False,
                                            loaderProps={"variant": "dots"},
                                        ),
                                    ],
                                    shadow="sm",
                                    p="lg",
                                    radius="md",
                                    withBorder=True,
                                    style={"position": "relative"},
                                ),
                                dmc.Paper(
                                    [
                                        dmc.Title(
                                            "On-Behalf-Of User (OBO) Authorization",
                                            order=3,
                                            mb="md",
                                        ),
                                        dmc.Text(
                                            [
                                                "Uses the accessing user's credentials via the ",
                                                dmc.InlineCodeHighlight(
                                                    code="X-Forwarded-Access-Token"
                                                ),
                                                " header.",
                                            ],
                                            size="sm",
                                            mb="xs",
                                        ),
                                        dmc.Text(
                                            id="obo-username",
                                            size="sm",
                                            mb="md",
                                        ),
                                        dmc.Alert(
                                            id="obo-token-status",
                                            title="OBO Status",
                                            color="blue",
                                            mb="md",
                                            radius="sm",
                                        ),
                                        html.Div(
                                            id="accordion-container",
                                            children=dmc.Accordion(
                                                children=[
                                                    dmc.AccordionItem(
                                                        [
                                                            dmc.AccordionControl(
                                                                "View Access Token Details",
                                                                icon=get_icon("material-symbols:key-outline"),
                                                            ),
                                                            dmc.AccordionPanel(
                                                                [
                                                                    dmc.Stack(
                                                                        [
                                                                            dmc.Text("Raw JWT Token:", size="sm", fw=500, mb="xs"),
                                                                            dmc.ScrollArea(
                                                                                dmc.Code(
                                                                                    id="jwt-raw-token",
                                                                                    children="Token will appear here when available",
                                                                                    block=True,
                                                                                    style={"whiteSpace": "pre-wrap", "wordBreak": "break-all"},
                                                                                ),
                                                                                h=100,
                                                                                type="auto",
                                                                            ),
                                                                            dmc.Divider(my="md"),
                                                                            dmc.Text("Decoded JWT Payload:", size="sm", fw=500, mb="xs"),
                                                                            dmc.ScrollArea(
                                                                                dmc.Code(
                                                                                    id="jwt-decoded",
                                                                                    children="Decoded token will appear here",
                                                                                    block=True,
                                                                                    style={"whiteSpace": "pre"},
                                                                                ),
                                                                                h=200,
                                                                                type="auto",
                                                                            ),
                                                                            dmc.Divider(my="md"),
                                                                            dmc.Text("Parsed Scopes:", size="sm", fw=500, mb="xs"),
                                                                            html.Div(id="jwt-scopes-list"),
                                                                        ],
                                                                        gap="sm",
                                                                    )
                                                                ]
                                                            ),
                                                        ],
                                                        value="token-details",
                                                    )
                                                ],
                                                mb="md",
                                            ),
                                        ),
                                        dmc.Button(
                                            "Run Query (OBO)",
                                            id="run-query-obo",
                                            variant="outline",
                                            leftSection=get_icon(
                                                "material-symbols:play-arrow-outline"
                                            ),
                                            mb="md",
                                            loading=False,
                                            loaderProps={
                                                "variant": "dots",
                                                "size": "sm",
                                            },
                                        ),
                                        dmc.Alert(
                                            id="alert-obo",
                                            children="Status will appear here.",
                                            title="Status",
                                            color="gray",
                                            withCloseButton=True,
                                            hide=True,
                                            radius="sm",
                                            mt="md",
                                        ),
                                        html.Div(
                                            create_data_table("table-output-obo"),
                                            id="table-container-obo",
                                            style={"display": "none"},
                                        ),
                                        dmc.LoadingOverlay(
                                            id="loading-overlay-obo",
                                            visible=False,
                                            loaderProps={"variant": "dots"},
                                        ),
                                    ],
                                    shadow="sm",
                                    p="lg",
                                    radius="md",
                                    withBorder=True,
                                    style={"position": "relative"},
                                ),
                            ],
                            gap="xl",
                        ),
                        html.Div(id="initial-load-trigger", style={"display": "none"}),
                        dcc.Store(id="obo-token-store"),
                    ],
                    fluid=False,
                    p="0",
                ),
            ),
        ],
    ),
)


@callback(
    [
        Output("header-username", "children"),
        Output("obo-token-status", "children"),
        Output("obo-token-status", "color"),
        Output("obo-token-status", "title"),
        Output("run-query-obo", "disabled"),
        Output("obo-token-store", "data"),
        Output("obo-username", "children"),
        Output("sql-http-path", "data"),
        Output("sql-http-path", "value"),
        Output("sp-name-display", "children"),
        Output("jwt-raw-token", "children"),
        Output("jwt-decoded", "children"),
        Output("jwt-scopes-list", "children"),
        Output("accordion-container", "style"),
    ],
    Input("initial-load-trigger", "children"),
)
def update_header_and_warehouses(_):
    # Call fetch_warehouses() and get the results directly
    wh_options, wh_value = fetch_warehouses()

    # Call fetch_sp_details() and get the result directly
    sp_name = fetch_sp_details()

    header_username_display = ["User: ", dmc.Code("Unknown")]
    obo_status_msg = "Checking OBO status..."
    obo_color = "gray"
    obo_title = "Checking..."
    obo_disabled = True
    has_token = False
    obo_username = ["Current user: ", html.B("Unknown")]
    jwt_raw = "No token available"
    jwt_decoded = "No token to decode"
    jwt_scopes_list = dmc.Text("No scopes available", size="sm", c="dimmed")
    accordion_style = {"display": "none"}

    try:
        from flask import request

        headers = dict(request.headers)
        username = headers.get("X-Forwarded-Preferred-Username")
        obo_token = headers.get("X-Forwarded-Access-Token")

        header_username_display = username if username else "Not available"
        obo_username = [
            "Current user: ",
            html.B(username if username else "Not available"),
        ]

        has_token = bool(obo_token)
        has_sql_scope = False

        if has_token:
            # Show accordion when token is present
            accordion_style = {"display": "block"}
            
            # Store the raw JWT
            jwt_raw = obo_token
            
            # Try to decode the JWT
            try:
                # Decode without verification (since we don't have the public key)
                decoded_token = jwt.decode(obo_token, options={"verify_signature": False})
                jwt_decoded = json.dumps(decoded_token, indent=2)
                
                # Parse scopes
                scopes = decoded_token.get("scope", "").split()
                
                # Check if SQL scope is present
                # Looking for scopes that contain 'sql' (case-insensitive)
                has_sql_scope = any('sql' in scope.lower() for scope in scopes)
                
                if scopes:
                    jwt_scopes_list = dmc.List(
                        [dmc.ListItem(dmc.Code(scope)) for scope in scopes],
                        size="sm",
                        spacing="xs",
                    )
                else:
                    jwt_scopes_list = dmc.Text("No scopes found in token", size="sm", c="dimmed")
                    
            except Exception as e:
                jwt_decoded = f"Error decoding JWT: {str(e)}"
                jwt_scopes_list = dmc.Text("Error parsing scopes", size="sm", c="red")
            
            # Update OBO status based on SQL scope presence
            if has_sql_scope:
                obo_status_msg = [
                    dmc.InlineCodeHighlight(code="X-Forwarded-Access-Token"),
                    " found with SQL scope. OBO is properly configured.",
                ]
                obo_color = "green"
                obo_title = "OBO Configured"
                obo_disabled = False
            else:
                obo_status_msg = [
                    dmc.InlineCodeHighlight(code="X-Forwarded-Access-Token"),
                    " found but SQL scope is missing. Enable SQL auth scope for this app to use OBO.",
                ]
                obo_color = "orange"
                obo_title = "SQL Scope Missing"
                obo_disabled = True
                
        else:
            obo_status_msg = [
                dmc.InlineCodeHighlight(code="X-Forwarded-Access-Token"),
                " header NOT found. OBO requires this header. Enable OBO for this app to proceed.",
            ]
            obo_color = "orange"
            obo_title = "OBO Unavailable"
            obo_disabled = True

    except Exception:
        header_username_display = ["User: ", dmc.Code("Error")]
        obo_status_msg = "Error loading OBO status."
        obo_color = "red"
        obo_title = "Error Loading Headers"
        obo_disabled = True
        has_token = False

    # No longer need to read from potentially stale globals
    # wh_options = warehouse_options
    # wh_value = initial_warehouse_value

    # --- DEBUGGING ---
    # print("--- Callback update_header_and_warehouses ---")
    # print(f"Warehouses being sent to dropdown ({len(wh_options)}): {wh_options}")
    # print(f"Initial value being sent: {wh_value}")
    # print("---------------------------------------------")
    # --- END DEBUGGING ---

    return (
        header_username_display,
        obo_status_msg,
        obo_color,
        obo_title,
        obo_disabled,
        {"has_token": has_token},
        obo_username,
        # Return warehouse data and initial value
        wh_options,
        wh_value,
        # Return SP name
        sp_name,
        # Return JWT details
        jwt_raw,
        jwt_decoded,
        jwt_scopes_list,
        # Return accordion visibility
        accordion_style,
    )


@callback(
    [
        Output("table-output-sp", "data"),
        Output("table-output-sp", "columns"),
        Output("table-output-sp", "tooltip_data"),
        Output("alert-sp", "children"),
        Output("alert-sp", "color"),
        Output("alert-sp", "hide"),
        Output("alert-sp", "title"),
        Output("table-container-sp", "style"),
        Output("loading-overlay-sp", "visible"),
        Output("run-query-sp", "loading"),
    ],
    Input("run-query-sp", "n_clicks"),
    State("sql-http-path", "value"),
    State("table-name-input", "value"),
    running=[
        (Output("run-query-sp", "loading"), True, False),
    ],
    prevent_initial_call=True,
)
def run_sp_query_callback(n_clicks, http_path, table_name):
    container_style = {"display": "none"}
    loading_visible = False

    if not n_clicks or not http_path or not table_name:
        return dash.no_update + (False, False)

    if not cfg:
        return (
            [],
            [],
            [],
            [
                "Error: Databricks SDK not configured. Check environment variables like ",
                dmc.InlineCodeHighlight(code="DATABRICKS_HOST"),
                " etc.",
            ],
            "red",
            False,
            "Configuration Error",
            container_style,
            False,
            False,
        )

    loading_visible = True

    alert_hide = False

    try:
        conn = get_connection_sp(http_path)
        df = run_query(table_name, conn)
        conn.close()
        loading_visible = False

        if not df.empty:
            data = df.to_dict("records")
            columns = [{"name": i, "id": i} for i in df.columns]
            tooltips = [
                {
                    column: {"value": str(value), "type": "markdown"}
                    for column, value in row.items()
                }
                for row in data
            ]
            alert_msg = [
                "Success! Fetched ",
                html.B(f"{len(df)}"),
                " rows from ",
                dmc.Code(f"{table_name}"),
                " using the service principal's permissions.",
            ]
            alert_color = "green"
            alert_title = "Success"
            container_style = {"display": "block"}
            return (
                data,
                columns,
                tooltips,
                alert_msg,
                alert_color,
                alert_hide,
                alert_title,
                container_style,
                loading_visible,
                False,
            )
        else:
            alert_msg = [
                "Query ran successfully using Service Principal but returned no data from ",
                dmc.Code(f"'{table_name}'"),
                ".",
            ]
            alert_color = "yellow"
            alert_title = "No Data"
            return (
                [],
                [],
                [],
                alert_msg,
                alert_color,
                alert_hide,
                alert_title,
                container_style,
                loading_visible,
                False,
            )

    except Exception as e:
        loading_visible = False
        alert_msg = ["Error querying with Service Principal: ", dmc.Code(str(e))]
        alert_color = "red"
        alert_title = "Error"
        return (
            [],
            [],
            [],
            alert_msg,
            alert_color,
            alert_hide,
            alert_title,
            container_style,
            loading_visible,
            False,
        )


@callback(
    [
        Output("table-output-obo", "data"),
        Output("table-output-obo", "columns"),
        Output("table-output-obo", "tooltip_data"),
        Output("alert-obo", "children"),
        Output("alert-obo", "color"),
        Output("alert-obo", "hide"),
        Output("alert-obo", "title"),
        Output("table-container-obo", "style"),
        Output("loading-overlay-obo", "visible"),
        Output("run-query-obo", "loading"),
    ],
    Input("run-query-obo", "n_clicks"),
    State("sql-http-path", "value"),
    State("table-name-input", "value"),
    running=[
        (Output("run-query-obo", "loading"), True, False),
    ],
    prevent_initial_call=True,
)
def run_obo_query_callback(n_clicks, http_path, table_name):
    container_style = {"display": "none"}
    loading_visible = False

    if not n_clicks or not http_path or not table_name:
        return dash.no_update + (False, False)

    if not cfg:
        return (
            [],
            [],
            [],
            [
                "Error: Databricks SDK not configured. Check environment variables like ",
                dmc.InlineCodeHighlight(code="DATABRICKS_HOST"),
                " etc.",
            ],
            "red",
            False,
            "Configuration Error",
            container_style,
            False,
            False,
        )

    loading_visible = True

    alert_hide = False

    try:
        user_token = get_user_token()
        if not user_token:
            alert_msg = [
                "Error: ",
                dmc.InlineCodeHighlight(code="X-Forwarded-Access-Token"),
                " not found in this request's headers. Cannot run OBO query. Ensure OBO is enabled for the App.",
            ]
            alert_color = "red"
            alert_title = "OBO Token Missing"
            loading_visible = False
            return (
                [],
                [],
                [],
                alert_msg,
                alert_color,
                alert_hide,
                alert_title,
                container_style,
                loading_visible,
                False,
            )

        conn = get_connection_obo(http_path, user_token)
        df = run_query(table_name, conn)
        conn.close()
        loading_visible = False

        if not df.empty:
            data = df.to_dict("records")
            columns = [{"name": i, "id": i} for i in df.columns]
            tooltips = [
                {
                    column: {"value": str(value), "type": "markdown"}
                    for column, value in row.items()
                }
                for row in data
            ]
            alert_msg = [
                "Success! Fetched ",
                html.B(f"{len(df)}"),
                " rows from ",
                dmc.Code(f"{table_name}"),
                " using OBO authorization.",
            ]
            alert_color = "green"
            alert_title = "Success"
            container_style = {"display": "block"}
            return (
                data,
                columns,
                tooltips,
                alert_msg,
                alert_color,
                alert_hide,
                alert_title,
                container_style,
                loading_visible,
                False,
            )
        else:
            alert_msg = [
                "OBO Query ran successfully but returned no data from ",
                dmc.Code(f"'{table_name}'"),
                ".",
            ]
            alert_color = "yellow"
            alert_title = "No Data"
            return (
                [],
                [],
                [],
                alert_msg,
                alert_color,
                alert_hide,
                alert_title,
                container_style,
                loading_visible,
                False,
            )

    except Exception as e:
        loading_visible = False
        alert_msg_base = ["Error querying with OBO: ", dmc.Code(str(e))]
        alert_color = "red"
        alert_title = "Error"
        if (
            "PERMISSION_DENIED" in str(e).upper()
            or "DOES NOT HAVE PRIVILEGE" in str(e).upper()
        ):
            alert_msg = alert_msg_base + [
                " | Check if the user has SELECT permissions on the table and USE on the warehouse/catalog/schema."
            ]
        elif "OBO token not found" in str(e):
            alert_msg = [
                "Error: OBO token missing ( ",
                dmc.InlineCodeHighlight(code="X-Forwarded-Access-Token"),
                " ). Ensure OBO is enabled for this App and you are accessing it through Databricks.",
            ]
        else:
            alert_msg = alert_msg_base

        return (
            [],
            [],
            [],
            alert_msg,
            alert_color,
            alert_hide,
            alert_title,
            container_style,
            loading_visible,
            False,
        )


if __name__ == "__main__":
    app.run()
