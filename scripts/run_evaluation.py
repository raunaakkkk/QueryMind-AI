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

DATASET = ROOT / "data" / "evaluation_queries.csv"


def run_evaluation() -> dict[str, float | int]:
    initialize_database()
    total = 0
    successful = 0
    correctly_handled = 0
    unsupported = 0
    failed = 0

    with DATASET.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total += 1
            question = (row.get("question") or "").strip()
            if not question:
                continue
            try:
                result = execute_question(question)
                successful += 1
                if result.get("supported") and result.get("result_count") is not None:
                    correctly_handled += 1
                if "unsupported" in question.lower() and result.get("supported"):
                    correctly_handled -= 1
            except ValueError:
                unsupported += 1
            except Exception:
                failed += 1

    accuracy = (correctly_handled / total) * 100 if total else 0
    return {
        "total": total,
        "successful": successful,
        "correctly_handled": correctly_handled,
        "unsupported": unsupported,
        "failed": failed,
        "accuracy": round(accuracy, 2),
    }


if __name__ == "__main__":
    report = run_evaluation()
    print(report)
