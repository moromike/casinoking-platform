import pathlib
import re

from app.modules.platform.site_v3.manifests import list_module_manifests


ROOT = pathlib.Path(__file__).resolve().parents[2]
FRONTEND_V3_APP = ROOT / "frontend-v3" / "app"
FRONTEND_DESCRIPTOR = (
    FRONTEND_V3_APP
    / "ui"
    / "site-v3-admin"
    / "site-v3-admin-descriptors.ts"
)
ADMIN_UI_DIR = FRONTEND_V3_APP / "ui" / "site-v3-admin"
ADMIN_ROUTE = FRONTEND_V3_APP / "admin" / "site-v3" / "page.tsx"
ADMIN_SHELL = FRONTEND_V3_APP / "ui" / "admin-site-v3-page.tsx"
LEGACY_ADMIN_ROUTE = ROOT / "frontend" / "app" / "admin" / "site-v3" / "page.tsx"
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

    for category in ["structure", "hero", "catalog", "promo", "system", "text_legal"]:
        assert f'key: "{category}"' in descriptor_source

    assert "SITE_V3_MODULE_CATEGORIES" in admin_source
    assert "site-v3-library-category-row" in admin_source
    assert "site-v3-inline-module-select-row" in admin_source
    assert "Add selected module" in admin_source
    assert "site-v3-inline-module-option" not in admin_source
    assert "Add module</option>" not in admin_source


def test_site_v3_admin_exposes_system_registration_page_management():
    descriptor_source = FRONTEND_DESCRIPTOR.read_text(encoding="utf-8")
    admin_source = read_admin_ui_source()
    builder_source = (ADMIN_UI_DIR / "site-v3-admin-builder.tsx").read_text(encoding="utf-8")
    nav_source = (ADMIN_UI_DIR / "screens" / "site-v3-admin-nav.tsx").read_text(encoding="utf-8")

    assert 'moduleCode: "system_registration_form"' in descriptor_source
    assert 'category: "system"' in descriptor_source
    assert 'post_register_path: "/account"' in descriptor_source
    assert "This first slice does not persist consent records." in descriptor_source
    assert "System pages" in nav_source
    assert 'kind: "systemPages"' in admin_source
    assert "SiteV3SystemPagesScreen" in admin_source
    assert "openRegistrationSystemPage" in builder_source
    assert 'page_code: "register"' in builder_source
    assert 'title: "Registration"' in builder_source
    assert 'createModuleFromDescriptor("system_registration_form", 0)' in builder_source
    assert "Save, validate and publish to make /register consume this config." in builder_source
    assert 'const CUSTOM_DEFINITION_CATEGORIES: SiteV3ModuleDefinitionCategory[] = ["hero", "catalog", "promo", "text_legal"]' in admin_source


def test_site_v3_admin_complex_fields_are_human_editors():
    admin_source = read_admin_ui_source()

    assert "site-v3-nav-editor" in admin_source
    assert "Add navigation item" in admin_source
    assert "linesToNavItems" not in admin_source
    assert "Search available games" in admin_source
    assert "Selected game titles" in admin_source
    assert "Available title library" in admin_source
    assert "Clear selected games" in admin_source
    assert "No games match this search" in admin_source
    assert "game icon" not in admin_source.lower()


def test_site_v3_admin_module_creation_stays_in_composition():
    builder_source = (ADMIN_UI_DIR / "site-v3-admin-builder.tsx").read_text(encoding="utf-8")

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
    builder_source = (ADMIN_UI_DIR / "site-v3-admin-builder.tsx").read_text(encoding="utf-8")

    validate_source = builder_source.split("async function handleValidate", maxsplit=1)[1].split("async function handlePublish", maxsplit=1)[0]
    archive_source = builder_source.split("async function handleArchive", maxsplit=1)[1].split("const isBusy", maxsplit=1)[0]
    save_source = builder_source.split("async function handleSaveDraft", maxsplit=1)[1].split("async function handleValidate", maxsplit=1)[0]
    publish_source = builder_source.split("async function handlePublish", maxsplit=1)[1].split("async function handleArchive", maxsplit=1)[0]

    assert 'setCurrentView({ kind: "validation" })' in validate_source
    assert 'setCurrentView({ kind: "pages" })' in archive_source
    assert "loadPages(null, { preserveDirty: false })" in archive_source
    assert 'setCurrentView({ kind: "composition" })' in save_source
    assert 'setCurrentView({ kind: "composition" })' in publish_source


def test_site_v3_admin_dirty_state_blocks_page_filter_and_reload_loss():
    builder_source = (ADMIN_UI_DIR / "site-v3-admin-builder.tsx").read_text(encoding="utf-8")

    assert "confirmDiscardUnsavedChanges" in builder_source
    assert 'loadPages(undefined, { preserveDirty: false })' in builder_source
    assert "async function loadPage" in builder_source
    assert "Promise<boolean>" in builder_source
    assert "function changeLocale" in builder_source
    assert "function changeStatusFilter" in builder_source
    assert "setLocale(nextLocale)" in builder_source
    assert "setStatusFilter(nextStatusFilter)" in builder_source


def test_site_v3_admin_publish_requires_validation_green():
    builder_source = (ADMIN_UI_DIR / "site-v3-admin-builder.tsx").read_text(encoding="utf-8")
    action_bar_source = (ADMIN_UI_DIR / "screens" / "site-v3-page-action-bar.tsx").read_text(encoding="utf-8")
    detail_source = (ADMIN_UI_DIR / "screens" / "site-v3-page-detail-screen.tsx").read_text(encoding="utf-8")

    assert 'validation.status !== "valid"' in builder_source
    assert "Run validation and fix any issues before publishing." in builder_source
    assert 'validationStatus !== "valid"' in action_bar_source
    assert 'validation.status !== "valid"' in detail_source


def test_site_v3_admin_ia_contract_keeps_mounted_instances_out_of_left_nav():
    nav_source = (ADMIN_UI_DIR / "screens" / "site-v3-admin-nav.tsx").read_text(encoding="utf-8")
    helper_source = (ADMIN_UI_DIR / "site-v3-admin-helpers.ts").read_text(encoding="utf-8")
    composition_source = (ADMIN_UI_DIR / "screens" / "site-v3-composition-screen.tsx").read_text(encoding="utf-8")
    admin_source = read_admin_ui_source()

    assert "Mounted modules" not in nav_source
    assert "modules.map" not in nav_source
    assert 'kind: "moduleInstance"' not in nav_source
    assert "SITE_V3_MODULE_DESCRIPTORS[module.module_code]" not in nav_source
    assert "SiteV3NewModuleWizardScreen" not in admin_source
    assert 'kind: "moduleWizard"' not in helper_source
    assert 'kind: "moduleStudio"' in helper_source
    assert "Module Studio" in admin_source
    assert "renderer_template" in admin_source
    assert "updateSiteV3ModuleDefinitionDraft" in admin_source
    assert "Use template fields" in admin_source
    assert "Edit draft" in admin_source
    assert "Clone" in admin_source
    assert "Update draft" in admin_source
    assert "TEMPLATE_FIELD_PRESETS" in admin_source
    assert "Template preview" in admin_source
    assert "StudioTemplatePreview" in admin_source
    assert "CustomModuleBadge" in admin_source
    assert "site-v3-module-custom-badge" in admin_source
    assert "Add module to page" in composition_source
    assert "site-v3-module-order-index" in composition_source
    assert "previewHeadline(module, descriptors)" in composition_source


def test_site_v3_admin_asset_picker_consumes_existing_site_assets():
    api_source = (ADMIN_UI_DIR / "site-v3-admin-api.ts").read_text(encoding="utf-8")
    admin_source = read_admin_ui_source()

    assert "listSiteV3Assets" in api_source
    assert "uploadSiteV3Asset" in api_source
    assert "apiFormRequest" in api_source
    assert "/admin/sites/" in api_source
    assert "asset_kind=homepage_banner" in api_source or "homepage_banner" in api_source
    assert "site-v3-asset-picker" in admin_source
    assert "site-v3-asset-upload" in admin_source
    assert "onUploadSiteAsset" in admin_source
    assert "accept=\"image/png,image/jpeg,image/webp\"" in admin_source
    assert "Accepted formats: PNG, JPEG, WebP" in admin_source
    assert "Max size: 2 MB" in admin_source
    assert "Recommended dimensions: 1600x900 or larger, 16:9" in admin_source
    assert "aria-pressed={selected}" in admin_source
    assert "asset_id: asset.id" in admin_source
    assert "public_url: asset.public_url" in admin_source
    assert "Manual public URL" in admin_source
    assert "https://... or /static/..." in admin_source
    assert "https://... or /assets/..." not in admin_source
    assert "cover/crop with no stretch" in admin_source
    assert "Upload is not part of WP3" not in admin_source
    assert "Asset ID" not in admin_source
    assert "Asset kind" not in admin_source


def test_site_v3_admin_route_uses_v3_shell_and_legacy_redirect():
    route_source = ADMIN_ROUTE.read_text(encoding="utf-8")
    shell_source = ADMIN_SHELL.read_text(encoding="utf-8")
    legacy_route_source = LEGACY_ADMIN_ROUTE.read_text(encoding="utf-8")
    console_source = CONSOLE.read_text(encoding="utf-8")
    admin_source = read_admin_ui_source()

    assert "AdminSiteV3Page" in route_source
    assert "SiteV3AdminBuilder" in shell_source
    assert '"/admin/auth/login"' in shell_source
    assert '"/admin/auth/me"' in shell_source
    assert "ADMIN_STORAGE_KEYS" in shell_source
    assert "redirect(`${SITE_V3_BASE_URL}/admin/site-v3`)" in legacy_route_source
    assert "CasinoKingConsole" not in legacy_route_source
    assert 'router.push("/admin/site-v3")' in console_source
    assert "http://localhost:3001" not in console_source
    assert "NEXT_PUBLIC_SITE_V3_BASE_URL" in admin_source
    assert "href={SITE_V3_PUBLIC_BASE_URL}" in admin_source
