# Site V3 Admin Module Navigation Smoke - 2026-05-27

Scope: verify the CMS navigation fixes requested for module flow.

Evidence:
- `01_modules_submenu.png` - Modules side navigation exposes category subitems and no standalone Module settings entry.
- `02_inline_add_module_picker.png` - Composition Add module opens an inline picker without leaving the page flow.
- `03_added_module_instance.png` - choosing a module from the inline picker opens the new mounted instance.

Gate result: PASS.

Notes:
- Browser smoke logged in through `/admin/site-v3`.
- `Module settings` is now contextual only: it appears as the module instance screen, not as a side-nav item.
- Backend, draft/publish and public renderer contracts remain unchanged.
