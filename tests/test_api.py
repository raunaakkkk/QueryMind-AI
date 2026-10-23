from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_query_endpoint():
    response = client.post("/api/query", json={"question": "Show me students in computer science"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["supported"] is True
    assert payload["result_count"] >= 0


def test_schema_endpoint():
    response = client.get("/api/schema")
    assert response.status_code == 200
    assert "tables" in response.json()
