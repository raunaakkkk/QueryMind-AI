from __future__ import annotations

from fastapi.staticfiles import StaticFiles

from app.api.routes import app as api_app
from app.config import BASE_DIR
from app.database.connection import ensure_database_and_seed

ensure_database_and_seed()
app = api_app
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
