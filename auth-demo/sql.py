import logging

import pandas as pd

from auth import w

logger = logging.getLogger(__name__)


def fetch_warehouses():
    warehouse_options = []
    warehouse_options_initial = None
    if w:
        try:
            warehouses = w.warehouses.list()
            warehouse_list = sorted(
                [wh for wh in warehouses if wh.odbc_params and wh.odbc_params.path],
                key=lambda x: x.name,
            )
            if warehouse_list:
                warehouse_options = [
                    {"label": wh.name, "value": wh.odbc_params.path}
                    for wh in warehouse_list
                ]
                warehouse_options_initial = warehouse_options[0]["value"]
            else:
                warehouse_options = [
                    {"label": "No warehouses found", "value": "", "disabled": True}
                ]

        except Exception as e:
            logger.exception(f"Error fetching warehouses: {e}")
            warehouse_options = [
                {"label": f"Error fetching: {e}", "value": "", "disabled": True}
            ]
    else:
        warehouse_options = [
            {"label": "SDK Not Configured", "value": "", "disabled": True}
        ]

    return warehouse_options, warehouse_options_initial


def run_query(table_name, conn):
    if not table_name or not conn:
        return pd.DataFrame()

    # IDENTIFIER() binds the user-supplied name as a parameter, never as SQL text
    query = "SELECT * FROM IDENTIFIER(:table_name) LIMIT 1000"
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, {"table_name": table_name})
            df = cursor.fetchall_arrow().to_pandas()
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(
                    df[col]
                ) or pd.api.types.is_timedelta64_dtype(df[col]):
                    try:
                        df[col] = pd.to_datetime(df[col]).dt.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    except Exception:
                        df[col] = df[col].astype(str)
                elif isinstance(df[col].dtype, (pd.ArrowDtype)):
                    df[col] = df[col].astype(str)
                elif not pd.api.types.is_numeric_dtype(
                    df[col]
                ) and not pd.api.types.is_string_dtype(df[col]):
                    df[col] = df[col].astype(str)
            return df
    except Exception as e:
        logger.exception(f"Error running query for table {table_name!r}")
        raise
