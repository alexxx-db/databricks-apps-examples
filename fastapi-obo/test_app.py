import importlib

from fastapi.testclient import TestClient


def test_health_and_no_service_principal_fallback(monkeypatch):
    monkeypatch.setenv("DATABRICKS_HOST", "https://example.cloud.databricks.com")
    monkeypatch.setenv("DATABRICKS_TOKEN", "unused")
    monkeypatch.setenv("DATABRICKS_APP_NAME", "fastapi-obo")
    monkeypatch.setenv("DATABRICKS_WAREHOUSE_ID", "unused")
    import app

    client = TestClient(importlib.reload(app).app)
    assert client.get("/api/health").json() == {"status": "ok"}
    # Deployed without the user's token must be refused, not served as the app's service principal
    assert client.get("/api/tables/samples.nyctaxi.trips").status_code == 401
