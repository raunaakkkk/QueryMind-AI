from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.query_service import generate_sql

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


@pytest.mark.parametrize(
    "question",
    [
        "Show me the weather on Mars",
        "What is the capital of France?",
        "Tell me a joke",
        "Tell me a joke about students",
        "Show all electives in the database.",
    ],
)
def test_unrelated_queries_are_rejected(question: str):
    response = client.post("/api/query", json={"question": question})

    assert response.status_code == 400
    assert response.json()["supported"] is False
    assert "unsupported" in response.json()["error"].lower()


def test_unsupported_query_does_not_generate_default_sql():
    sql, params, parsed = generate_sql("Show me the weather on Mars")

    assert parsed["supported"] is False
    assert sql == ""
    assert params == []


def test_supported_student_count_query_still_works():
    response = client.post("/api/query", json={"question": "How many students are there in total?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["supported"] is True
    assert payload["columns"] == ["total_count"]
    assert payload["results"][0]["total_count"] > 0


def test_supported_implicit_student_list_query_still_works():
    response = client.post("/api/query", json={"question": "Students in computer science"})

    assert response.status_code == 200
    assert response.json()["supported"] is True


def test_schema_endpoint():
    response = client.get("/api/schema")
    assert response.status_code == 200
    assert "tables" in response.json()
