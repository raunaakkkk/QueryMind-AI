from __future__ import annotations

from typing import Any


def explain_query(result: dict[str, Any]) -> str:
    intent = result.get("intent", "list")
    filters = result.get("filters", [])
    total = result.get("result_count", 0)
    if intent == "count":
        return f"This query counts the matching records and returned {total} result(s)."
    if intent == "avg":
        return (
            "This query calculates the average value across the matching records "
            f"and returned {total} result row(s)."
        )
    if intent == "sum":
        return f"This query sums the relevant numeric values and returned {total} result row(s)."
    if intent == "max":
        return f"This query finds the highest value in the selected dataset and returned {total} result row(s)."
    if intent == "min":
        return f"This query identifies the lowest value in the selected dataset and returned {total} result row(s)."
    if intent == "group":
        return f"This query groups the records by the requested dimension and returned {total} grouped result row(s)."
    if filters:
        return f"This query retrieves records matching the requested filter conditions and returned {total} row(s)."
    return f"This query fetches the requested student-related records and returned {total} row(s)."
