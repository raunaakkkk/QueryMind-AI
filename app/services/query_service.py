from __future__ import annotations

import sqlite3
import time
from typing import Any

from app.config import DB_PATH, MAX_QUERY_ROWS
from app.database.connection import get_connection
from app.nlp.entity_extractor import extract_entities
from app.nlp.intent_detector import detect_intent
from app.nlp.preprocessing import normalize_question
from app.nlp.schema_mapper import map_query
from app.sql.query_builder import build_query
from app.sql.validator import validate_sql


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
    supported = True
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
    if any(token in normalized for token in unsupported_keywords):
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
