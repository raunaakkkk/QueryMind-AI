from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.config import APP_TITLE, DB_PATH, MAX_QUERY_ROWS
from app.database.connection import ensure_database_and_seed, get_connection
from app.services.analytics_service import average_marks_by_course_or_department, department_distribution, summary_stats
from app.services.query_service import execute_question
from app.services.response_generator import explain_query

app = FastAPI(title=APP_TITLE)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(Path(__file__).resolve().parents[1] / "static" / "index.html"))


@app.get("/api/health")
def health() -> dict[str, object]:
    ensure_database_and_seed()
    conn = get_connection(DB_PATH)
    try:
        table_count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchone()[0]
        return {
            "status": "ok",
            "database": str(DB_PATH),
            "tables": table_count,
            "max_rows": MAX_QUERY_ROWS,
        }
    finally:
        conn.close()


@app.post("/api/query")
def query_api(request: QueryRequest) -> dict[str, object]:
    try:
        result = execute_question(request.question)
        result["explanation"] = explain_query(result)
        return result
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc), "supported": False})
    except Exception as exc:  # pragma: no cover
        return JSONResponse(status_code=500, content={"error": "Query execution failed.", "details": str(exc)})


@app.get("/api/schema")
def schema() -> dict[str, object]:
    conn = get_connection(DB_PATH)
    try:
        tables = []
        query = (
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        for row in conn.execute(query):
            table_name = row[0]
            columns = [
                {
                    "name": column[1],
                    "type": column[2],
                    "not_null": bool(column[3]),
                    "primary_key": bool(column[5]),
                }
                for column in conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
            ]
            tables.append({"name": table_name, "columns": columns})
        return {"tables": tables}
    finally:
        conn.close()


@app.get("/api/analytics/summary")
def analytics_summary() -> dict[str, object]:
    return summary_stats()


@app.get("/api/analytics/department-distribution")
def analytics_department_distribution() -> list[dict[str, object]]:
    return department_distribution()


@app.get("/api/analytics/average-marks")
def analytics_average_marks() -> list[dict[str, object]]:
    return average_marks_by_course_or_department()


@app.get("/api/tables/{table_name}")
def table_preview(table_name: str) -> dict[str, object]:
    allowed = {"departments", "students", "courses", "enrollments", "marks"}
    if table_name not in allowed:
        raise HTTPException(status_code=404, detail="Table is not allowed.")
    conn = get_connection(DB_PATH)
    try:
        columns = [row[1] for row in conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()]
        rows = conn.execute(f'SELECT * FROM "{table_name}" LIMIT 25').fetchall()
        return {"table": table_name, "columns": columns, "rows": [dict(row) for row in rows]}
    finally:
        conn.close()
