from dataclasses import dataclass
import os


def _parse_csv_env(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "CasinoKing Backend")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    app_env: str = os.getenv("APP_ENV", "development")
    api_v1_prefix: str = os.getenv("API_V1_PREFIX", "/api/v1")
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://casinoking:casinoking@postgres:5432/casinoking",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    jwt_secret: str = os.getenv(
        "JWT_SECRET",
        "change-me-please-use-a-longer-local-secret",
    )
    jwt_access_token_ttl_minutes: int = int(
        os.getenv("JWT_ACCESS_TOKEN_TTL_MINUTES", "60")
    )
    site_access_password: str = os.getenv(
        "SITE_ACCESS_PASSWORD",
        "change-me",
    )
    mines_server_seed: str = os.getenv(
        "MINES_SERVER_SEED",
        "change-me-local-mines-server-seed",
    )
    cors_allowed_origins: tuple[str, ...] = _parse_csv_env(
        os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:3000",
        )
    )


settings = Settings()
