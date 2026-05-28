import pathlib
import re

from app.modules.platform.site_v3.manifests import list_module_manifests


ROOT = pathlib.Path(__file__).resolve().parents[2]
FRONTEND_DESCRIPTOR = (
    ROOT
    / "frontend"
    / "app"
    / "ui"
    / "site-v3-admin"
    / "site-v3-admin-descriptors.ts"
)
ADMIN_UI_DIR = ROOT / "frontend" / "app" / "ui" / "site-v3-admin"
ADMIN_ROUTE = ROOT / "frontend" / "app" / "admin" / "site-v3" / "page.tsx"
CONSOLE = ROOT / "frontend" / "app" / "ui" / "casinoking-console.tsx"


def read_admin_ui_source() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(ADMIN_UI_DIR.rglob("*.ts*"))
    )


def test_site_v3_admin_module_descriptors_match_backend_manifest():
    source = FRONTEND_DESCRIPTOR.read_text(encoding="utf-8")
    frontend_codes = set(re.findall(r'moduleCode:\s*"([^"]+)"', source))
    backend_codes = {manifest.module_code for manifest in list_module_manifests()}

    assert frontend_codes == backend_codes

    for manifest in list_module_manifests():
        assert f'{manifest.module_code}:' in source
        assert f'moduleCode: "{manifest.module_code}"' in source
        assert f"schemaVersion: {manifest.schema_version}" in source
        assert "humanHint:" in source


def test_site_v3_admin_module_picker_groups_modules_for_human_composition():
    descriptor_source = FRONTEND_DESCRIPTOR.read_text(encoding="utf-8")
    admin_source = read_admin_ui_source()

    for category in ["structure", "hero", "catalog", "promo", "text_legal"]:
        assert f'key: "{category}"' in descriptor_source

    assert "SITE_V3_MODULE_CATEGORIES" in admin_source
    assert "site-v3-library-category-row" in admin_source
    assert "site-v3-inline-module-select-row" in admin_source
    assert "Add selected module" in admin_source
    assert "site-v3-inline-module-option" not in admin_source
    assert "Add module</option>" not in admin_source


def test_site_v3_admin_complex_fields_are_human_editors():
    admin_source = read_admin_ui_source()

    assert "site-v3-nav-editor" in admin_source
    assert "Add navigation item" in admin_source
    assert "linesToNavItems" not in admin_source
    assert "Search available games" in admin_source
    assert "Game Grid catalog" in admin_source
    assert "Available game library" in admin_source
    assert "Clear selected games" in admin_source
    assert "No games match this search" in admin_source


def test_site_v3_admin_module_creation_stays_in_composition():
    builder_source = (
        ROOT
        / "frontend"
        / "app"
        / "ui"
        / "site-v3-admin"
        / "site-v3-admin-builder.tsx"
    ).read_text(encoding="utf-8")

    composition_add_source = builder_source.split("function addModuleFromComposition", maxsplit=1)[1].split("return (", maxsplit=1)[0]
    library_add_source = builder_source.split("function addModuleAndShowComposition", maxsplit=1)[1].split("function openModuleInstance", maxsplit=1)[0]
    duplicate_source = builder_source.split("function duplicateModule", maxsplit=1)[1].split("function moveModule", maxsplit=1)[0]

    assert 'setCurrentView({ kind: "composition" })' in composition_add_source
    assert 'kind: "moduleInstance"' not in composition_add_source
    assert 'setCurrentView({ kind: "composition" })' in library_add_source
    assert 'kind: "moduleInstance"' not in library_add_source
    assert 'setCurrentView({ kind: "composition" })' in duplicate_source
    admin_source = read_admin_ui_source()
    assert "Add module to page" in admin_source
    assert "Mount on current page" in admin_source
    assert "opened for editing" not in builder_source


def test_site_v3_admin_workflow_destinations_are_explicit():
    builder_source = (
        ROOT
        / "frontend"
        / "app"
        / "ui"
        / "site-v3-admin"
        / "site-v3-admin-builder.tsx"
    ).read_text(encoding="utf-8")

    validate_source = builder_source.split("async function handleValidate", maxsplit=1)[1].split("async function handlePublish", maxsplit=1)[0]
    archive_source = builder_source.split("async function handleArchive", maxsplit=1)[1].split("const isBusy", maxsplit=1)[0]
    save_source = builder_source.split("async function handleSaveDraft", maxsplit=1)[1].split("async function handleValidate", maxsplit=1)[0]
    publish_source = builder_source.split("async function handlePublish", maxsplit=1)[1].split("async function handleArchive", maxsplit=1)[0]

    assert 'setCurrentView({ kind: "validation" })' in validate_source
    assert 'setCurrentView({ kind: "pages" })' in archive_source
    assert "loadPages(null)" in archive_source
    assert 'setCurrentView({ kind: "composition" })' in save_source
    assert 'setCurrentView({ kind: "composition" })' in publish_source


def test_site_v3_admin_ia_contract_keeps_mounted_instances_out_of_left_nav():
    nav_source = (ADMIN_UI_DIR / "screens" / "site-v3-admin-nav.tsx").read_text(encoding="utf-8")
    helper_source = (ADMIN_UI_DIR / "site-v3-admin-helpers.ts").read_text(encoding="utf-8")
    composition_source = (ADMIN_UI_DIR / "screens" / "site-v3-composition-screen.tsx").read_text(encoding="utf-8")
    admin_source = read_admin_ui_source()

    assert "Mounted modules" not in nav_source
    assert "modules.map" not in nav_source
    assert 'kind: "moduleInstance"' not in nav_source
    assert "SITE_V3_MODULE_DESCRIPTORS[module.module_code]" not in nav_source
    assert "template" not in admin_source.lower()
    assert "SiteV3NewModuleWizardScreen" not in admin_source
    assert 'kind: "moduleWizard"' not in helper_source
    assert "Add module to page" in composition_source
    assert "site-v3-module-order-index" in composition_source
    assert "previewHeadline(module)" in composition_source


def test_site_v3_admin_asset_picker_consumes_existing_site_assets():
    api_source = (
        ROOT
        / "frontend"
        / "app"
        / "ui"
        / "site-v3-admin"
        / "site-v3-admin-api.ts"
    ).read_text(encoding="utf-8")
    admin_source = read_admin_ui_source()

    assert "listSiteV3Assets" in api_source
    assert "/admin/sites/" in api_source
    assert "asset_kind=homepage_banner" in api_source or "homepage_banner" in api_source
    assert "site-v3-asset-picker" in admin_source
    assert "aria-pressed={selected}" in admin_source
    assert "asset_id: asset.id" in admin_source
    assert "public_url: asset.public_url" in admin_source
    assert "Manual public URL" in admin_source
    assert "Asset ID" not in admin_source
    assert "Asset kind" not in admin_source


def test_site_v3_admin_route_mounts_existing_console_without_new_login():
    route_source = ADMIN_ROUTE.read_text(encoding="utf-8")
    console_source = CONSOLE.read_text(encoding="utf-8")

    assert 'adminSiteV3Route' in route_source
    assert '<CasinoKingConsole area="admin" adminSiteV3Route />' in route_source
    assert 'adminSection === "site_v3"' in console_source
    assert 'router.push("/admin/site-v3")' in console_source
    assert "http://localhost:3001" not in console_source
