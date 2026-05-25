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


def test_site_v3_admin_route_mounts_existing_console_without_new_login():
    route_source = ADMIN_ROUTE.read_text(encoding="utf-8")
    console_source = CONSOLE.read_text(encoding="utf-8")

    assert 'adminSiteV3Route' in route_source
    assert '<CasinoKingConsole area="admin" adminSiteV3Route />' in route_source
    assert 'adminSection === "site_v3"' in console_source
    assert 'router.push("/admin/site-v3")' in console_source
    assert "http://localhost:3001" not in console_source
