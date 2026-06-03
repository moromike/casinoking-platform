from __future__ import annotations

from dataclasses import asdict, dataclass

from app.modules.platform.game_codes import GAME_CODE_BOXE
from app.modules.platform.game_modules.descriptors import (
    EMBED_PROTOCOL_V1,
    STORAGE_ALLOWED_USES,
    build_replay_descriptor,
)


class GameModuleManifestNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class GameModuleRuntimeManifest:
    entry: str
    embed_protocol: str
    supported_modes: tuple[str, ...]
    frontend_package_ready: bool
    consumes_host_storage_namespace: bool
    consumes_neutral_embed_protocol: bool


@dataclass(frozen=True)
class GameModuleBackendManifest:
    action_api_version: int
    requires_platform_adapter: bool
    adapter_mode: str
    launch_token_endpoint: str | None
    launch_token_modes: tuple[str, ...]
    launch_token_optional_actions: tuple[str, ...]
    launch_token_required_actions: tuple[str, ...]
    token_authoritative_fields: tuple[str, ...]
    legacy_no_token_start_supported: bool
    service_ready: bool
    service_split_blockers: tuple[str, ...]


@dataclass(frozen=True)
class GameModuleAdminManifest:
    title_config_schema_version: int
    supports_copy_i18n: bool
    supports_assets: bool
    supports_theme: bool
    supports_sounds: bool
    arbitrary_code_allowed: bool


@dataclass(frozen=True)
class GameModuleAssetKindManifest:
    kind: str
    mime: tuple[str, ...]
    max_bytes: int
    recommended_dimensions: str
    render_mode: str
    required: bool = False


@dataclass(frozen=True)
class GameModuleI18nManifest:
    locales: tuple[str, ...]
    default_locale: str
    fallback_policy: str


@dataclass(frozen=True)
class GameModuleReportingManifest:
    descriptor_version: int
    player_replay_endpoint: str
    admin_replay_endpoint: str
    replay_payload_schema: str
    viewer: str
    account_summary_fields: tuple[str, ...]
    finance_summary_fields: tuple[str, ...]
    retention: str


@dataclass(frozen=True)
class GameModuleStorageManifest:
    namespace_from_launch_descriptor: bool
    allowed_uses: tuple[str, ...]
    forbidden_uses: tuple[str, ...]


@dataclass(frozen=True)
class GameModuleHostIntegrationManifest:
    selected_target: str
    physical_split: str
    mock_host_ready: bool
    forbidden_host_imports: tuple[str, ...]
    next_gate: str
    known_blockers: tuple[str, ...]


@dataclass(frozen=True)
class GameModuleManifest:
    manifest_version: int
    game_code: str
    display_name: str
    runtime: GameModuleRuntimeManifest
    backend: GameModuleBackendManifest
    admin: GameModuleAdminManifest
    reporting: GameModuleReportingManifest
    storage: GameModuleStorageManifest
    assets: tuple[GameModuleAssetKindManifest, ...]
    i18n: GameModuleI18nManifest
    host_integration: GameModuleHostIntegrationManifest
    test_gates: tuple[str, ...]


def get_game_module_manifest(game_code: str) -> GameModuleManifest:
    normalized_game_code = game_code.strip().lower()
    if normalized_game_code == GAME_CODE_BOXE:
        return build_boxe_game_module_manifest()
    raise GameModuleManifestNotFoundError(f"Game module manifest not found: {game_code}")


def serialize_game_module_manifest(manifest: GameModuleManifest) -> dict[str, object]:
    return asdict(manifest)


def build_boxe_game_module_manifest() -> GameModuleManifest:
    replay = build_replay_descriptor(game_code=GAME_CODE_BOXE)
    return GameModuleManifest(
        manifest_version=1,
        game_code=GAME_CODE_BOXE,
        display_name="BOXE",
        runtime=GameModuleRuntimeManifest(
            entry="/runtime/boxe",
            embed_protocol=EMBED_PROTOCOL_V1,
            supported_modes=("demo", "real"),
            frontend_package_ready=False,
            consumes_host_storage_namespace=False,
            consumes_neutral_embed_protocol=False,
        ),
        backend=GameModuleBackendManifest(
            action_api_version=1,
            requires_platform_adapter=True,
            adapter_mode="in_process_v1",
            launch_token_endpoint="/games/boxe/launch-token",
            launch_token_modes=("real",),
            launch_token_optional_actions=("start",),
            launch_token_required_actions=(),
            token_authoritative_fields=("title_code", "site_code", "game_code", "mode"),
            legacy_no_token_start_supported=True,
            service_ready=False,
            service_split_blockers=(
                "Platform adapter DTOs still carry psycopg.Cursor in-process state.",
                "Real-money open/settle must stay inside host wallet/ledger transaction boundaries.",
                "BOXE start accepts optional launch-token authority but strict token requirement is deferred.",
            ),
        ),
        admin=GameModuleAdminManifest(
            title_config_schema_version=1,
            supports_copy_i18n=True,
            supports_assets=True,
            supports_theme=True,
            supports_sounds=True,
            arbitrary_code_allowed=False,
        ),
        reporting=GameModuleReportingManifest(
            descriptor_version=1,
            player_replay_endpoint=replay.player_replay_endpoint,
            admin_replay_endpoint=replay.admin_replay_endpoint,
            replay_payload_schema=replay.replay_payload_schema,
            viewer=replay.viewer,
            account_summary_fields=replay.account_summary_fields,
            finance_summary_fields=replay.finance_summary_fields,
            retention=replay.retention,
        ),
        storage=GameModuleStorageManifest(
            namespace_from_launch_descriptor=True,
            allowed_uses=STORAGE_ALLOWED_USES,
            forbidden_uses=(
                "authoritative_player_identity",
                "wallet_balance",
                "hidden_outcome",
                "permanent_cross_host_token",
            ),
        ),
        assets=(
            GameModuleAssetKindManifest(
                kind="game_card",
                mime=("image/png", "image/jpeg", "image/webp"),
                max_bytes=300 * 1024,
                recommended_dimensions="512x512",
                render_mode="cover",
            ),
            GameModuleAssetKindManifest(
                kind="symbol_safe",
                mime=("image/png", "image/svg+xml"),
                max_bytes=150 * 1024,
                recommended_dimensions="256x256",
                render_mode="contain",
            ),
            GameModuleAssetKindManifest(
                kind="symbol_mine",
                mime=("image/png", "image/svg+xml"),
                max_bytes=150 * 1024,
                recommended_dimensions="256x256",
                render_mode="contain",
            ),
            GameModuleAssetKindManifest(
                kind="title_logo",
                mime=("image/png", "image/jpeg", "image/webp", "image/svg+xml"),
                max_bytes=300 * 1024,
                recommended_dimensions="wide transparent logo",
                render_mode="contain",
            ),
            GameModuleAssetKindManifest(
                kind="game_area_background",
                mime=("image/png", "image/jpeg", "image/webp"),
                max_bytes=800 * 1024,
                recommended_dimensions="1600x900",
                render_mode="cover",
            ),
            GameModuleAssetKindManifest(
                kind="audio_safe_reveal",
                mime=("audio/mpeg", "audio/ogg", "audio/wav", "audio/webm"),
                max_bytes=1024 * 1024,
                recommended_dimensions="short effect",
                render_mode="audio",
            ),
            GameModuleAssetKindManifest(
                kind="audio_mine_hit",
                mime=("audio/mpeg", "audio/ogg", "audio/wav", "audio/webm"),
                max_bytes=1024 * 1024,
                recommended_dimensions="short effect",
                render_mode="audio",
            ),
            GameModuleAssetKindManifest(
                kind="audio_collect",
                mime=("audio/mpeg", "audio/ogg", "audio/wav", "audio/webm"),
                max_bytes=1024 * 1024,
                recommended_dimensions="short effect",
                render_mode="audio",
            ),
            GameModuleAssetKindManifest(
                kind="audio_win",
                mime=("audio/mpeg", "audio/ogg", "audio/wav", "audio/webm"),
                max_bytes=1024 * 1024,
                recommended_dimensions="short effect",
                render_mode="audio",
            ),
        ),
        i18n=GameModuleI18nManifest(
            locales=("it", "en", "de", "es"),
            default_locale="it",
            fallback_policy="default-locale-then-packaged-copy",
        ),
        host_integration=GameModuleHostIntegrationManifest(
            selected_target="same_repo_manifest_first",
            physical_split="none",
            mock_host_ready=True,
            forbidden_host_imports=(
                "@/app/ui/boxe",
                "@/app/ui/mines",
                "@/app/ui/hi-lo",
                "@/app/ui/casinoking-console",
                "@/app/ui/player-account-page",
                "@/app/ui/site-v3-admin",
            ),
            next_gate="consume-launch-descriptor-in-runtime-actions",
            known_blockers=(
                "Runtime frontend still stores CasinoKing-oriented auth/demo keys.",
                "Embed protocol still keeps casinoking:* compatibility aliases.",
                "BOXE runtime does not yet send X-Game-Launch-Token on start.",
                "BOXE/HI-LO action APIs do not yet require X-Game-Launch-Token.",
                "Replay viewers are still imported directly by host account/finance UI.",
            ),
        ),
        test_gates=(
            "tests/contract/test_gmp5_game_module_manifest.py",
            "tests/integration/test_gmp5_mock_host_integration.py",
            "tests/contract/test_gmp3_host_neutral_descriptors.py",
            "tests/integration/test_gmp3_host_neutral_demo_launch.py",
            "tests/contract/test_gmp2_boxe_adapter_contract.py",
        ),
    )
