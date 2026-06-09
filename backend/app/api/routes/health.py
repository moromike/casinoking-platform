from urllib.parse import urlparse
import socket

import psycopg
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.connection import db_connection

router = APIRouter(prefix="/health")


@router.get("/live")
def live() -> dict[str, object]:
    return {
        "success": True,
        "data": {
            "status": "live",
            "service": "backend",
        },
    }


@router.get("/ready")
def ready():
    checks = {
        "app": "ok",
        "database": _check_database(),
        "redis": _check_redis(),
    }
    is_ready = all(result == "ok" for result in checks.values())
    payload = {
        "status": "ready" if is_ready else "not_ready",
        "service": "backend",
        "checks": checks,
    }
    if is_ready:
        return {"success": True, "data": payload}
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"success": False, "data": payload},
    )


def _check_database() -> str:
    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
    except psycopg.Error:
        return "error"
    return "ok"


def _check_redis() -> str:
    parsed = urlparse(settings.redis_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    password = parsed.password
    try:
        with socket.create_connection((host, port), timeout=1.0) as client:
            client.settimeout(1.0)
            if password:
                client.sendall(_redis_command("AUTH", password))
                auth_response = client.recv(128)
                if not auth_response.startswith(b"+OK"):
                    return "error"
            client.sendall(_redis_command("PING"))
            response = client.recv(128)
    except OSError:
        return "error"
    return "ok" if response.startswith(b"+PONG") else "error"


def _redis_command(*parts: str) -> bytes:
    payload = f"*{len(parts)}\r\n"
    for part in parts:
        encoded = part.encode("utf-8")
        payload += f"${len(encoded)}\r\n{part}\r\n"
    return payload.encode("utf-8")
