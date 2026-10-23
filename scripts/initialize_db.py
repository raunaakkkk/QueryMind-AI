from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

initialize_database = import_module("app.database.connection").initialize_database


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")