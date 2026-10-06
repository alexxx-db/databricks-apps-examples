import uuid

import pandas as pd
import pytest

from dash_dbx_writeback.callbacks import results_callbacks
from dash_dbx_writeback.config import db_config
from dash_dbx_writeback.database_operations import bulk_insert, execute_sql

# Needs a live Postgres/Lakebase; CI runs `pytest -m "not integration"`
pytestmark = pytest.mark.integration


def test_dropdown_lists_submitted_forecasts_newest_first(monkeypatch):
    table = db_config.get_full_table_name(f"forecast_submissions_{uuid.uuid4().hex[:8]}")
    monkeypatch.setattr(db_config, "get_full_table_name", lambda _: table)
    try:
        for day, forecast_id in enumerate(["FCST-A", "FCST-B"], start=1):
            # Same columns the submit callback writes (quoted uppercase in Postgres)
            df = pd.DataFrame({"SELL_ID": [1, 2]})
            df["FORECAST_ID"] = forecast_id
            df["SUBMISSION_TIMESTAMP"] = f"2026-01-0{day}T00:00:00"
            bulk_insert(table, df)

        options = results_callbacks.populate_forecast_dropdown(None)

        assert [o["value"] for o in options] == ["FCST-B", "FCST-A"]
    finally:
        execute_sql(f"DROP TABLE IF EXISTS {table}")
