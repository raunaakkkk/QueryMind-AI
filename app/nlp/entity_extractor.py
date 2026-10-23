from __future__ import annotations

import re
from typing import Any

DEPARTMENT_ALIASES = {
    "cse": "computer science",
    "computer science": "computer science",
    "computer science and engineering": "computer science",
    "it": "information technology",
    "information technology": "information technology",
    "ece": "electronics",
    "electronics": "electronics",
    "mech": "mechanical engineering",
    "mechanical": "mechanical engineering",
    "civil": "civil engineering",
    "math": "mathematics",
    "physics": "physics",
    "biotech": "biotechnology",
}

COURSE_ALIASES = {
    "data structures": "data structures",
    "database systems": "database systems",
    "algorithms": "algorithms",
    "operating systems": "operating systems",
    "computer networks": "computer networks",
    "software engineering": "software engineering",
    "digital logic": "digital logic",
    "signals and systems": "signals and systems",
    "thermodynamics": "thermodynamics",
    "fluid mechanics": "fluid mechanics",
    "structural analysis": "structural analysis",
    "engineering mathematics": "engineering mathematics",
    "electromagnetics": "electromagnetics",
    "quantum physics": "quantum physics",
    "molecular biology": "molecular biology",
    "bioinformatics": "bioinformatics",
    "applied statistics": "applied statistics",
    "discrete mathematics": "discrete mathematics",
    "circuit theory": "circuit theory",
    "machine learning": "machine learning",
}


def normalize_terms(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()


def extract_numeric_values(question: str) -> list[int]:
    values = []
    for match in re.findall(r"\b(\d+)\b", question):
        values.append(int(match))
    return values


def extract_comparison_filters(question: str) -> list[dict[str, Any]]:
    conditions: list[dict[str, Any]] = []
    patterns = [
        (r"(above|greater than|more than|over)\s+(\d+)", "gt"),
        (r"(below|less than|under|below)\s+(\d+)", "lt"),
        (r"(at least|minimum|no less than)\s+(\d+)", "gte"),
        (r"(at most|maximum|no more than|up to)\s+(\d+)", "lte"),
        (r"(equal to|equals|=)\s+(\d+)", "eq"),
        (r"(not equal|not equal to|!=)\s+(\d+)", "ne"),
    ]
    for pattern, operator in patterns:
        for match in re.finditer(pattern, question.lower()):
            value = int(match.group(2))
            conditions.append({"field": "marks", "operator": operator, "value": value})
    return conditions


def extract_department(question: str) -> str | None:
    normalized = normalize_terms(question)
    for alias, canonical in DEPARTMENT_ALIASES.items():
        if alias in normalized:
            return canonical
    return None


def extract_course(question: str) -> str | None:
    normalized = normalize_terms(question)
    for alias, canonical in COURSE_ALIASES.items():
        if alias in normalized:
            return canonical
    return None


def extract_year(question: str) -> int | None:
    matches = re.findall(r"\b(1|2|3|4)\s*(?:st|nd|rd|th)?\s*(?:year|yr)\b", question.lower())
    if matches:
        return int(matches[0])
    year_matches = re.findall(r"\b(2020|2021|2022|2023|2024|2025)\b", question)
    if year_matches:
        return int(year_matches[0])
    return None


def extract_limit(question: str) -> int | None:
    pattern = (
        r"\b(top|highest|lowest|first|last)\s+(\d+)\b"
        r"|\b(\d+)\s*(?:students|rows|records|results)\b"
    )
    match = re.search(pattern, question.lower())
    if match:
        if match.group(2):
            return int(match.group(2))
        if match.group(3):
            return int(match.group(3))
    return None


def extract_name(question: str) -> str | None:
    name_pattern = re.search(r"(?:student|name|named)\s+([a-z]+(?:\s+[a-z]+)?)", question.lower())
    if name_pattern:
        return name_pattern.group(1).strip()
    return None


def extract_entities(question: str) -> dict[str, Any]:
    return {
        "department": extract_department(question),
        "course": extract_course(question),
        "year": extract_year(question),
        "limit": extract_limit(question),
        "name": extract_name(question),
        "numeric_values": extract_numeric_values(question),
        "comparisons": extract_comparison_filters(question),
    }
