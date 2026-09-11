from uuid import uuid4
import pytest
import httpx
from tests.conftest import user_cleanup_coordinator, _decode_access_token_role
from typing import Generator, Any

from app.modules.games.mines.randomness import generate_board
from app.modules.games.mines.runtime import get_runtime_config
import psycopg
from psycopg.rows import DictRow
from psycopg.types.json import Jsonb
import copy

type DbConnection = psycopg.Connection[DictRow]
type DbCursor = psycopg.Cursor[DictRow]


MINES_DEFAULT_TITLE_CODE = "mines_classic"

TITLE_CONFIG_GENERIC_COLUMNS = (
    "title_code",
    "rules_sections_json",
    "ui_labels_json",
    "bet_limits_json",
    "demo_labels_json",
    "theme_tokens_json",
    "draft_rules_sections_json",
    "draft_ui_labels_json",
    "draft_bet_limits_json",
    "draft_demo_labels_json",
    "draft_theme_tokens_json",
    "published_at",
    "updated_by_admin_user_id",
    "draft_updated_by_admin_user_id",
    "draft_updated_at",
)

TITLE_CONFIG_GENERIC_JSON_COLUMNS = {
    "rules_sections_json",
    "ui_labels_json",
    "bet_limits_json",
    "demo_labels_json",
    "theme_tokens_json",
    "draft_rules_sections_json",
    "draft_ui_labels_json",
    "draft_bet_limits_json",
    "draft_demo_labels_json",
    "draft_theme_tokens_json",
}

MINES_TITLE_CONFIG_COLUMNS = (
    "title_code",
    "published_grid_sizes_json",
    "published_mine_counts_json",
    "default_mine_counts_json",
    "published_board_assets_json",
    "draft_grid_sizes_json",
    "draft_mine_counts_json",
    "draft_default_mine_counts_json",
    "draft_board_assets_json",
    "created_at",
    "updated_at",
)
MINES_TITLE_CONFIG_JSON_COLUMNS = {
    "published_grid_sizes_json",
    "published_mine_counts_json",
    "default_mine_counts_json",
    "published_board_assets_json",
    "draft_grid_sizes_json",
    "draft_mine_counts_json",
    "draft_default_mine_counts_json",
    "draft_board_assets_json",
}
@pytest.fixture
def preserve_mines_backoffice_config(
    db_connection: DbConnection,
) -> Generator[None, None, None]:
    """Preserve and restore Mines backoffice config across tests.

    After Phase 3 the configuration lives in two tables: `title_configs` (engine
    agnostic) and `mines_title_configs` (engine specific). The legacy view
    `mines_backoffice_config` is read-only by design (no INSTEAD OF triggers),
    so writers must operate on the new tables directly.
    """

    with db_connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT {", ".join(TITLE_CONFIG_GENERIC_COLUMNS)}
            FROM title_configs
            WHERE title_code = %s
            """,
            (MINES_DEFAULT_TITLE_CODE,),
        )
        generic_snapshot = cursor.fetchone()

        cursor.execute(
            f"""
            SELECT {", ".join(MINES_TITLE_CONFIG_COLUMNS)}
            FROM mines_title_configs
            WHERE title_code = %s
            """,
            (MINES_DEFAULT_TITLE_CODE,),
        )
        engine_snapshot = cursor.fetchone()

    if generic_snapshot is None or engine_snapshot is None:
        baseline = _build_test_mines_backoffice_snapshot()
        with db_connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO title_configs (
                    title_code,
                    rules_sections_json,
                    ui_labels_json,
                    published_at,
                    updated_at
                )
                VALUES (%s, %s::jsonb, %s::jsonb, NOW(), NOW())
                ON CONFLICT (title_code) DO NOTHING
                """,
                (
                    MINES_DEFAULT_TITLE_CODE,
                    Jsonb(baseline["rules_sections"]),
                    Jsonb(baseline["ui_labels"]),
                ),
            )
            cursor.execute(
                """
                INSERT INTO mines_title_configs (
                    title_code,
                    published_grid_sizes_json,
                    published_mine_counts_json,
                    default_mine_counts_json,
                    published_board_assets_json,
                    updated_at
                )
                VALUES (%s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, NOW())
                ON CONFLICT (title_code) DO NOTHING
                """,
                (
                    MINES_DEFAULT_TITLE_CODE,
                    Jsonb(baseline["published_grid_sizes"]),
                    Jsonb(baseline["published_mine_counts"]),
                    Jsonb(baseline["default_mine_counts"]),
                    Jsonb(baseline["board_assets"]),
                ),
            )

    preserved_generic = copy.deepcopy(generic_snapshot) if generic_snapshot is not None else None
    preserved_engine = copy.deepcopy(engine_snapshot) if engine_snapshot is not None else None
    yield

    with db_connection.cursor() as cursor:
        if preserved_generic is not None:
            generic_values = [
                Jsonb(preserved_generic[column])
                if column in TITLE_CONFIG_GENERIC_JSON_COLUMNS and preserved_generic[column] is not None
                else preserved_generic[column]
                for column in TITLE_CONFIG_GENERIC_COLUMNS
            ]
            cursor.execute(
                f"""
                INSERT INTO title_configs ({", ".join(TITLE_CONFIG_GENERIC_COLUMNS)})
                VALUES ({", ".join(["%s"] * len(TITLE_CONFIG_GENERIC_COLUMNS))})
                ON CONFLICT (title_code) DO UPDATE SET
                    {", ".join(f"{col} = EXCLUDED.{col}" for col in TITLE_CONFIG_GENERIC_COLUMNS if col != 'title_code')}
                """,
                generic_values,
            )

        if preserved_engine is not None:
            engine_values = [
                Jsonb(preserved_engine[column])
                if column in MINES_TITLE_CONFIG_JSON_COLUMNS and preserved_engine[column] is not None
                else preserved_engine[column]
                for column in MINES_TITLE_CONFIG_COLUMNS
            ]
            cursor.execute(
                f"""
                INSERT INTO mines_title_configs ({", ".join(MINES_TITLE_CONFIG_COLUMNS)})
                VALUES ({", ".join(["%s"] * len(MINES_TITLE_CONFIG_COLUMNS))})
                ON CONFLICT (title_code) DO UPDATE SET
                    {", ".join(f"{col} = EXCLUDED.{col}" for col in MINES_TITLE_CONFIG_COLUMNS if col != 'title_code')}
                """,
                engine_values,
            )


# NON E' PIU' `autouse`, dal 10/09/2026 (PASSO 4B).
# La riga canonica di `sites` la sporca UN solo file di collaudo su 141
# (misura in missioni/2026-09-10-passo4b/01-analisi/G5-invariante-per-file.txt):
# tests/integration/test_hi_lo_service.py, dove `_open_hi_lo_real_table` ha
# `site_code="casinoking"` come valore predefinito e riscrive `display_name`
# con un ON CONFLICT DO UPDATE. Ora la chiede solo quel file, con una fixture
# `autouse` di modulo che dipende da questa.
# ATTENZIONE: e' un PRESERVE, non un RESET — fotografa il valore che trova e
# lo ripristina a fine collaudo. Se la riga arriva GIA' sporca, questa fixture
# conserva la sporcatura: non garantisce la baseline, garantisce solo che chi
# sporca ripulisca.
# E LA GARANZIA RIGUARDA QUATTRO COLONNE SU SEI: `site_code`, `display_name`,
# `base_url`, `status`. NON conserva `created_at` ne' `updated_at`, e anzi il
# ripristino forza sempre `updated_at = NOW()`: a ogni teardown il timestamp
# avanza comunque. E' accettabile perche' NESSUN collaudo della suite asserisce
# su `sites.updated_at` ne' su `sites.created_at` (verificato il 10/09/2026:
# `grep -rn "updated_at" tests/ --include=*.py | grep -i site` non restituisce
# alcuna riga). Se un giorno un collaudo guardasse quei timestamp, questa
# fixture andrebbe estesa a sei colonne.
# Chi la rimette `autouse` si riprenda anche questa frase: il punto non e' la
# velocita', e' che la radice della suite non deve pagare la pulizia di un
# difetto che appartiene a un file solo.
@pytest.fixture
def create_published_mines_variant(db_connection: DbConnection, _mines_cleanup_registrar):
    created_title_codes: set[str] = set()

    def _create_published_mines_variant(
        *,
        title_code: str | None = None,
        display_name: str = "Mines Test Variant",
        site_code: str = "casinoking",
        lobby_visibility: str = "visible",
        demo_enabled: bool = True,
        real_enabled: bool = True,
        cleanup: bool = True,
    ) -> dict[str, object]:
        resolved_title_code = title_code or f"mines_test_{uuid4().hex[:8]}"
        with db_connection.cursor() as cursor:
            _upsert_published_mines_variant(
                cursor=cursor,
                title_code=resolved_title_code,
                display_name=display_name,
                site_code=site_code,
                lobby_visibility=lobby_visibility,
                demo_enabled=demo_enabled,
                real_enabled=real_enabled,
            )
        if cleanup:
            created_title_codes.add(resolved_title_code)
        return {
            "title_code": resolved_title_code,
            "site_code": site_code,
            "display_name": display_name,
        }

    yield _create_published_mines_variant

    for title_code in created_title_codes:
        _cleanup_mines_variant_if_unreferenced(
            db_connection=db_connection,
            title_code=title_code,
        )


@pytest.fixture
def track_mines_variant_cleanup(db_connection: DbConnection, _mines_cleanup_registrar):
    created_title_codes: set[str] = set()

    def _track_mines_variant_cleanup(title_code: str) -> str:
        created_title_codes.add(title_code)
        return title_code

    yield _track_mines_variant_cleanup

    for title_code in created_title_codes:
        _cleanup_mines_variant_if_unreferenced(
            db_connection=db_connection,
            title_code=title_code,
        )


def _upsert_published_mines_variant(
    *,
    cursor,
    title_code: str,
    display_name: str,
    site_code: str,
    lobby_visibility: str,
    demo_enabled: bool,
    real_enabled: bool,
) -> None:
    cursor.execute(
        """
        INSERT INTO game_titles (
            title_code,
            engine_code,
            display_name,
            status,
            is_master,
            source_title_code
        )
        SELECT
            %s,
            engine_code,
            %s,
            'active',
            false,
            title_code
        FROM game_titles
        WHERE title_code = %s
        ON CONFLICT (title_code) DO UPDATE
        SET display_name = EXCLUDED.display_name,
            status = 'active',
            is_master = false,
            source_title_code = %s,
            updated_at = NOW()
        """,
        (title_code, display_name, MINES_DEFAULT_TITLE_CODE, MINES_DEFAULT_TITLE_CODE),
    )
    cursor.execute(
        """
        INSERT INTO site_titles (
            site_code,
            title_code,
            position,
            status,
            lobby_visibility,
            demo_enabled,
            real_enabled,
            lobby_display_name,
            lobby_description,
            featured
        )
        VALUES (%s, %s, 999, 'active', %s, %s, %s, %s, 'Test publication variant', false)
        ON CONFLICT (site_code, title_code) DO UPDATE
        SET status = 'active',
            lobby_visibility = EXCLUDED.lobby_visibility,
            demo_enabled = EXCLUDED.demo_enabled,
            real_enabled = EXCLUDED.real_enabled,
            lobby_display_name = EXCLUDED.lobby_display_name,
            lobby_description = EXCLUDED.lobby_description,
            featured = EXCLUDED.featured,
            updated_at = NOW()
        """,
        (
            site_code,
            title_code,
            lobby_visibility,
            demo_enabled,
            real_enabled,
            display_name,
        ),
    )
    cursor.execute(
        """
        INSERT INTO title_configs (
            title_code,
            rules_sections_json,
            ui_labels_json,
            bet_limits_json,
            demo_labels_json,
            theme_tokens_json,
            draft_rules_sections_json,
            draft_ui_labels_json,
            draft_bet_limits_json,
            draft_demo_labels_json,
            draft_theme_tokens_json,
            published_at,
            updated_by_admin_user_id,
            draft_updated_by_admin_user_id,
            draft_updated_at
        )
        SELECT
            %s,
            rules_sections_json,
            ui_labels_json,
            bet_limits_json,
            demo_labels_json,
            theme_tokens_json,
            draft_rules_sections_json,
            draft_ui_labels_json,
            draft_bet_limits_json,
            draft_demo_labels_json,
            draft_theme_tokens_json,
            COALESCE(published_at, NOW()),
            updated_by_admin_user_id,
            draft_updated_by_admin_user_id,
            COALESCE(draft_updated_at, NOW())
        FROM title_configs
        WHERE title_code = %s
        ON CONFLICT (title_code) DO UPDATE
        SET rules_sections_json = EXCLUDED.rules_sections_json,
            ui_labels_json = EXCLUDED.ui_labels_json,
            bet_limits_json = EXCLUDED.bet_limits_json,
            demo_labels_json = EXCLUDED.demo_labels_json,
            theme_tokens_json = EXCLUDED.theme_tokens_json,
            draft_rules_sections_json = EXCLUDED.draft_rules_sections_json,
            draft_ui_labels_json = EXCLUDED.draft_ui_labels_json,
            draft_bet_limits_json = EXCLUDED.draft_bet_limits_json,
            draft_demo_labels_json = EXCLUDED.draft_demo_labels_json,
            draft_theme_tokens_json = EXCLUDED.draft_theme_tokens_json,
            published_at = EXCLUDED.published_at,
            updated_at = NOW()
        """,
        (title_code, MINES_DEFAULT_TITLE_CODE),
    )
    cursor.execute(
        """
        INSERT INTO mines_title_configs (
            title_code,
            published_grid_sizes_json,
            published_mine_counts_json,
            default_mine_counts_json,
            published_board_assets_json,
            draft_grid_sizes_json,
            draft_mine_counts_json,
            draft_default_mine_counts_json,
            draft_board_assets_json
        )
        SELECT
            %s,
            published_grid_sizes_json,
            published_mine_counts_json,
            default_mine_counts_json,
            published_board_assets_json,
            draft_grid_sizes_json,
            draft_mine_counts_json,
            draft_default_mine_counts_json,
            draft_board_assets_json
        FROM mines_title_configs
        WHERE title_code = %s
        ON CONFLICT (title_code) DO UPDATE
        SET published_grid_sizes_json = EXCLUDED.published_grid_sizes_json,
            published_mine_counts_json = EXCLUDED.published_mine_counts_json,
            default_mine_counts_json = EXCLUDED.default_mine_counts_json,
            published_board_assets_json = EXCLUDED.published_board_assets_json,
            draft_grid_sizes_json = EXCLUDED.draft_grid_sizes_json,
            draft_mine_counts_json = EXCLUDED.draft_mine_counts_json,
            draft_default_mine_counts_json = EXCLUDED.draft_default_mine_counts_json,
            draft_board_assets_json = EXCLUDED.draft_board_assets_json,
            updated_at = NOW()
        """,
        (title_code, MINES_DEFAULT_TITLE_CODE),
    )


def _cleanup_test_users(
    *,
    db_connection: DbConnection,
    user_ids: list[str],
) -> None:
    if not user_ids:
        return

    unique_user_ids = sorted(set(user_ids))
    with db_connection.transaction():
        with db_connection.cursor() as cursor:
            cursor.execute(
                "CREATE TEMP TABLE cleanup_users ON COMMIT DROP AS SELECT UNNEST(%s::uuid[]) AS id",
                (unique_user_ids,),
            )
            cursor.execute(
                """
                CREATE TEMP TABLE cleanup_wallet_accounts ON COMMIT DROP AS
                SELECT id FROM wallet_accounts
                WHERE user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                CREATE TEMP TABLE cleanup_ledger_accounts ON COMMIT DROP AS
                SELECT id FROM ledger_accounts
                WHERE owner_user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                CREATE TEMP TABLE cleanup_transactions ON COMMIT DROP AS
                SELECT id FROM ledger_transactions
                WHERE user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                DELETE FROM demo_round_events
                WHERE demo_play_session_id IN (
                    SELECT id FROM demo_play_sessions
                    WHERE user_id IN (SELECT id FROM cleanup_users)
                )
                """
            )
            cursor.execute("SELECT to_regclass('public.mines_game_rounds') AS table_name")
            if cursor.fetchone()["table_name"] is not None:
                cursor.execute(
                    """
                    CREATE TEMP TABLE IF NOT EXISTS targeted_cleanup_mines_round_ids ON COMMIT DROP AS
                    SELECT id FROM mines_game_rounds
                    WHERE user_id IN (SELECT id FROM cleanup_users)
                       OR platform_round_id IN (
                          SELECT id FROM platform_rounds
                          WHERE user_id IN (SELECT id FROM cleanup_users)
                       )
                    """
                )
                cursor.execute("SELECT to_regclass('public.game_idempotency_keys') AS table_name")
                if cursor.fetchone()["table_name"] is not None:
                    cursor.execute(
                        """
                        DELETE FROM game_idempotency_keys
                        WHERE game_code = 'mines'
                          AND (round_id IN (SELECT id FROM targeted_cleanup_mines_round_ids)
                            OR player_id IN (SELECT id FROM cleanup_users))
                        """
                    )
                cursor.execute(
                    """
                    DELETE FROM mines_game_rounds
                    WHERE id IN (SELECT id FROM targeted_cleanup_mines_round_ids)
                    """
                )
            cursor.execute(
                """
                DELETE FROM demo_play_sessions
                WHERE user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute("SELECT to_regclass('public.boxe_rounds') AS table_name")
            if cursor.fetchone()["table_name"] is not None:
                cursor.execute(
                    """
                    CREATE TEMP TABLE IF NOT EXISTS targeted_cleanup_boxe_round_ids ON COMMIT DROP AS
                    SELECT id FROM boxe_rounds
                    WHERE platform_round_id IN (
                        SELECT id FROM platform_rounds
                        WHERE user_id IN (SELECT id FROM cleanup_users)
                    )
                    """
                )
                cursor.execute("SELECT to_regclass('public.game_idempotency_keys') AS table_name")
                if cursor.fetchone()["table_name"] is not None:
                    cursor.execute(
                        """
                        DELETE FROM game_idempotency_keys
                        WHERE game_code = 'boxe'
                          AND (round_id IN (SELECT id FROM targeted_cleanup_boxe_round_ids)
                            OR player_id IN (SELECT id FROM cleanup_users))
                        """
                    )
                cursor.execute(
                    """
                    DELETE FROM boxe_rounds
                    WHERE id IN (SELECT id FROM targeted_cleanup_boxe_round_ids)
                    """
                )
            cursor.execute(
                """
                DELETE FROM platform_rounds
                WHERE user_id IN (SELECT id FROM cleanup_users)
                   OR wallet_account_id IN (SELECT id FROM cleanup_wallet_accounts)
                   OR start_ledger_transaction_id IN (SELECT id FROM cleanup_transactions)
                   OR settlement_ledger_transaction_id IN (SELECT id FROM cleanup_transactions)
                """
            )
            cursor.execute(
                """
                DELETE FROM game_table_sessions
                WHERE user_id IN (SELECT id FROM cleanup_users)
                   OR wallet_account_id IN (SELECT id FROM cleanup_wallet_accounts)
                   OR access_session_id IN (
                      SELECT id FROM game_access_sessions
                      WHERE user_id IN (SELECT id FROM cleanup_users)
                   )
                """
            )
            cursor.execute(
                """
                DELETE FROM game_access_sessions
                WHERE user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                DELETE FROM admin_actions
                WHERE admin_user_id IN (SELECT id FROM cleanup_users)
                   OR target_user_id IN (SELECT id FROM cleanup_users)
                   OR ledger_transaction_id IN (SELECT id FROM cleanup_transactions)
                """
            )
            cursor.execute(
                """
                DELETE FROM admin_audit_log
                WHERE admin_user_id IN (SELECT id FROM cleanup_users)
                   OR resource_id IN (SELECT id::text FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                UPDATE title_assets
                SET uploaded_by_admin_user_id = NULL
                WHERE uploaded_by_admin_user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                UPDATE title_locale_maps
                SET created_by_admin_user_id = NULL
                WHERE created_by_admin_user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                UPDATE title_locale_maps
                SET published_by_admin_user_id = NULL
                WHERE published_by_admin_user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                UPDATE site_home_slots
                SET created_by = NULL
                WHERE created_by IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                UPDATE site_home_slots
                SET updated_by = NULL
                WHERE updated_by IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                UPDATE title_configs
                SET updated_by_admin_user_id = NULL
                WHERE updated_by_admin_user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                UPDATE title_configs
                SET draft_updated_by_admin_user_id = NULL
                WHERE draft_updated_by_admin_user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                UPDATE mines_backoffice_config_legacy
                SET updated_by_admin_user_id = NULL
                WHERE updated_by_admin_user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                UPDATE mines_backoffice_config_legacy
                SET draft_updated_by_admin_user_id = NULL
                WHERE draft_updated_by_admin_user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                UPDATE fairness_seed_rotations
                SET rotated_by_admin_user_id = NULL
                WHERE rotated_by_admin_user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                DELETE FROM ledger_entries
                WHERE transaction_id IN (SELECT id FROM cleanup_transactions)
                   OR ledger_account_id IN (SELECT id FROM cleanup_ledger_accounts)
                """
            )
            cursor.execute(
                """
                DELETE FROM ledger_transactions
                WHERE id IN (SELECT id FROM cleanup_transactions)
                """
            )
            cursor.execute(
                """
                DELETE FROM wallet_accounts
                WHERE id IN (SELECT id FROM cleanup_wallet_accounts)
                """
            )
            cursor.execute(
                """
                DELETE FROM ledger_accounts
                WHERE id IN (SELECT id FROM cleanup_ledger_accounts)
                """
            )
            cursor.execute("SELECT to_regclass('public.site_v3_pages') AS table_name")
            if cursor.fetchone()["table_name"] is not None:
                cursor.execute("SELECT to_regclass('public.site_v3_module_definitions') AS table_name")
                if cursor.fetchone()["table_name"] is not None:
                    cursor.execute(
                        """
                        DELETE FROM site_v3_module_definitions definition
                        WHERE definition.created_by IN (SELECT id FROM cleanup_users)
                           OR definition.updated_by IN (SELECT id FROM cleanup_users)
                           OR definition.published_by IN (SELECT id FROM cleanup_users)
                           OR definition.archived_by IN (SELECT id FROM cleanup_users)
                           OR EXISTS (
                              SELECT 1
                              FROM site_v3_module_definition_versions version
                              WHERE version.definition_id = definition.id
                                AND (
                                    version.created_by IN (SELECT id FROM cleanup_users)
                                    OR version.published_by IN (SELECT id FROM cleanup_users)
                                )
                           )
                        """
                    )
                cursor.execute(
                    """
                    DELETE FROM site_v3_pages page
                    WHERE page.created_by IN (SELECT id FROM cleanup_users)
                       OR page.updated_by IN (SELECT id FROM cleanup_users)
                       OR page.archived_by IN (SELECT id FROM cleanup_users)
                       OR EXISTS (
                          SELECT 1
                          FROM site_v3_page_versions version
                          WHERE version.page_id = page.id
                            AND (
                                version.created_by IN (SELECT id FROM cleanup_users)
                                OR version.published_by IN (SELECT id FROM cleanup_users)
                            )
                       )
                       OR EXISTS (
                          SELECT 1
                          FROM site_v3_modules module
                          WHERE module.page_id = page.id
                            AND (
                                module.created_by IN (SELECT id FROM cleanup_users)
                                OR module.updated_by IN (SELECT id FROM cleanup_users)
                            )
                       )
                    """
                )
            cursor.execute(
                """
                DELETE FROM admin_profiles
                WHERE user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                DELETE FROM access_logs
                WHERE user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                DELETE FROM password_reset_tokens
                WHERE user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                DELETE FROM user_credentials
                WHERE user_id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                DELETE FROM users
                WHERE id IN (SELECT id FROM cleanup_users)
                """
            )
            cursor.execute(
                """
                CREATE TEMP TABLE cleanup_orphan_titles ON COMMIT DROP AS
                SELECT gt.title_code
                FROM game_titles gt
                WHERE gt.title_code ~ '^(mines_test_|mines_auth_|statement_|integration_|contract_|browser_)'
                  AND NOT EXISTS (SELECT 1 FROM platform_rounds pr WHERE pr.title_code = gt.title_code)
                  AND NOT EXISTS (SELECT 1 FROM mines_game_rounds mgr WHERE mgr.title_code = gt.title_code)
                  AND NOT EXISTS (SELECT 1 FROM game_access_sessions gas WHERE gas.title_code = gt.title_code)
                  AND NOT EXISTS (SELECT 1 FROM game_table_sessions gts WHERE gts.title_code = gt.title_code)
                  AND NOT EXISTS (SELECT 1 FROM demo_play_sessions dps WHERE dps.title_code = gt.title_code)
                  AND NOT EXISTS (SELECT 1 FROM mines_game_rounds mgr WHERE mgr.title_code = gt.title_code)
                  AND NOT EXISTS (SELECT 1 FROM title_assets ta WHERE ta.title_code = gt.title_code)
                """
            )
            cursor.execute(
                """
                DELETE FROM admin_audit_log
                WHERE resource_id IN (SELECT title_code FROM cleanup_orphan_titles)
                   OR resource_id IN (
                      SELECT 'casinoking:' || title_code FROM cleanup_orphan_titles
                   )
                """
            )
            cursor.execute(
                """
                DELETE FROM mines_title_configs
                WHERE title_code IN (SELECT title_code FROM cleanup_orphan_titles)
                """
            )
            cursor.execute(
                """
                DELETE FROM title_configs
                WHERE title_code IN (SELECT title_code FROM cleanup_orphan_titles)
                """
            )
            cursor.execute(
                """
                DELETE FROM site_titles
                WHERE title_code IN (SELECT title_code FROM cleanup_orphan_titles)
                """
            )
            cursor.execute(
                """
                DELETE FROM game_titles
                WHERE title_code IN (SELECT title_code FROM cleanup_orphan_titles)
                  AND NOT EXISTS (
                      SELECT 1 FROM game_access_sessions gas
                      WHERE gas.title_code = game_titles.title_code
                  )
                """
            )


def _cleanup_mines_variant_if_unreferenced(
    *,
    db_connection: DbConnection,
    title_code: str,
) -> None:
    with db_connection.cursor() as cursor:
        if _mines_variant_has_refs(cursor, title_code):
            return

        _delete_mines_variant(cursor, title_code)


def _mines_variant_has_refs(cursor: DbCursor, title_code: str) -> bool:
    cursor.execute(
        """
        SELECT
            EXISTS (SELECT 1 FROM platform_rounds WHERE title_code = %s)
            OR EXISTS (SELECT 1 FROM mines_game_rounds WHERE title_code = %s)
            OR EXISTS (SELECT 1 FROM game_access_sessions WHERE title_code = %s)
            OR EXISTS (SELECT 1 FROM game_table_sessions WHERE title_code = %s)
            OR EXISTS (SELECT 1 FROM demo_play_sessions WHERE title_code = %s)
            OR EXISTS (SELECT 1 FROM mines_game_rounds WHERE title_code = %s)
            OR EXISTS (SELECT 1 FROM title_assets WHERE title_code = %s)
            AS has_refs
        """,
        (
            title_code,
            title_code,
            title_code,
            title_code,
            title_code,
            title_code,
            title_code,
        ),
    )
    return cursor.fetchone()["has_refs"] is True


def _delete_mines_variant(cursor: DbCursor, title_code: str) -> None:
    cursor.execute(
        """
        DELETE FROM admin_audit_log
        WHERE resource_id = %s
           OR resource_id = %s
           OR resource_id LIKE %s
        """,
        (title_code, f"casinoking:{title_code}", f"{title_code}:%"),
    )
    cursor.execute("DELETE FROM mines_title_configs WHERE title_code = %s", (title_code,))
    cursor.execute("DELETE FROM title_configs WHERE title_code = %s", (title_code,))
    print(f"DELETED {cursor.rowcount} from title_configs for {title_code}", flush=True)
    cursor.execute("DELETE FROM site_titles WHERE title_code = %s", (title_code,))
    cursor.execute("DELETE FROM game_titles WHERE title_code = %s", (title_code,))


def _build_test_mines_backoffice_snapshot() -> dict[str, object]:
    runtime = get_runtime_config()
    published_grid_sizes = list(runtime["supported_grid_sizes"])
    published_mine_counts = {
        str(grid_size): _sample_test_mine_counts(runtime["supported_mine_counts"][str(grid_size)])
        for grid_size in published_grid_sizes
    }
    default_mine_counts = {
        str(grid_size): mine_counts[min(len(mine_counts) // 2, len(mine_counts) - 1)]
        for grid_size, mine_counts in (
            (grid_size, published_mine_counts[str(grid_size)]) for grid_size in published_grid_sizes
        )
    }
    return {
        "rules_sections": {
            "ways_to_win": "<p>Pick cells and avoid mines.</p>",
            "payout_display": "<p>The current payout is always shown.</p>",
            "settings_menu": "<p>Grid size and mines are configurable before the hand starts.</p>",
            "bet_collect": "<p>Bet starts the hand. Collect closes a winning hand.</p>",
            "balance_display": "<p>All CHIP values are displayed with two decimals.</p>",
            "general": "<p>Mines remains server-authoritative in every mode.</p>",
            "history": "<p>Completed hands are visible in player history.</p>",
        },
        "published_grid_sizes": published_grid_sizes,
        "published_mine_counts": published_mine_counts,
        "default_mine_counts": default_mine_counts,
        "ui_labels": {
            "demo": {
                "bet": "Bet",
                "bet_loading": "Betting...",
                "collect": "Collect",
                "collect_loading": "Collecting...",
                "home": "Home",
                "fullscreen": "Fullscreen",
                "game_info": "Game info",
            },
            "real": {
                "bet": "Bet",
                "bet_loading": "Betting...",
                "collect": "Collect",
                "collect_loading": "Collecting...",
                "home": "Home",
                "fullscreen": "Fullscreen",
                "game_info": "Game info",
            },
        },
        "board_assets": {
            "safe_icon_data_url": None,
            "mine_icon_data_url": None,
        },
    }


def _sample_test_mine_counts(values: list[int]) -> list[int]:
    if len(values) <= 5:
        return list(values)

    return list(values[:5])

# ── Marker auto-assignment (B2a) ────────────────────────────────────────────

# File-level overrides for contract/ and integration/ tests.
# Key = file name; Value = marker name.
_FILE_MARKERS: dict[str, str] = {
    # -- browser_smoke --
    "test_boxe_smoke.py": "browser_smoke",
    "test_boxe_lobby_launch.py": "browser_smoke",
    "test_frontend_smoke.py": "browser_smoke",
    "test_mines_embed_browser_smoke.py": "browser_smoke",
    "test_player_account_statement_browser_smoke.py": "browser_smoke",
    "test_site_v3_admin_builder_browser.py": "browser_smoke",
    "test_site_v3_player_handoff_browser.py": "browser_smoke",
    "test_site_v3_public_renderer_browser.py": "browser_smoke",
    # -- migration_schema --
    "test_apply_migrations.py": "migration_schema",
    "test_local_admin_bootstrap.py": "migration_schema",
    "test_platform_catalog_bootstrap.py": "migration_schema",
    "test_schema_drift_guard.py": "migration_schema",
    # -- visual (integration overlays) --
    "test_boxe_visual_regression.py": "visual",
    "test_mines_skin_visual_regression.py": "visual",
    # -- money_admin --
    "test_account_wallet_movements.py": "money_admin",
    "test_admin_audit_log.py": "money_admin",
    "test_admin_bonus_and_adjustments.py": "money_admin",
    "test_admin_financial_reports.py": "money_admin",
    "test_admin_force_close_boxe_hi_lo.py": "money_admin",
    "test_admin_force_close_sessions.py": "money_admin",
    "test_admin_ledger_report.py": "money_admin",
    "test_admin_ledger_transactions_access.py": "money_admin",
    "test_admin_rbac.py": "money_admin",
    "test_admin_session_drilldown.py": "money_admin",
    "test_admin_suspend.py": "money_admin",
    "test_financial_and_mines_flows.py": "money_admin",
    "test_reconciliation_integrity.py": "money_admin",
    "test_wallet_detail_access.py": "money_admin",
    "test_finance_replay_metadata_contract.py": "money_admin",
    "test_ledger_admin_access.py": "money_admin",
    "test_wallet_detail_contract.py": "money_admin",
    "test_mines_admin_session_snapshot_access.py": "money_admin",
    "test_session_cascade_close.py": "money_admin",
    # -- catalog --
    "test_admin_assets_contract.py": "catalog",
    "test_admin_theme_editor_load_gate.py": "catalog",
    "test_asset_registry.py": "catalog",
    "test_boxe_admin_assets.py": "catalog",
    "test_boxe_admin_config.py": "catalog",
    "test_game_library_publication.py": "catalog",
    "test_game_title_archive_restore.py": "catalog",
    "test_hi_lo_admin_config.py": "catalog",
    "test_platform_settings_inventory.py": "catalog",
    "test_player_lobby_game_card_asset.py": "catalog",
    "test_site_home_slots.py": "catalog",
    "test_site_v3_admin_builder_contract.py": "catalog",
    "test_title_code_propagation.py": "catalog",
    "test_title_configs_split.py": "catalog",
    "test_title_editor_agnostic.py": "catalog",
    "test_title_editor_agnostic_frontend.py": "catalog",
    "test_title_theme_contract.py": "catalog",
    "test_mines_backoffice_config.py": "catalog",
}



@pytest.fixture
def mines_db_helpers(db_helpers):
    class MinesDbHelpers:
        def get_mine_positions(self, session_id: str) -> list[int]:
            row = db_helpers.fetchone(
                """
                SELECT
                    mgr.mine_positions_json,
                    mgr.grid_size,
                    mgr.mine_count,
                    mgr.fairness_version,
                    mgr.nonce,
                    fsr.server_seed
                FROM mines_game_rounds mgr
                JOIN fairness_seed_rotations fsr
                  ON fsr.server_seed_hash = mgr.server_seed_hash
                WHERE mgr.id = %s
                """,
                (session_id,),
            )
            assert row is not None
            if row["mine_positions_json"] is not None:
                return list(row["mine_positions_json"])
            # SIC-08: open rounds do not persist mine positions; recompute
            # them from (server_seed, nonce, grid_size, mine_count,
            # fairness_version).
            mine_positions, _rng_material, _board_hash = generate_board(
                grid_size=row["grid_size"],
                mine_count=row["mine_count"],
                fairness_version=row["fairness_version"],
                server_seed=str(row["server_seed"]),
                nonce=row["nonce"],
            )
            return list(mine_positions)
    return MinesDbHelpers()



@pytest.fixture
def mines_auth_headers(client: httpx.Client, db_connection: DbConnection, _mines_cleanup_registrar):
    token_cache: dict[tuple[str, str, str, str], str] = {}
    created_title_codes: set[str] = set()
    implicit_title_code: str | None = None

    def _auth_headers(
        access_token: str,
        *,
        include_game_launch_token: bool = True,
        title_code: str | None = None,
        site_code: str = "casinoking",
        mode: str = "real",
    ) -> dict[str, str]:
        nonlocal implicit_title_code

        headers = {"Authorization": f"Bearer {access_token}"}
        if not include_game_launch_token:
            return headers

        resolved_title_code = title_code
        if resolved_title_code is None:
            if _decode_access_token_role(access_token) != "player":
                return headers
            if implicit_title_code is None:
                implicit_title_code = f"mines_auth_{uuid4().hex[:8]}"
                with db_connection.cursor() as cursor:
                    _upsert_published_mines_variant(
                        cursor=cursor,
                        title_code=implicit_title_code,
                        display_name="Mines Auth Header Variant",
                        site_code=site_code,
                        lobby_visibility="visible",
                        demo_enabled=True,
                        real_enabled=True,
                    )
                created_title_codes.add(implicit_title_code)
            resolved_title_code = implicit_title_code

        cache_key = (access_token, resolved_title_code, site_code, mode)
        # PERCHE' si fallisce subito: un collaudo che prosegue su un cammino degradato
        # senza gettone e' peggio di un collaudo rosso, perche' nasconde il difetto.
        if cache_key not in token_cache:
            issue_response = client.post(
                "/games/mines/launch-token",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "game_code": "mines",
                    "title_code": resolved_title_code,
                    "site_code": site_code,
                    "mode": mode,
                },
            )
            assert issue_response.status_code == 200, (
                "L'emissione del game launch token e' fallita: "
                f"status_code={issue_response.status_code}, corpo={issue_response.text}"
            )
            token_cache[cache_key] = issue_response.json()["data"]["game_launch_token"]

        game_launch_token = token_cache[cache_key]
        headers["X-Game-Launch-Token"] = game_launch_token
        return headers

    _auth_headers.implicit_title_code = lambda: implicit_title_code
    _auth_headers.created_title_codes = lambda: created_title_codes.copy()
    yield _auth_headers

    for title_code_to_cleanup in created_title_codes:
        _cleanup_mines_variant_if_unreferenced(
            db_connection=db_connection,
            title_code=title_code_to_cleanup,
        )




# NON autouse (4C-bis, 11/09/2026): pytest_plugins registra il plugin per TUTTA la
# sessione, quindi una fixture autouse qui si applicava a ogni collaudo della suite,
# anche ai file che non toccano Mines. La registrazione del callback di pulizia e'
# ora una dipendenza esplicita delle fixture che scrivono righe Mines
# (create_published_mines_variant, mines_auth_headers, track_mines_variant_cleanup).
@pytest.fixture
def _mines_cleanup_registrar(user_cleanup_coordinator):
    def _clean_mines_tables(cursor):
        cursor.execute("DELETE FROM mines_title_configs WHERE title_code IN (SELECT code FROM cleanup_titles)")
        
        cursor.execute(
            """
            CREATE TEMP TABLE IF NOT EXISTS targeted_mines_round_ids ON COMMIT DROP AS
            SELECT id FROM mines_game_rounds WHERE title_code IN (SELECT code FROM cleanup_titles)
            OR user_id IN (SELECT id FROM cleanup_users)
            OR user_id IN (SELECT id FROM cleanup_anon)
            OR platform_round_id IN (SELECT id FROM targeted_platform_rounds)
            OR demo_session_id IN (SELECT id FROM targeted_demo_session_ids)
            """
        )
        cursor.execute("SELECT to_regclass('public.game_idempotency_keys') AS table_name")
        if cursor.fetchone()["table_name"] is not None:
            cursor.execute(
                """
                DELETE FROM game_idempotency_keys
                WHERE game_code = 'mines'
                  AND (round_id IN (SELECT id FROM targeted_mines_round_ids)
                    OR player_id IN (SELECT id FROM cleanup_users)
                    OR player_id IN (SELECT id FROM cleanup_anon))
                """
            )
        cursor.execute("DELETE FROM mines_game_rounds WHERE id IN (SELECT id FROM targeted_mines_round_ids)")

    user_cleanup_coordinator.register_domain_callback(_clean_mines_tables)


# NON autouse (4C-bis, 11/09/2026): la variante "mines" di default viene creata solo
# per i collaudi che la chiedono per nome. Prima la pagava tutta la suite.
@pytest.fixture
def default_mines_variant(create_published_mines_variant, preserve_mines_backoffice_config):
    # Crea la variante pubblicata di default "mines" per i collaudi che se la
    # aspettano (risoluzione lobby/sito sul titolo "mines").
    create_published_mines_variant(title_code="mines")
