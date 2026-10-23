from __future__ import annotations

from typing import Any

TABLE_COLUMNS = {
    "departments": ["department_id", "department_name"],
    "students": ["student_id", "name", "age", "gender", "department_id", "year", "email"],
    "courses": ["course_id", "course_name", "credits", "department_id"],
    "enrollments": ["enrollment_id", "student_id", "course_id", "semester"],
    "marks": ["mark_id", "student_id", "course_id", "marks", "grade"],
}


FIELD_ALIASES = {
    "student": "students",
    "students": "students",
    "department": "departments",
    "departments": "departments",
    "course": "courses",
    "courses": "courses",
    "enrollment": "enrollments",
    "enrollments": "enrollments",
    "mark": "marks",
    "year": "students.year",
    "name": "students.name",
    "department_name": "departments.department_name",
    "course_name": "courses.course_name",
    "marks": "marks.marks",
}


def map_query(question: str, intent: dict[str, Any], entities: dict[str, Any]) -> dict[str, Any]:
    selected_table = "students"
    if "department" in question or "departments" in question:
        selected_table = "departments"
    elif "course" in question:
        selected_table = "courses"
    elif "marks" in question or "score" in question or "grade" in question:
        selected_table = "marks"
    elif "enroll" in question or "semester" in question:
        selected_table = "enrollments"

    return {
        "table": selected_table,
        "columns": TABLE_COLUMNS.get(selected_table, TABLE_COLUMNS["students"]),
        "entity_department": entities.get("department"),
        "entity_course": entities.get("course"),
        "entity_year": entities.get("year"),
        "limit": entities.get("limit"),
        "comparisons": entities.get("comparisons", []),
        "name": entities.get("name"),
        "intent": intent.get("intent"),
        "aggregate": intent.get("aggregate"),
        "group_by": intent.get("group_by"),
    }
