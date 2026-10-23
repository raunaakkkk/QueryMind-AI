# Architecture

The application follows a layered architecture:

1. Frontend: a single-page HTML/CSS/JS interface served by FastAPI.
2. API layer: request validation and exposure of query and analytics endpoints.
3. Service layer: question parsing, SQL generation, explanation, analytics orchestration.
4. NLP layer: normalization, intent detection, entity extraction, schema mapping.
5. Database layer: SQLite initialization, foreign-key-safe schema, and reproducible seed script.

The query engine is intentionally deterministic and rule-based. It supports a defined subset of natural-language patterns and rejects unsafe SQL before execution.
