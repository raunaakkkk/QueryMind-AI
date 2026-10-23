from __future__ import annotations

from typing import Any

import pandas as pd

from app.config import DB_PATH
from app.database.connection import get_connection


def fetch_all(sql: str, params: list[Any] | tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    conn = get_connection(DB_PATH)
    try:
        conn.execute("PRAGMA query_only = ON")
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def summary_stats() -> dict[str, Any]:
    conn = get_connection(DB_PATH)
    try:
        stats = {
            "total_students": conn.execute("SELECT COUNT(*) AS total FROM students").fetchone()[0],
            "total_departments": conn.execute("SELECT COUNT(*) AS total FROM departments").fetchone()[0],
            "total_courses": conn.execute("SELECT COUNT(*) AS total FROM courses").fetchone()[0],
            "total_enrollments": conn.execute("SELECT COUNT(*) AS total FROM enrollments").fetchone()[0],
            "average_marks": conn.execute("SELECT AVG(marks) AS avg FROM marks").fetchone()[0],
            "highest_marks": conn.execute("SELECT MAX(marks) AS highest FROM marks").fetchone()[0],
        }
    finally:
        conn.close()
    return stats


def department_distribution() -> list[dict[str, Any]]:
    sql = (
        "SELECT d.department_name AS department, COUNT(s.student_id) AS student_count "
        "FROM departments d LEFT JOIN students s ON s.department_id = d.department_id "
        "GROUP BY d.department_name ORDER BY student_count DESC"
    )
    return fetch_all(sql)


def average_marks_by_course_or_department() -> list[dict[str, Any]]:
    sql = (
        "SELECT c.course_name AS label, AVG(m.marks) AS average_marks "
        "FROM marks m LEFT JOIN courses c ON c.course_id = m.course_id "
        "GROUP BY c.course_name ORDER BY average_marks DESC"
    )
    rows = fetch_all(sql)
    df = pd.DataFrame(rows)
    return df.to_dict(orient="records")
