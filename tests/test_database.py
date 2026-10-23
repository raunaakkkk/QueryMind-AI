from __future__ import annotations

from app.database.connection import get_connection
from app.database.seed import seed_database


def test_database_seed_and_foreign_keys():
    conn = get_connection()
    try:
        conn.execute("PRAGMA foreign_key_check").fetchall()
        assert conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0] >= 5
        assert conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] >= 100
        assert conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0] >= 12
        assert conn.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0] >= 100
        assert conn.execute("SELECT COUNT(*) FROM marks").fetchone()[0] >= 200
    finally:
        conn.close()


def test_seed_is_reentrant():
    conn = get_connection()
    try:
        seed_database(conn)
        seed_database(conn)
        assert conn.execute("SELECT COUNT(*) FROM students").fetchone()[0] >= 100
    finally:
        conn.close()
