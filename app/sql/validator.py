from __future__ import annotations

import re

FORBIDDEN_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter", "create", "attach", "detach",
    "grant", "revoke", "replace", "truncate", "execute", "pragma", "begin", "commit",
    "rollback", "savepoint", "vacuum",
]


class ValidationError(ValueError):
    """Raised when an SQL statement fails the read-only safety checks."""


def validate_sql(sql: str) -> str:
    statement = sql.strip()
    if not statement:
        raise ValidationError("The SQL query is empty.")
    if ";" in statement:
        raise ValidationError("Multiple SQL statements are not allowed.")
    lowered = statement.lower()
    if not lowered.startswith("select") and not lowered.startswith("with"):
        raise ValidationError("Only SELECT queries are permitted.")
    if any(keyword in lowered for keyword in FORBIDDEN_KEYWORDS):
        raise ValidationError("Unsupported SQL operation detected.")
    if "--" in statement or "/*" in statement or "*/" in statement:
        raise ValidationError("Comments are not allowed in SQL input.")
    if re.search(r"\bunion\b.*\bselect\b", lowered):
        raise ValidationError("UNION queries are not permitted.")
    return statement
