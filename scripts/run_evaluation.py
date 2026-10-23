from __future__ import annotations

import csv
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

initialize_database = import_module("app.database.connection").initialize_database
execute_question = import_module("app.services.query_service").execute_question
parse_question = import_module("app.services.query_service").parse_question

DATASET = ROOT / "data" / "evaluation_queries.csv"


def run_evaluation() -> dict[str, float | int]:
    initialize_database()
    total = 0
    expected_supported = 0
    expected_unsupported = 0
    correct_classifications = 0
    incorrect_classifications = 0
    successful_sql_executions = 0
    query_database_errors = 0
    unsupported_rejections = 0
    unexpected_errors = 0

    with DATASET.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total += 1
            question = (row.get("question") or "").strip()
            expected_intent = (row.get("intent") or "").strip().lower()
            if not expected_intent:
                raise ValueError(f"Evaluation case {total} has no intent label.")
            expects_unsupported = expected_intent == "unsupported"
            if expects_unsupported:
                expected_unsupported += 1
            else:
                expected_supported += 1

            parsed = parse_question(question)
            if parsed["supported"] != (not expects_unsupported):
                incorrect_classifications += 1
            else:
                correct_classifications += 1

            try:
                execute_question(question)
                successful_sql_executions += 1
            except ValueError:
                if parsed["supported"]:
                    query_database_errors += 1
                else:
                    unsupported_rejections += 1
            except Exception:
                unexpected_errors += 1

    return {
        "total_cases": total,
        "expected_supported_cases": expected_supported,
        "expected_unsupported_cases": expected_unsupported,
        "correct_classifications": correct_classifications,
        "incorrect_classifications": incorrect_classifications,
        "successful_sql_executions": successful_sql_executions,
        "query_database_errors": query_database_errors,
        "unsupported_query_rejections": unsupported_rejections,
        "unexpected_errors": unexpected_errors,
    }


if __name__ == "__main__":
    report = run_evaluation()
    print(report)
