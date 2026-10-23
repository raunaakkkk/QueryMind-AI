from __future__ import annotations

import pytest

from app.services.query_service import safe_execute
from app.sql.validator import ValidationError, validate_sql


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE students;",
        "DELETE FROM students WHERE student_id = 1;",
        "UPDATE students SET age = 99 WHERE student_id = 1;",
        "INSERT INTO students (name) VALUES ('Mallory');",
        "ATTACH DATABASE ':memory:' AS x;",
    ],
)
def test_reject_destructive_sql(sql: str):
    with pytest.raises((ValidationError, ValueError)):
        safe_execute(sql)


def test_reject_multiple_statements():
    with pytest.raises((ValidationError, ValueError)):
        validate_sql("SELECT * FROM students; DROP TABLE students;")
