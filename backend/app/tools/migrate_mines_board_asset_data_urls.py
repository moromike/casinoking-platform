from __future__ import annotations

import base64
from dataclasses import dataclass

from psycopg.types.json import Jsonb

from app.db.connection import db_connection
from app.modules.platform.asset_registry.service import AssetUpload, upload_title_asset
from app.modules.platform.asset_registry.storage import AssetStorage


DATA_URL_PREFIXES = {
    "data:image/png;base64,": "image/png",
    "data:image/svg+xml;base64,": "image/svg+xml",
}

FIELD_TO_ASSET_KIND = {
    "safe_icon_data_url": "symbol_safe",
    "mine_icon_data_url": "symbol_mine",
}

CONFIG_COLUMNS = (
    "published_board_assets_json",
    "draft_board_assets_json",
)


@dataclass(frozen=True)
class MigratedAsset:
    title_code: str
    config_column: str
    board_asset_field: str
    public_url: str


def migrate_mines_board_asset_data_urls(
    *,
    storage: AssetStorage | None = None,
) -> list[MigratedAsset]:
    migrated: list[MigratedAsset] = []

    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    title_code,
                    published_board_assets_json,
                    draft_board_assets_json
                FROM mines_title_configs
                ORDER BY title_code
                """
            )
            rows = cursor.fetchall()

            for row in rows:
                title_code = str(row["title_code"])
                updates: dict[str, dict[str, object]] = {}

                for config_column in CONFIG_COLUMNS:
                    board_assets = row[config_column]
                    if not isinstance(board_assets, dict):
                        continue

                    next_board_assets = dict(board_assets)
                    changed = False
                    for field_name, asset_kind in FIELD_TO_ASSET_KIND.items():
                        value = next_board_assets.get(field_name)
                        parsed = _parse_asset_data_url(value)
                        if parsed is None:
                            continue

                        mime, content = parsed
                        asset = upload_title_asset(
                            AssetUpload(
                                title_code=title_code,
                                asset_kind=asset_kind,
                                mime=mime,
                                content=content,
                                uploaded_by_admin_user_id=None,
                            ),
                            storage=storage,
                        )
                        next_board_assets[field_name] = asset["public_url"]
                        migrated.append(
                            MigratedAsset(
                                title_code=title_code,
                                config_column=config_column,
                                board_asset_field=field_name,
                                public_url=str(asset["public_url"]),
                            )
                        )
                        changed = True

                    if changed:
                        updates[config_column] = next_board_assets

                if updates:
                    set_fragments = [
                        f"{column_name} = %s::jsonb"
                        for column_name in updates
                    ]
                    params = [
                        Jsonb(value)
                        for value in updates.values()
                    ]
                    params.append(title_code)
                    cursor.execute(
                        f"""
                        UPDATE mines_title_configs
                        SET {", ".join(set_fragments)},
                            updated_at = NOW()
                        WHERE title_code = %s
                        """,
                        params,
                    )

    return migrated


def _parse_asset_data_url(value: object) -> tuple[str, bytes] | None:
    if not isinstance(value, str):
        return None
    for prefix, mime in DATA_URL_PREFIXES.items():
        if not value.startswith(prefix):
            continue
        encoded = value.removeprefix(prefix)
        try:
            return mime, base64.b64decode(encoded, validate=True)
        except ValueError:
            return None
    return None


if __name__ == "__main__":
    migrated_assets = migrate_mines_board_asset_data_urls()
    print(f"Migrated Mines board assets: {len(migrated_assets)}")
