from __future__ import annotations

import re
import sqlite3
import time
from typing import Any

from app.config import DB_PATH, MAX_QUERY_ROWS
from app.database.connection import get_connection
from app.nlp.entity_extractor import COURSE_ALIASES, DEPARTMENT_ALIASES, extract_entities
from app.nlp.intent_detector import detect_intent
from app.nlp.preprocessing import normalize_question
from app.nlp.schema_mapper import map_query
from app.sql.query_builder import build_query
from app.sql.validator import validate_sql

SCHEMA_REFERENCES = {
    "student",
    "students",
    "learner",
    "learners",
    "department",
    "departments",
    "course",
    "courses",
    "enrollment",
    "enrollments",
    "enrolled",
    "semester",
    "semesters",
    "mark",
    "marks",
    "score",
    "scores",
    "grade",
    "grades",
    "year",
    "years",
    "age",
    "ages",
    "gender",
    "male",
    "female",
    "email",
    "emails",
    "credit",
    "credits",
}

QUERY_ACTIONS = {
    "show",
    "list",
    "display",
    "give",
    "find",
    "fetch",
    "get",
    "provide",
    "what",
    "which",
    "who",
    "count",
    "average",
    "avg",
    "mean",
    "sum",
    "minimum",
    "lowest",
    "min",
    "maximum",
    "highest",
    "max",
    "top",
    "unique",
    "distinct",
    "how",
    "many",
    "number",
    "total",
    "each",
    "by",
    "per",
}


def parse_question(question: str) -> dict[str, Any]:
    normalized = normalize_question(question)
    intent = detect_intent(normalized)
    entities = extract_entities(normalized)
    mapped = map_query(normalized, intent, entities)
    filters = []
    if entities.get("comparisons"):
        filters.extend(entities["comparisons"])
    if entities.get("year") is not None:
        filters.append({"field": "year", "operator": "eq", "value": entities["year"]})
    mapped["filters"] = filters
    mapped["department"] = entities.get("department")
    mapped["course"] = entities.get("course")
    mapped["year"] = entities.get("year")
    mapped["name"] = entities.get("name")
    mapped["limit"] = entities.get("limit") or 10
    if intent.get("group_by"):
        mapped["group_by"] = intent.get("group_by")
    tokens = set(re.findall(r"[a-z0-9]+", normalized))
    has_schema_reference = bool(tokens & SCHEMA_REFERENCES) or any(
        re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", normalized)
        for alias in (*DEPARTMENT_ALIASES, *COURSE_ALIASES)
        if len(alias) > 2
    )
    has_query_action = bool(tokens & QUERY_ACTIONS) or intent.get("group_by") is not None
    generic_result_limit = bool(
        re.search(r"\b(?:show|list|display|get|give|fetch)\s+(?:me\s+)?fewer than \d+ results?\b", normalized)
    )
    implicit_list = bool(
        re.match(r"^(?:students?|learners?|departments?|courses?|enrollments?|marks?|grades?)\b", normalized)
    )
    supported = (has_schema_reference and (has_query_action or implicit_list)) or generic_result_limit
    unsupported_keywords = [
        "join",
        "update",
        "delete",
        "create table",
        "drop table",
        "insert into",
        "password",
        "file",
    ]
    destructive_action = re.search(r"\b(?:drop|delete|update|insert|create|alter)\b", normalized)
    if any(token in normalized for token in unsupported_keywords) or destructive_action:
        supported = False
    return {
        "question": question,
        "normalized_question": normalized,
        "intent": intent,
        "entities": entities,
        "mapped": mapped,
        "supported": supported,
    }


def generate_sql(question: str) -> tuple[str, list[Any], dict[str, Any]]:
    parsed = parse_question(question)
    if not parsed["supported"]:
        return "", [], parsed
    sql, params = build_query(parsed["mapped"])
    return sql, params, parsed


def safe_execute(statement: str, params: list[Any] | tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
    validate_sql(statement)
    db = get_connection(DB_PATH)
    try:
        db.execute("PRAGMA query_only = ON")
        cursor = db.execute(statement, params or [])
        rows = [dict(row) for row in cursor.fetchall()]
        return rows[:MAX_QUERY_ROWS]
    except sqlite3.DatabaseError as exc:
        raise ValueError(f"Database error: {exc}") from exc
    finally:
        db.close()


def execute_question(question: str) -> dict[str, Any]:
    start = time.perf_counter()
    sql, params, parsed = generate_sql(question)
    if not parsed["supported"]:
        raise ValueError(
            "This question is unsupported. Try a supported query such as "
            "'show students in computer science' or 'how many students are in "
            "each department?'"
        )
    rows = safe_execute(sql, params)
    elapsed = round((time.perf_counter() - start) * 1000, 2)
    columns = list(rows[0].keys()) if rows else []
    return {
        "question": question,
        "intent": parsed["intent"]["intent"],
        "table": parsed["mapped"].get("table"),
        "filters": parsed["mapped"].get("filters", []),
        "sql": sql,
        "params": params,
        "results": rows,
        "columns": columns,
        "result_count": len(rows),
        "execution_time_ms": elapsed,
        "supported": True,
    }
