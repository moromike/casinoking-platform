from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class DatabaseConfig:
    database_url: str = settings.database_url


database_config = DatabaseConfig()
