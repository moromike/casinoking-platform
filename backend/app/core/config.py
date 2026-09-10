from dataclasses import dataclass, field
import os
from pathlib import Path


def _parse_csv_env(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    app_name: str = field(
        default_factory=lambda: os.getenv("APP_NAME", "CasinoKing Backend")
    )
    app_version: str = field(
        default_factory=lambda: os.getenv("APP_VERSION", "0.1.0")
    )
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    api_v1_prefix: str = field(
        default_factory=lambda: os.getenv("API_V1_PREFIX", "/api/v1")
    )
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql://casinoking:casinoking@postgres:5432/casinoking",
        )
    )
    redis_url: str = field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://redis:6379/0")
    )
    jwt_secret: str = field(
        default_factory=lambda: os.getenv(
            "JWT_SECRET",
            "change-me-please-use-a-longer-local-secret",
        )
    )
    jwt_access_token_ttl_minutes: int = field(
        default_factory=lambda: int(os.getenv("JWT_ACCESS_TOKEN_TTL_MINUTES", "60"))
    )
    game_launch_token_ttl_minutes: int = field(
        default_factory=lambda: int(os.getenv("GAME_LAUNCH_TOKEN_TTL_MINUTES", "5"))
    )
    site_v3_draft_preview_secret: str = field(
        default_factory=lambda: os.getenv(
            "SITE_V3_DRAFT_PREVIEW_SECRET",
            "change-me-site-v3-draft-preview-secret-local-only",
        )
    )
    site_v3_public_base_url: str = field(
        default_factory=lambda: os.getenv(
            "SITE_V3_PUBLIC_BASE_URL",
            "http://localhost:3000",
        ).rstrip("/")
    )
    site_access_password: str = field(
        default_factory=lambda: os.getenv(
            "SITE_ACCESS_PASSWORD",
            "change-me",
        )
    )
    mines_server_seed: str = field(
        default_factory=lambda: os.getenv(
            "MINES_SERVER_SEED",
            "change-me-local-mines-server-seed",
        )
    )
    cors_allowed_origins: tuple[str, ...] = field(
        default_factory=lambda: _parse_csv_env(
            os.getenv(
                "CORS_ALLOWED_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
            )
        )
    )
    asset_storage_root: Path = field(
        default_factory=lambda: Path(os.getenv("ASSET_STORAGE_ROOT", "var/assets"))
    )
    asset_public_base_url: str = field(
        default_factory=lambda: os.getenv(
            "ASSET_PUBLIC_BASE_URL",
            "/static/games",
        ).rstrip("/")
    )

    # LA FINESTRA DEL CONFINE ESTERNO (POR-03, D7).
    # Senza momento una richiesta intercettata resta valida per sempre. La
    # finestra e' asimmetrica apposta: nel passato si tollera la latenza di rete
    # e le code di un fornitore, nel futuro solo lo scarto di orologio, perche'
    # un timestamp nel futuro non ha ragioni legittime di essere lontano.
    seamless_finestra_passato_secondi: int = field(
        default_factory=lambda: int(os.getenv("SEAMLESS_FINESTRA_PASSATO_SECONDI", "300"))
    )
    seamless_finestra_futuro_secondi: int = field(
        default_factory=lambda: int(os.getenv("SEAMLESS_FINESTRA_FUTURO_SECONDI", "60"))
    )
    # LA PORTA DI SERVIZIO, E PERCHE' NON SI APRE IN PRODUZIONE.
    # Serve ai collaudi storici che portano timestamp fissi del 7/09/2026.
    # Lasciarla aperta in produzione rimetterebbe esattamente il difetto che
    # POR-03 chiude: la sfida al piano l'ha chiamata "porta di servizio
    # pericolosa" ed aveva ragione. validate_for_environment la vieta.
    seamless_finestra_disattivata: bool = field(
        default_factory=lambda: os.getenv("SEAMLESS_FINESTRA_DISATTIVATA", "0") == "1"
    )

    def validate_for_environment(self) -> None:
        if self.app_env not in ("production", "prod"):
            return
        weak: list[str] = []
        secret_fields = (
            ("JWT_SECRET", self.jwt_secret),
            ("SITE_V3_DRAFT_PREVIEW_SECRET", self.site_v3_draft_preview_secret),
            ("SITE_ACCESS_PASSWORD", self.site_access_password),
            ("MINES_SERVER_SEED", self.mines_server_seed),
        )
        for name, value in secret_fields:
            lowered = value.lower()
            if len(value) < 24 or "change-me" in lowered or "changeme" in lowered:
                weak.append(name)
        if "casinoking:casinoking@" in self.database_url:
            weak.append("DATABASE_URL")
        if weak:
            raise RuntimeError(
                "Segreti deboli in ambiente di produzione: " + ", ".join(weak)
            )
        # D7: la finestra del confine non si disattiva in produzione, mai.
        # Un interruttore che spegne un controllo di sicurezza e che qualcuno
        # puo' accendere con una variabile d'ambiente non e' un parametro: e'
        # il controllo stesso reso opzionale.
        if self.seamless_finestra_disattivata:
            raise RuntimeError(
                "SEAMLESS_FINESTRA_DISATTIVATA=1 in produzione: la finestra "
                "temporale del confine esterno non si spegne. Senza, una "
                "richiesta intercettata resta valida per sempre (POR-03)."
            )


settings = Settings()
