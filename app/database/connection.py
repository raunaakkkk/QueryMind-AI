from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from app.config import DB_PATH


def ensure_database_and_seed() -> None:
    ensure_database()
    from app.database.seed import seed_database

    conn = get_connection()
    try:
        conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='students'")
        if conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 0:
            seed_database(conn)
            conn.commit()
    finally:
        conn.close()

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    target = Path(db_path) if db_path is not None else DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def ensure_database() -> None:
    conn = get_connection()
    try:
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


def initialize_database() -> None:
    ensure_database()
    from app.database.seed import seed_database

    conn = get_connection()
    try:
        seed_database(conn)
        conn.commit()
    finally:
        conn.close()


def fetch_one(query: str, params: Iterable[object] | None = None, db_path: str | Path | None = None):
    params = tuple(params or ())
    conn = get_connection(db_path)
    try:
        row = conn.execute(query, params).fetchone()
        return dict(row) if row is not None else None
    finally:
        conn.close()
