from __future__ import annotations

from html import escape
from html.parser import HTMLParser
import json
from urllib.parse import urlparse

from app.db.connection import db_connection
from app.modules.games.mines.runtime import get_runtime_config

GAME_CODE = "mines"

RULE_SECTION_KEYS = (
    "ways_to_win",
    "payout_display",
    "settings_menu",
    "bet_collect",
    "balance_display",
    "general",
    "history",
)

UI_LABEL_KEYS = (
    "bet",
    "bet_loading",
    "collect",
    "collect_loading",
    "home",
    "fullscreen",
    "game_info",
)


class MinesBackofficeValidationError(Exception):
    pass


def get_public_backoffice_config() -> dict[str, object]:
    return _load_effective_config()


def get_admin_backoffice_config() -> dict[str, object]:
    return _load_effective_config()


def update_admin_backoffice_config(
    *,
    admin_user_id: str,
    rules_sections: dict[str, str],
    published_grid_sizes: list[int],
    published_mine_counts: dict[str, list[int]],
    default_mine_counts: dict[str, int],
    ui_labels: dict[str, dict[str, str]],
) -> dict[str, object]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            _ensure_admin_user_exists(cursor=cursor, admin_user_id=admin_user_id)

            normalized_rules = _normalize_rules_sections(rules_sections)
            normalized_grids, normalized_mines, normalized_defaults = (
                _normalize_published_configuration(
                    published_grid_sizes=published_grid_sizes,
                    published_mine_counts=published_mine_counts,
                    default_mine_counts=default_mine_counts,
                )
            )
            normalized_labels = _normalize_ui_labels(ui_labels)

            cursor.execute(
                """
                INSERT INTO mines_backoffice_config (
                    game_code,
                    rules_sections_json,
                    published_grid_sizes_json,
                    published_mine_counts_json,
                    default_mine_counts_json,
                    ui_labels_json,
                    updated_by_admin_user_id
                )
                VALUES (%s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s)
                ON CONFLICT (game_code)
                DO UPDATE
                SET rules_sections_json = EXCLUDED.rules_sections_json,
                    published_grid_sizes_json = EXCLUDED.published_grid_sizes_json,
                    published_mine_counts_json = EXCLUDED.published_mine_counts_json,
                    default_mine_counts_json = EXCLUDED.default_mine_counts_json,
                    ui_labels_json = EXCLUDED.ui_labels_json,
                    updated_by_admin_user_id = EXCLUDED.updated_by_admin_user_id,
                    updated_at = NOW()
                RETURNING updated_at
                """,
                (
                    GAME_CODE,
                    json.dumps(normalized_rules),
                    json.dumps(normalized_grids),
                    json.dumps(normalized_mines),
                    json.dumps(normalized_defaults),
                    json.dumps(normalized_labels),
                    admin_user_id,
                ),
            )
            row = cursor.fetchone()

    payload = _build_effective_payload(
        stored_row={
            "rules_sections_json": normalized_rules,
            "published_grid_sizes_json": normalized_grids,
            "published_mine_counts_json": normalized_mines,
            "default_mine_counts_json": normalized_defaults,
            "ui_labels_json": normalized_labels,
            "updated_by_admin_user_id": admin_user_id,
            "updated_at": row["updated_at"],
        }
    )
    return payload


def is_published_configuration_supported(*, grid_size: int, mine_count: int) -> bool:
    config = _load_effective_config()
    published_grid_sizes = config["published_grid_sizes"]
    published_mine_counts = config["published_mine_counts"]
    return (
        grid_size in published_grid_sizes
        and mine_count in published_mine_counts.get(str(grid_size), [])
    )


def _load_effective_config() -> dict[str, object]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    game_code,
                    rules_sections_json,
                    published_grid_sizes_json,
                    published_mine_counts_json,
                    default_mine_counts_json,
                    ui_labels_json,
                    updated_by_admin_user_id,
                    updated_at
                FROM mines_backoffice_config
                WHERE game_code = %s
                """,
                (GAME_CODE,),
            )
            row = cursor.fetchone()

    return _build_effective_payload(stored_row=row)


def _build_effective_payload(*, stored_row: dict[str, object] | None) -> dict[str, object]:
    defaults = _build_default_config()
    if stored_row is None:
        return defaults

    return {
        "game_code": GAME_CODE,
        "rules_sections": _normalize_rules_sections(
            stored_row["rules_sections_json"] or defaults["rules_sections"]
        ),
        "published_grid_sizes": _normalize_grid_list(
            stored_row["published_grid_sizes_json"] or defaults["published_grid_sizes"]
        ),
        "published_mine_counts": _normalize_mine_map(
            stored_row["published_mine_counts_json"] or defaults["published_mine_counts"]
        ),
        "default_mine_counts": _normalize_default_map(
            stored_row["default_mine_counts_json"] or defaults["default_mine_counts"]
        ),
        "ui_labels": _normalize_ui_labels(
            stored_row["ui_labels_json"] or defaults["ui_labels"]
        ),
        "updated_by_admin_user_id": (
            str(stored_row["updated_by_admin_user_id"])
            if stored_row["updated_by_admin_user_id"]
            else None
        ),
        "updated_at": (
            stored_row["updated_at"].isoformat()
            if stored_row["updated_at"] is not None
            else None
        ),
    }


def _build_default_config() -> dict[str, object]:
    runtime = get_runtime_config()
    published_grid_sizes = list(runtime["supported_grid_sizes"])
    published_mine_counts = {
        str(grid_size): _sample_mine_counts(runtime["supported_mine_counts"][str(grid_size)])
        for grid_size in published_grid_sizes
    }
    default_mine_counts = {
        grid_key: mine_counts[len(mine_counts) // 2]
        for grid_key, mine_counts in published_mine_counts.items()
    }
    return {
        "game_code": GAME_CODE,
        "rules_sections": {
            "ways_to_win": (
                "<p>Pick cells from the grid. Every diamond increases your potential win. "
                "If you reveal a mine, the hand ends immediately in loss.</p>"
            ),
            "payout_display": (
                "<p>The ladder under the MINES title shows the next useful click values. "
                "The highlighted value is the payout you can collect right now.</p>"
            ),
            "settings_menu": (
                "<p>The preview updates immediately when grid size or mines change. "
                "During an active hand the configuration is locked.</p>"
            ),
            "bet_collect": (
                "<p>Bet always starts a new hand. Collect is available only after at least "
                "one safe reveal.</p>"
            ),
            "balance_display": (
                "<p>Balance, bet and win are shown in CHIP with two decimals. "
                "On loss all mines become visible on the current board.</p>"
            ),
            "general": (
                "<p>Mines is server-authoritative. The frontend never decides board, outcome "
                "or payout.</p>"
            ),
            "history": (
                "<p>Completed hands are visible in account history for authenticated players. "
                "The game frame stays focused on gameplay.</p>"
            ),
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
        "updated_by_admin_user_id": None,
        "updated_at": None,
    }


def _sample_mine_counts(values: list[int]) -> list[int]:
    if len(values) <= 5:
        return list(values)

    last_index = len(values) - 1
    sampled_indices = {round((index * last_index) / 4) for index in range(5)}
    return [values[index] for index in sorted(sampled_indices)]


def _normalize_rules_sections(raw_sections: object) -> dict[str, str]:
    if not isinstance(raw_sections, dict):
        raise MinesBackofficeValidationError("rules_sections must be an object")

    normalized: dict[str, str] = {}
    for key in RULE_SECTION_KEYS:
        value = raw_sections.get(key)
        if not isinstance(value, str) or not value.strip():
            raise MinesBackofficeValidationError(f"rules_sections.{key} must be a non-empty string")
        normalized[key] = _sanitize_html(value)
    return normalized


def _normalize_published_configuration(
    *,
    published_grid_sizes: list[int],
    published_mine_counts: dict[str, list[int]],
    default_mine_counts: dict[str, int],
) -> tuple[list[int], dict[str, list[int]], dict[str, int]]:
    runtime = get_runtime_config()
    runtime_grid_sizes = set(runtime["supported_grid_sizes"])
    runtime_mines = runtime["supported_mine_counts"]

    normalized_grid_sizes = _normalize_grid_list(published_grid_sizes)
    if not normalized_grid_sizes:
        raise MinesBackofficeValidationError("At least one published grid size is required")

    if not set(normalized_grid_sizes).issubset(runtime_grid_sizes):
        raise MinesBackofficeValidationError("Published grid sizes must be a subset of the official runtime")

    normalized_mine_counts = _normalize_mine_map(published_mine_counts)
    normalized_defaults = _normalize_default_map(default_mine_counts)

    for grid_size in normalized_grid_sizes:
        grid_key = str(grid_size)
        supported_mine_counts = set(runtime_mines[grid_key])
        if grid_key not in normalized_mine_counts:
            raise MinesBackofficeValidationError(f"Missing published mine counts for grid {grid_key}")

        mine_counts = normalized_mine_counts[grid_key]
        if len(mine_counts) == 0:
            raise MinesBackofficeValidationError(f"Grid {grid_key} must publish at least one mine count")
        if len(mine_counts) > 5:
            raise MinesBackofficeValidationError(f"Grid {grid_key} can publish at most 5 mine counts")
        if not set(mine_counts).issubset(supported_mine_counts):
            raise MinesBackofficeValidationError(
                f"Grid {grid_key} contains mine counts outside the official runtime"
            )

        default_mine_count = normalized_defaults.get(grid_key)
        if default_mine_count is None:
            raise MinesBackofficeValidationError(f"Missing default mine count for grid {grid_key}")
        if default_mine_count not in mine_counts:
            raise MinesBackofficeValidationError(
                f"Default mine count for grid {grid_key} must belong to the published mine counts"
            )

    for grid_key in normalized_mine_counts:
        if int(grid_key) not in normalized_grid_sizes:
            raise MinesBackofficeValidationError(
                f"Grid {grid_key} has mine counts configured but is not in published_grid_sizes"
            )

    for grid_key in normalized_defaults:
        if int(grid_key) not in normalized_grid_sizes:
            raise MinesBackofficeValidationError(
                f"Grid {grid_key} has a default mine count but is not in published_grid_sizes"
            )

    return normalized_grid_sizes, normalized_mine_counts, normalized_defaults


def _normalize_ui_labels(raw_labels: object) -> dict[str, dict[str, str]]:
    if not isinstance(raw_labels, dict):
        raise MinesBackofficeValidationError("ui_labels must be an object")

    normalized: dict[str, dict[str, str]] = {}
    for mode in ("demo", "real"):
        mode_payload = raw_labels.get(mode)
        if not isinstance(mode_payload, dict):
            raise MinesBackofficeValidationError(f"ui_labels.{mode} must be an object")
        normalized[mode] = {}
        for key in UI_LABEL_KEYS:
            value = mode_payload.get(key)
            if not isinstance(value, str) or not value.strip():
                raise MinesBackofficeValidationError(
                    f"ui_labels.{mode}.{key} must be a non-empty string"
                )
            normalized[mode][key] = value.strip()
    return normalized


def _normalize_grid_list(raw_value: object) -> list[int]:
    if not isinstance(raw_value, list):
        raise MinesBackofficeValidationError("published_grid_sizes must be a list")
    normalized_values = sorted(
        {
            int(value)
            for value in raw_value
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit())
        }
    )
    if len(normalized_values) != len(raw_value):
        raise MinesBackofficeValidationError("published_grid_sizes must contain only unique integers")
    return normalized_values


def _normalize_mine_map(raw_value: object) -> dict[str, list[int]]:
    if not isinstance(raw_value, dict):
        raise MinesBackofficeValidationError("published_mine_counts must be an object")
    normalized: dict[str, list[int]] = {}
    for raw_grid_key, raw_counts in raw_value.items():
        if not isinstance(raw_grid_key, str) or not raw_grid_key.isdigit():
            raise MinesBackofficeValidationError("published_mine_counts keys must be numeric strings")
        if not isinstance(raw_counts, list):
            raise MinesBackofficeValidationError(
                f"published_mine_counts.{raw_grid_key} must be a list"
            )
        values = sorted(
            {
                int(value)
                for value in raw_counts
                if isinstance(value, int) or (isinstance(value, str) and value.isdigit())
            }
        )
        if len(values) != len(raw_counts):
            raise MinesBackofficeValidationError(
                f"published_mine_counts.{raw_grid_key} must contain only unique integers"
            )
        normalized[raw_grid_key] = values
    return normalized


def _normalize_default_map(raw_value: object) -> dict[str, int]:
    if not isinstance(raw_value, dict):
        raise MinesBackofficeValidationError("default_mine_counts must be an object")
    normalized: dict[str, int] = {}
    for raw_grid_key, raw_default in raw_value.items():
        if not isinstance(raw_grid_key, str) or not raw_grid_key.isdigit():
            raise MinesBackofficeValidationError("default_mine_counts keys must be numeric strings")
        if not isinstance(raw_default, int) and not (
            isinstance(raw_default, str) and raw_default.isdigit()
        ):
            raise MinesBackofficeValidationError(
                f"default_mine_counts.{raw_grid_key} must be an integer"
            )
        normalized[raw_grid_key] = int(raw_default)
    return normalized


def _ensure_admin_user_exists(*, cursor, admin_user_id: str) -> None:
    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE id = %s
          AND role = 'admin'
        """,
        (admin_user_id,),
    )
    if cursor.fetchone() is None:
        raise MinesBackofficeValidationError("Admin user not found")


class _SafeHtmlSanitizer(HTMLParser):
    allowed_tags = {
        "p",
        "br",
        "strong",
        "em",
        "ul",
        "ol",
        "li",
        "code",
        "a",
    }
    self_closing_tags = {"br"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.open_tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.allowed_tags:
            return
        if tag == "a":
            href = None
            for key, value in attrs:
                if key == "href" and value and _is_safe_href(value):
                    href = value
                    break
            if href:
                self.parts.append(f'<a href="{escape(href, quote=True)}" rel="noopener noreferrer">')
                self.open_tags.append(tag)
            return
        self.parts.append(f"<{tag}>")
        if tag not in self.self_closing_tags:
            self.open_tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag not in self.allowed_tags or tag in self.self_closing_tags:
            return
        if tag in self.open_tags:
            while self.open_tags:
                current = self.open_tags.pop()
                self.parts.append(f"</{current}>")
                if current == tag:
                    break

    def handle_data(self, data: str) -> None:
        self.parts.append(escape(data))

    def get_html(self) -> str:
        while self.open_tags:
            self.parts.append(f"</{self.open_tags.pop()}>")
        return "".join(self.parts)


def _sanitize_html(value: str) -> str:
    sanitizer = _SafeHtmlSanitizer()
    sanitizer.feed(value.strip())
    sanitizer.close()
    sanitized = sanitizer.get_html().strip()
    if not sanitized:
        raise MinesBackofficeValidationError("HTML content cannot be empty after sanitization")
    return sanitized


def _is_safe_href(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "mailto"} and not value.lower().startswith("javascript:")
