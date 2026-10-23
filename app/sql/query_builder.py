from __future__ import annotations

import re
from typing import Any


def build_query(interpreted: dict[str, Any]) -> tuple[str, list[Any]]:
    intent = interpreted.get("intent", "list")
    aggregate = interpreted.get("aggregate")
    filters = interpreted.get("filters", [])
    department = interpreted.get("department")
    course = interpreted.get("course")
    year = interpreted.get("year")
    name = interpreted.get("name")
    limit = interpreted.get("limit") or 10

    select_parts = ["s.student_id", "s.name", "d.department_name", "s.year"]
    base = "FROM students s"
    joins = "LEFT JOIN departments d ON d.department_id = s.department_id"
    where_clauses: list[str] = []
    params: list[Any] = []

    if department:
        where_clauses.append("LOWER(d.department_name) = LOWER(?)")
        params.append(department)
    if year is not None:
        where_clauses.append("s.year = ?")
        params.append(year)
    if name:
        where_clauses.append("LOWER(s.name) LIKE LOWER(?)")
        params.append(f"%{name}%")

    for condition in filters:
        field = condition.get("field")
        operator = condition.get("operator")
        value = condition.get("value")
        if field == "marks":
            field_sql = "m.marks"
        elif field == "department_name":
            field_sql = "d.department_name"
        elif field == "course_name":
            field_sql = "c.course_name"
        elif field == "year":
            field_sql = "s.year"
        else:
            field_sql = "s.name"
        if operator == "gt":
            where_clauses.append(f"{field_sql} > ?")
        elif operator == "lt":
            where_clauses.append(f"{field_sql} < ?")
        elif operator == "gte":
            where_clauses.append(f"{field_sql} >= ?")
        elif operator == "lte":
            where_clauses.append(f"{field_sql} <= ?")
        elif operator == "eq":
            if field in {"department_name", "course_name"}:
                where_clauses.append(f"LOWER({field_sql}) = LOWER(?)")
            else:
                where_clauses.append(f"{field_sql} = ?")
        elif operator == "ne":
            if field in {"department_name", "course_name"}:
                where_clauses.append(f"LOWER({field_sql}) != LOWER(?)")
            else:
                where_clauses.append(f"{field_sql} != ?")
        else:
            continue
        params.append(value)

    if course or any(item.get("field") == "marks" for item in filters):
        base = "FROM students s"
        joins = (
            "LEFT JOIN departments d ON d.department_id = s.department_id "
            "LEFT JOIN enrollments e ON e.student_id = s.student_id "
            "LEFT JOIN courses c ON c.course_id = e.course_id "
            "LEFT JOIN marks m ON m.student_id = s.student_id AND m.course_id = c.course_id"
        )
        select_parts = ["s.student_id", "s.name", "d.department_name", "c.course_name", "m.marks", "m.grade"]
    elif department:
        select_parts = ["s.student_id", "s.name", "d.department_name", "s.year"]

    if aggregate == "count":
        select_parts = ["COUNT(*) AS total_count"]
        base = "FROM students s"
        joins = "LEFT JOIN departments d ON d.department_id = s.department_id"
    elif aggregate == "avg":
        select_parts = ["AVG(m.marks) AS average_marks"]
        base = "FROM marks m"
        joins = (
            "LEFT JOIN students s ON s.student_id = m.student_id "
            "LEFT JOIN courses c ON c.course_id = m.course_id"
        )
    elif aggregate == "sum":
        select_parts = ["SUM(m.marks) AS total_marks"]
        base = "FROM marks m"
        joins = (
            "LEFT JOIN students s ON s.student_id = m.student_id "
            "LEFT JOIN courses c ON c.course_id = m.course_id"
        )
    elif aggregate == "max":
        select_parts = ["MAX(m.marks) AS highest_marks"]
        base = "FROM marks m"
        joins = (
            "LEFT JOIN students s ON s.student_id = m.student_id "
            "LEFT JOIN courses c ON c.course_id = m.course_id"
        )
    elif aggregate == "min":
        select_parts = ["MIN(m.marks) AS lowest_marks"]
        base = "FROM marks m"
        joins = (
            "LEFT JOIN students s ON s.student_id = m.student_id "
            "LEFT JOIN courses c ON c.course_id = m.course_id"
        )

    if interpreted.get("group_by") == "department":
        select_parts = ["d.department_name AS label", "COUNT(*) AS value"]
        base = "FROM students s"
        joins = "LEFT JOIN departments d ON d.department_id = s.department_id"
        group_sql = "GROUP BY d.department_name"
    elif interpreted.get("group_by") == "course":
        select_parts = ["c.course_name AS label", "AVG(m.marks) AS value"]
        base = "FROM marks m"
        joins = "LEFT JOIN courses c ON c.course_id = m.course_id"
        group_sql = "GROUP BY c.course_name"
    elif interpreted.get("group_by") == "year":
        select_parts = ["s.year AS label", "COUNT(*) AS value"]
        base = "FROM students s"
        joins = ""
        group_sql = "GROUP BY s.year"
    else:
        group_sql = ""

    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
    else:
        where_sql = ""

    order_sql = ""
    if intent in {"max", "top"}:
        if "m.marks" in select_parts or aggregate in {"max", "avg"}:
            order_sql = "ORDER BY m.marks DESC"
        else:
            order_sql = "ORDER BY s.student_id ASC"
    elif intent == "list":
        order_sql = "ORDER BY s.student_id ASC"

    if limit and intent in {"max", "top", "list"}:
        order_sql = f"{order_sql} LIMIT ?" if order_sql else "LIMIT ?"
        params.append(limit)

    query = (
        f"SELECT {', '.join(select_parts)} {base} {joins} {where_sql} "
        f"{group_sql} {order_sql}"
    ).replace("  ", " ").strip()
    query = re.sub(r"\s+", " ", query)
    return query, params
