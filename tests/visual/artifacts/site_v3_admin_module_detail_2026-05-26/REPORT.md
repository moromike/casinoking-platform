# Site V3 Admin Module Detail Smoke - 2026-05-26

Scope: verify that module type and module instance detail screens are readable for a human CMS operator.

Evidence:
- `01_module_library.png` - module library grouped by type category.
- `02_hero_category.png` - Hero and banners category detail.
- `03_hero_type_detail_grouped.png` - Hero banner type detail with grouped fields.
- `04_hero_instance_grouped.png` - mounted Hero banner instance with grouped editor fields.

Gate result: PASS.

Notes:
- Browser smoke logged in through `/admin/site-v3`.
- Field sections are grouped as Content, Links and actions, Assets and media, Game catalog, or Legal and safe HTML depending on module descriptor.
- Backend, draft/publish and public renderer contracts were not changed.
