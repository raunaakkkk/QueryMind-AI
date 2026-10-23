from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = Path(os.getenv("QUERYMIND_DB_PATH", str(DATA_DIR / "college.db"))).resolve()
MAX_QUERY_ROWS = int(os.getenv("QUERYMIND_MAX_ROWS", "200"))
QUERY_TIMEOUT_SECONDS = int(os.getenv("QUERYMIND_TIMEOUT_SECONDS", "5"))
APP_TITLE = "NLP Database Interaction"
