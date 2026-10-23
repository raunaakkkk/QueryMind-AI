from __future__ import annotations

import re

try:
    import spacy  # type: ignore
except Exception:  # pragma: no cover - fallback path
    spacy = None


def normalize_question(question: str) -> str:
    value = question.strip()
    value = re.sub(r"\s+", " ", value)
    value = value.lower()
    return value


def tokenize_question(question: str) -> list[str]:
    value = normalize_question(question)
    tokens = re.findall(r"[a-z0-9]+(?:\.[a-z0-9]+)?", value)
    if spacy is not None:
        try:
            nlp = spacy.blank("en")
            doc = nlp(value)
            tokens = [token.text.lower() for token in doc if not token.is_punct]
        except Exception:
            pass
    return tokens
