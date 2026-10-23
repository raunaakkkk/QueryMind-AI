from __future__ import annotations

import csv

import pytest

from scripts import run_evaluation


def test_evaluation_separates_classification_and_execution_outcomes(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    dataset = tmp_path / "evaluation_queries.csv"
    rows = [
        {"question": "supported success", "intent": "list", "expected_behavior": "free text"},
        {"question": "supported error", "intent": "avg", "expected_behavior": "free text"},
        {"question": "unsupported reject", "intent": "unsupported", "expected_behavior": "free text"},
        {"question": "unsupported mismatch", "intent": "unsupported", "expected_behavior": "free text"},
    ]
    with dataset.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    parsed_support = {
        "supported success": True,
        "supported error": True,
        "unsupported reject": False,
        "unsupported mismatch": True,
    }

    def execute(question: str) -> dict[str, object]:
        if question == "supported error":
            raise ValueError("Database error: invalid query")
        if question == "unsupported reject":
            raise ValueError("This question is unsupported.")
        return {"supported": True, "result_count": 0}

    monkeypatch.setattr(run_evaluation, "DATASET", dataset)
    monkeypatch.setattr(run_evaluation, "initialize_database", lambda: None)
    monkeypatch.setattr(
        run_evaluation,
        "parse_question",
        lambda question: {"supported": parsed_support[question]},
    )
    monkeypatch.setattr(run_evaluation, "execute_question", execute)

    report = run_evaluation.run_evaluation()

    assert report == {
        "total_cases": 4,
        "expected_supported_cases": 2,
        "expected_unsupported_cases": 2,
        "correct_classifications": 3,
        "incorrect_classifications": 1,
        "successful_sql_executions": 2,
        "query_database_errors": 1,
        "unsupported_query_rejections": 1,
        "unexpected_errors": 0,
    }
    assert "accuracy" not in report
