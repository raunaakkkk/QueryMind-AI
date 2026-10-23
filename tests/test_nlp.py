from __future__ import annotations

from app.nlp.entity_extractor import extract_entities
from app.nlp.intent_detector import detect_intent
from app.nlp.preprocessing import normalize_question


def test_normalize_question():
    text = "  Show students from CSE  "
    assert normalize_question(text) == "show students from cse"


def test_detect_intent_count():
    detection = detect_intent("How many students are there in each department?")
    assert detection["intent"] in {"count", "group"}


def test_extract_entities():
    entities = extract_entities("Find students in computer science with marks above 80")
    assert entities["department"] == "computer science"
    assert 80 in entities["numeric_values"]
