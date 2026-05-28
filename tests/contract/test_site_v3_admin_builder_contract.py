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
ADMIN_ROUTE = ROOT / "frontend" / "app" / "admin" / "site-v3" / "page.tsx"
CONSOLE = ROOT / "frontend" / "app" / "ui" / "casinoking-console.tsx"


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
    builder_source = (
        ROOT
        / "frontend"
        / "app"
        / "ui"
        / "site-v3-admin"
        / "site-v3-admin-builder.tsx"
    ).read_text(encoding="utf-8")

    for category in ["structure", "hero", "catalog", "promo", "text_legal"]:
        assert f'key: "{category}"' in descriptor_source

    assert "SITE_V3_MODULE_CATEGORIES" in builder_source
    assert "site-v3-library-category-row" in builder_source
    assert "site-v3-inline-module-select-row" in builder_source
    assert "Add selected module" in builder_source
    assert "site-v3-inline-module-option" not in builder_source
    assert "Add module</option>" not in builder_source


def test_site_v3_admin_complex_fields_are_human_editors():
    builder_source = (
        ROOT
        / "frontend"
        / "app"
        / "ui"
        / "site-v3-admin"
        / "site-v3-admin-builder.tsx"
    ).read_text(encoding="utf-8")

    assert "site-v3-nav-editor" in builder_source
    assert "Add navigation item" in builder_source
    assert "linesToNavItems" not in builder_source
    assert "Search games" in builder_source
    assert "Clear selected games" in builder_source
    assert "No games match this search" in builder_source


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


def test_site_v3_admin_asset_picker_consumes_existing_site_assets():
    api_source = (
        ROOT
        / "frontend"
        / "app"
        / "ui"
        / "site-v3-admin"
        / "site-v3-admin-api.ts"
    ).read_text(encoding="utf-8")
    builder_source = (
        ROOT
        / "frontend"
        / "app"
        / "ui"
        / "site-v3-admin"
        / "site-v3-admin-builder.tsx"
    ).read_text(encoding="utf-8")

    assert "listSiteV3Assets" in api_source
    assert "/admin/sites/" in api_source
    assert "asset_kind=homepage_banner" in api_source or "homepage_banner" in api_source
    assert "site-v3-asset-picker" in builder_source
    assert "aria-pressed={selected}" in builder_source
    assert "asset_id: asset.id" in builder_source
    assert "public_url: asset.public_url" in builder_source
    assert "Manual public URL" in builder_source
    assert "Asset ID" not in builder_source
    assert "Asset kind" not in builder_source


def test_site_v3_admin_route_mounts_existing_console_without_new_login():
    route_source = ADMIN_ROUTE.read_text(encoding="utf-8")
    console_source = CONSOLE.read_text(encoding="utf-8")

    assert 'adminSiteV3Route' in route_source
    assert '<CasinoKingConsole area="admin" adminSiteV3Route />' in route_source
    assert 'adminSection === "site_v3"' in console_source
    assert 'router.push("/admin/site-v3")' in console_source
    assert "http://localhost:3001" not in console_source
