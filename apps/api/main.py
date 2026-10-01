from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from db import engine
from v1 import router as v1_router

app = FastAPI(title="Wardrobe API")
app.include_router(v1_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
def health_db() -> dict[str, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            version = conn.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            ).scalar()
    except Exception:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ok", "pgvector": version or "not installed"}
