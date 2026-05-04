from __future__ import annotations

import json


GENERIC_DRAFT_FIELDS = (
    "draft_rules_sections_json",
    "draft_ui_labels_json",
)

GENERIC_PUBLISHED_FIELDS = (
    "rules_sections_json",
    "ui_labels_json",
)


def load_generic_row(*, cursor, title_code: str) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
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
            draft_updated_at,
            created_at,
            updated_at
        FROM title_configs
        WHERE title_code = %s
        """,
        (title_code,),
    )
    return cursor.fetchone()


def upsert_generic_draft(
    *,
    cursor,
    title_code: str,
    admin_user_id: str,
    published_rules_sections: dict[str, object],
    published_ui_labels: dict[str, object],
    draft_rules_sections: dict[str, object],
    draft_ui_labels: dict[str, object],
) -> None:
    cursor.execute(
        """
        INSERT INTO title_configs (
            title_code,
            rules_sections_json,
            ui_labels_json,
            draft_rules_sections_json,
            draft_ui_labels_json,
            draft_updated_by_admin_user_id,
            draft_updated_at
        )
        VALUES (
            %s,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s,
            NOW()
        )
        ON CONFLICT (title_code)
        DO UPDATE
        SET draft_rules_sections_json = EXCLUDED.draft_rules_sections_json,
            draft_ui_labels_json = EXCLUDED.draft_ui_labels_json,
            draft_updated_by_admin_user_id = EXCLUDED.draft_updated_by_admin_user_id,
            draft_updated_at = NOW()
        """,
        (
            title_code,
            json.dumps(published_rules_sections),
            json.dumps(published_ui_labels),
            json.dumps(draft_rules_sections),
            json.dumps(draft_ui_labels),
            admin_user_id,
        ),
    )


def upsert_generic_published(
    *,
    cursor,
    title_code: str,
    admin_user_id: str,
    rules_sections: dict[str, object],
    ui_labels: dict[str, object],
) -> None:
    cursor.execute(
        """
        INSERT INTO title_configs (
            title_code,
            rules_sections_json,
            ui_labels_json,
            draft_rules_sections_json,
            draft_ui_labels_json,
            draft_updated_by_admin_user_id,
            draft_updated_at,
            updated_by_admin_user_id,
            updated_at,
            published_at
        )
        VALUES (
            %s,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s,
            NOW(),
            %s,
            NOW(),
            NOW()
        )
        ON CONFLICT (title_code)
        DO UPDATE
        SET rules_sections_json = EXCLUDED.rules_sections_json,
            ui_labels_json = EXCLUDED.ui_labels_json,
            draft_rules_sections_json = EXCLUDED.rules_sections_json,
            draft_ui_labels_json = EXCLUDED.ui_labels_json,
            draft_updated_by_admin_user_id = EXCLUDED.updated_by_admin_user_id,
            draft_updated_at = NOW(),
            updated_by_admin_user_id = EXCLUDED.updated_by_admin_user_id,
            updated_at = NOW(),
            published_at = NOW()
        """,
        (
            title_code,
            json.dumps(rules_sections),
            json.dumps(ui_labels),
            json.dumps(rules_sections),
            json.dumps(ui_labels),
            admin_user_id,
            admin_user_id,
        ),
    )
