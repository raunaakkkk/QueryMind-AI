from __future__ import annotations

from app.sql.query_builder import build_query
from app.sql.validator import validate_sql


def test_build_query_for_count():
    sql, params = build_query({
        "intent": "count",
        "aggregate": "count",
        "filters": [{"field": "department_name", "operator": "eq", "value": "Computer Science"}],
        "department": "computer science",
        "limit": 10,
        "group_by": None,
    })
    assert "SELECT" in sql.upper()
    assert params


def test_sql_validation_rejects_destructive_query():
    try:
        validate_sql("DELETE FROM students WHERE student_id = 1;")
        assert False
    except ValueError:
        assert True
