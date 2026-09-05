#!/usr/bin/env bash
# seed-sito.sh - crea e pubblica la home page minima del sito v3 (casinoking/it).
# Riutilizza i service esistenti backend/app/modules/platform/site_v3/service.py
# (save_draft + publish_page) dentro il container backend gia' avviato.
# NON cancella nulla: solo INSERT/UPDATE di stato tramite i service applicativi.
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-/home/micheleubuntu/Downloads/CasinoKing/casinoking-platform/infra/docker/docker-compose.yml}"
SITE_CODE="${SITE_CODE:-casinoking}"
PAGE_CODE="${PAGE_CODE:-home}"
LOCALE="${LOCALE:-it}"

docker compose -f "${COMPOSE_FILE}" exec -T \
  -e SEED_SITE_CODE="${SITE_CODE}" \
  -e SEED_PAGE_CODE="${PAGE_CODE}" \
  -e SEED_LOCALE="${LOCALE}" \
  backend python - <<'PY'
import os

from app.db.connection import db_connection
from app.modules.platform.site_v3 import service

site_code = os.environ.get("SEED_SITE_CODE", "casinoking")
page_code = os.environ.get("SEED_PAGE_CODE", "home")
locale = os.environ.get("SEED_LOCALE", "it")

# Prendi un admin esistente come attore del seed (nessuna creazione di utenti).
with db_connection() as connection:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id FROM admin_profiles
            ORDER BY created_at
            LIMIT 1
            """
        )
        row = cursor.fetchone()
if row is None:
    raise SystemExit("Nessun admin in admin_profiles: impossibile pubblicare.")
admin_user_id = str(row["user_id"])
print(f"Attore admin: {admin_user_id}")

modules = [
    {
        "module_code": "global_header",
        "slot_key": "header",
        "sort_order": 0,
        "config_json": {
            "brand_label": "CasinoKing",
            "login_label": "Accedi",
            "account_label": "Conto",
        },
    },
    {
        "module_code": "hero_banner",
        "slot_key": "hero",
        "sort_order": 1,
        "config_json": {
            "headline": "Benvenuto su CasinoKing",
            "body": "Gioca a Mines, BOXE e HI-LO.",
            "cta_label": "Gioca ora",
            "cta_title_code": "mines001",
            "show_copy": True,
            "show_cta": True,
        },
    },
    {
        "module_code": "game_grid",
        "slot_key": "main",
        "sort_order": 2,
        "config_json": {
            "heading": "I nostri giochi",
            "title_codes": ["mines001", "boxe001", "hilo001"],
        },
    },
    {
        "module_code": "global_footer",
        "slot_key": "footer",
        "sort_order": 3,
        "config_json": {
            "legal_text": "CasinoKing - piattaforma di gioco. Vietato ai minori di 18 anni.",
        },
    },
]

saved = service.save_draft(
    site_code=site_code,
    page_code=page_code,
    locale=locale,
    title="CasinoKing - Home",
    modules=modules,
    expected_draft_version=None,
    admin_user_id=admin_user_id,
)
draft_version = int(saved["page"]["draft_version"])
print(f"Bozza salvata: draft_version={draft_version}")

published = service.publish_page(
    site_code=site_code,
    page_code=page_code,
    locale=locale,
    expected_draft_version=draft_version,
    admin_user_id=admin_user_id,
)
print(
    "Pubblicata: "
    f"page={published['page']['page_code']} "
    f"status={published['page']['status']} "
    f"published_version={published['page']['published_version']}"
)
PY

echo "Seed sito completato: ${SITE_CODE}/${PAGE_CODE} (${LOCALE})"
