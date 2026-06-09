from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


FieldType = Literal[
    "asset_ref",
    "boolean",
    "html",
    "nav_items",
    "string",
    "string_list",
    "title_code",
    "title_code_list",
    "url",
]


@dataclass(frozen=True)
class ModuleField:
    key: str
    field_type: FieldType
    required: bool = False
    max_length: int | None = None
    max_items: int | None = None


@dataclass(frozen=True)
class ModuleManifest:
    module_code: str
    schema_version: int
    slot_keys: tuple[str, ...]
    fields: tuple[ModuleField, ...]
    description: str


MVP_MODULE_CODES = (
    "global_header",
    "hero_banner",
    "game_grid",
    "game_grid_4x",
    "featured_game",
    "promo_band",
    "system_registration_form",
    "rich_text_safe",
    "global_footer",
)


MODULE_MANIFESTS: dict[str, ModuleManifest] = {
    "global_header": ModuleManifest(
        module_code="global_header",
        schema_version=1,
        slot_keys=("header",),
        description="Global brand header.",
        fields=(
            ModuleField("brand_label", "string", required=True, max_length=80),
            ModuleField("login_label", "string", required=False, max_length=40),
            ModuleField("account_label", "string", required=False, max_length=40),
        ),
    ),
    "hero_banner": ModuleManifest(
        module_code="hero_banner",
        schema_version=1,
        slot_keys=("main", "hero"),
        description="Primary homepage hero.",
        fields=(
            ModuleField("headline", "string", required=True, max_length=120),
            ModuleField("body", "string", required=False, max_length=500),
            ModuleField("cta_label", "string", required=False, max_length=60),
            ModuleField("cta_title_code", "title_code", required=False),
            ModuleField("media_asset_ref", "asset_ref", required=False),
            ModuleField("show_copy", "boolean", required=False),
            ModuleField("show_cta", "boolean", required=False),
        ),
    ),
    "game_grid": ModuleManifest(
        module_code="game_grid",
        schema_version=1,
        slot_keys=("main", "games"),
        description="Grid of launchable game titles.",
        fields=(
            ModuleField("heading", "string", required=True, max_length=100),
            ModuleField("title_codes", "title_code_list", required=True, max_items=24),
        ),
    ),
    "game_grid_4x": ModuleManifest(
        module_code="game_grid_4x",
        schema_version=1,
        slot_keys=("main", "games"),
        description="Large four-column grid of launchable game titles.",
        fields=(
            ModuleField("heading", "string", required=True, max_length=100),
            ModuleField("title_codes", "title_code_list", required=True, max_items=24),
        ),
    ),
    "featured_game": ModuleManifest(
        module_code="featured_game",
        schema_version=1,
        slot_keys=("main", "feature"),
        description="One highlighted launchable game.",
        fields=(
            ModuleField("title_code", "title_code", required=True),
            ModuleField("headline", "string", required=False, max_length=120),
            ModuleField("body", "string", required=False, max_length=500),
            ModuleField("cta_label", "string", required=False, max_length=60),
        ),
    ),
    "promo_band": ModuleManifest(
        module_code="promo_band",
        schema_version=1,
        slot_keys=("main", "promo"),
        description="Editorial promotional strip.",
        fields=(
            ModuleField("headline", "string", required=True, max_length=120),
            ModuleField("body", "string", required=False, max_length=500),
            ModuleField("cta_label", "string", required=False, max_length=60),
            ModuleField("cta_url", "string", required=False, max_length=300),
        ),
    ),
    "system_registration_form": ModuleManifest(
        module_code="system_registration_form",
        schema_version=1,
        slot_keys=("main", "system"),
        description="System-owned player registration form configuration.",
        fields=(
            ModuleField("eyebrow", "string", required=False, max_length=60),
            ModuleField("headline", "string", required=True, max_length=120),
            ModuleField("body", "string", required=False, max_length=500),
            ModuleField("first_name_label", "string", required=False, max_length=80),
            ModuleField("last_name_label", "string", required=False, max_length=80),
            ModuleField("fiscal_code_label", "string", required=False, max_length=80),
            ModuleField("phone_number_label", "string", required=False, max_length=80),
            ModuleField("email_label", "string", required=False, max_length=80),
            ModuleField("password_label", "string", required=False, max_length=80),
            ModuleField("access_code_label", "string", required=False, max_length=80),
            ModuleField("document_front_label", "string", required=False, max_length=80),
            ModuleField("document_back_label", "string", required=False, max_length=80),
            ModuleField("continue_label", "string", required=False, max_length=80),
            ModuleField("back_label", "string", required=False, max_length=80),
            ModuleField("submit_label", "string", required=False, max_length=80),
            ModuleField("busy_label", "string", required=False, max_length=80),
            ModuleField("login_label", "string", required=False, max_length=80),
            ModuleField("lobby_label", "string", required=False, max_length=80),
            ModuleField("checking_message", "string", required=False, max_length=200),
            ModuleField("authenticated_message", "string", required=False, max_length=200),
            ModuleField("authenticated_status", "string", required=False, max_length=200),
            ModuleField("document_upload_note", "string", required=False, max_length=800),
            ModuleField("success_message", "string", required=False, max_length=300),
            ModuleField("legal_note_html", "html", required=False, max_length=4000),
            ModuleField("post_register_path", "url", required=False, max_length=300),
            ModuleField("show_first_name", "boolean", required=False),
            ModuleField("show_last_name", "boolean", required=False),
            ModuleField("show_fiscal_code", "boolean", required=False),
            ModuleField("show_phone_number", "boolean", required=False),
            ModuleField("require_document_images", "boolean", required=False),
        ),
    ),
    "rich_text_safe": ModuleManifest(
        module_code="rich_text_safe",
        schema_version=1,
        slot_keys=("main", "content", "footer"),
        description="Allowlisted editorial HTML.",
        fields=(
            ModuleField("html", "html", required=True, max_length=12000),
        ),
    ),
    "global_footer": ModuleManifest(
        module_code="global_footer",
        schema_version=1,
        slot_keys=("footer",),
        description="Global footer text and links.",
        fields=(
            ModuleField("legal_text", "string", required=True, max_length=1000),
            ModuleField("links", "nav_items", required=False, max_items=12),
        ),
    ),
}


def get_module_manifest(module_code: str) -> ModuleManifest | None:
    return MODULE_MANIFESTS.get(module_code)


def list_module_manifests() -> list[ModuleManifest]:
    return [MODULE_MANIFESTS[module_code] for module_code in MVP_MODULE_CODES]
