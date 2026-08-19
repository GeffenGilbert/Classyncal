import os

import redis
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.base import get_db

router = APIRouter()

@router.get("/")
def home():
    return {"message": "Hello from the backend!"}

@router.get("/test")
def test():
    return {
        "status": "success",
        "message": "React successfully connected to FastAPI"
    }


# The uptime monitor points here, so this has to fail when a dependency is
# down. A route returning a hardcoded string would keep reporting "up" with
# Postgres on fire, which makes the soak test worse than useless - it would
# tell us the box held when we never actually checked.
@router.get("/health")
def health(db: Session = Depends(get_db)):
    checks = {}

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {type(exc).__name__}"

    try:
        client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://redis:6379"),
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {type(exc).__name__}"

    healthy = all(value == "ok" for value in checks.values())

    # 503 rather than a 200 carrying {"status": "unhealthy"} - uptime monitors
    # and Docker healthchecks both key off the status code, not the body.
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ok" if healthy else "degraded", "checks": checks},
    )
