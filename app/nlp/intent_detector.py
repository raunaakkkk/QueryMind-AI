from __future__ import annotations

import re

INTENT_KEYWORDS = {
    "count": ["count", "how many", "total number", "number of"],
    "sum": ["sum", "total of", "total marks", "total score"],
    "avg": ["average", "avg", "mean"],
    "min": ["minimum", "lowest", "min"],
    "max": ["maximum", "highest", "max", "top"],
    "list": ["show", "list", "display", "give", "find", "fetch"],
    "distinct": ["unique", "distinct"],
    "group": [
        "each department",
        "by department",
        "per department",
        "each course",
        "by course",
        "per course",
        "each year",
        "by year",
        "per year",
    ],
}


def detect_intent(question: str) -> dict:
    lowered = question.lower()
    intent = "list"
    aggregate = None
    group_by = None

    if any(token in lowered for token in ["how many", "count", "total number", "number of"]):
        intent = "count"
        aggregate = "count"
    elif any(token in lowered for token in ["average", "avg", "mean"]):
        intent = "avg"
        aggregate = "avg"
    elif any(token in lowered for token in ["sum", "total of", "total marks", "total score"]):
        intent = "sum"
        aggregate = "sum"
    elif any(token in lowered for token in ["minimum", "lowest", "min"]):
        intent = "min"
        aggregate = "min"
    elif any(token in lowered for token in ["maximum", "highest", "max", "top "]):
        intent = "max"
        aggregate = "max"
    elif any(token in lowered for token in ["unique", "distinct"]):
        intent = "distinct"
    elif any(token in lowered for token in ["each department", "by department", "per department"]):
        intent = "group"
        group_by = "department"
    elif any(token in lowered for token in ["each course", "by course", "per course"]):
        intent = "group"
        group_by = "course"
    elif any(token in lowered for token in ["each year", "by year", "per year"]):
        intent = "group"
        group_by = "year"

    if re.search(r"top\s+\d+|highest\s+\d+|lowest\s+\d+", lowered):
        intent = "top"
    if "show" in lowered or "list" in lowered or "display" in lowered or "find" in lowered:
        intent = "list"

    return {
        "intent": intent,
        "aggregate": aggregate,
        "group_by": group_by,
        "raw": lowered,
    }
