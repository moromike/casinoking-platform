Status: ACTIVE
Last meaningful update: 2026-05-25

# Site V3 - Lifecycle, API And Security Plan

## 0. Scopo

Questo documento definisce come Site V3 deve salvare, validare, pubblicare e
servire pagine e moduli.

Il lab CMS v2 attuale ha CRUD minimo, ma non basta:

- publish diretto su status;
- public endpoint non veramente published-only;
- niente snapshot published;
- niente versioning;
- niente contract per module schema;
- token admin gestito male nel lab frontend.

## 1. Lifecycle Page

Stati consigliati:

| Stato | Significato | Pubblico? |
| --- | --- | --- |
| `draft` | Bozza editabile admin | No |
| `published` | Versione live servita dal renderer pubblico | Si |
| `archived` | Pagina ritirata | No |

Concetto chiave: `draft` e `published` non devono essere lo stesso record
mutato in place. Serve uno snapshot pubblicato.

## 2. Lifecycle Flow

```text
Admin edits draft
  -> Save draft
  -> Validate draft
  -> Publish
  -> Create published snapshot/version
  -> Public renderer reads latest published snapshot only
```

Regole:

- `save draft` non cambia la pagina pubblica;
- `publish` richiede validation green;
- `publish` crea una versione immutabile o semi-immutabile;
- public renderer non legge draft;
- admin preview puo' leggere draft solo con auth admin;
- delete fisico evitato in MVP: usare archive dove possibile.

## 3. Data Model Target

Decisione lockata 2026-05-25 - Michele approved: WP2 crea nuove tabelle
`site_v3_pages`, `site_v3_page_versions`, `site_v3_modules`; `cms_v2_*` resta
dormiente.

Entita' minime:

| Entita' | Campi chiave |
| --- | --- |
| `site_v3_pages` | `id`, `site_code`, `page_code`, `locale`, `title`, `status`, `draft_version`, `published_version`, audit fields |
| `site_v3_page_versions` | `id`, `page_id`, `version`, `status`, `snapshot_json`, `validation_json`, `published_at`, `published_by` |
| `site_v3_modules` | `id`, `page_id`, `module_code`, `schema_version`, `slot_key`, `sort_order`, `config_json`, audit fields |
| asset registry mapping | asset ownership o references | Preferire asset registry platform se compatibile; no tabella asset dedicata nel lock MVP. |
| `admin_audit_events` | action, actor, before/after hash, request/support id, `source=site_v3` | Riuso obbligatorio; no tabella audit dedicata. |

Versioning MVP lockato:

- `publish` crea un published snapshot;
- admin mostra history list;
- revert UI resta Phase 2;
- public renderer legge solo l'ultimo snapshot published.

## 4. API Contract Target

### Admin APIs

| Endpoint logico | Metodo | Scopo |
| --- | --- | --- |
| `/admin/site-v3/sites/{site_code}/pages` | GET | lista pagine admin |
| `/admin/site-v3/sites/{site_code}/pages/{page_code}` | GET | draft + published summary |
| `/admin/site-v3/sites/{site_code}/pages/{page_code}/draft` | PUT | save draft |
| `/admin/site-v3/sites/{site_code}/pages/{page_code}/validate` | POST | validation dry-run |
| `/admin/site-v3/sites/{site_code}/pages/{page_code}/publish` | POST | publish snapshot |
| `/admin/site-v3/sites/{site_code}/pages/{page_code}/versions` | GET | history |
| `/admin/site-v3/sites/{site_code}/assets` | GET/POST | asset list/upload se non basta platform asset registry |

### Public APIs

| Endpoint logico | Metodo | Scopo |
| --- | --- | --- |
| `/site-v3/sites/{site_code}/pages/{page_code}` | GET | latest published page |
| `/site-v3/sites/{site_code}/navigation` | GET | navigation/header/footer published |
| `/site-v3/sites/{site_code}/manifest` | GET | public site manifest/cache hints |

Public APIs non devono accettare token admin e non devono esporre draft.

## 5. Validation Contract

Validation deve produrre:

```text
{
  "status": "valid" | "invalid",
  "issues": [
    {
      "severity": "error" | "warning",
      "module_id": "...",
      "field": "headline",
      "code": "SITEV3.VALIDATION.REQUIRED",
      "message": "Headline is required"
    }
  ]
}
```

Errori bloccanti:

- modulo sconosciuto;
- schema_version non supportata;
- campo required vuoto;
- asset mancante/non valido;
- title_code inesistente;
- rich text non sanitizzabile;
- route/page_code duplicato;
- locale mancante se obbligatorio.

Warning non bloccanti:

- immagine sotto dimensione consigliata;
- copy molto corto;
- CTA assente su promo;
- modulo non ottimale su mobile.

## 6. Security Contract

| Area | Regola |
| --- | --- |
| Auth admin | Usa admin session/token esistente dentro `:3000`, niente query token. |
| RBAC | Richiedere profilo admin esplicito; no fallback superadmin. |
| Public read | Solo published snapshot, no draft leakage. |
| Rich text | Sanitizzazione server-side o validazione severa + renderer safe. |
| Assets | MIME/size/dimension policy, no file path leakage. |
| Audit | save/publish/archive/upload devono registrare actor/request/support id. |
| Errors | usare AppError/CK.* o envelope platform, non stringhe raw. |
| Logging | niente body interi, niente token, niente PII non necessaria. |

## 7. Caching / Freshness

MVP:

- no caching aggressiva durante sviluppo;
- public API puo' restituire `published_version` e `updated_at`;
- renderer pubblico puo' ricaricare al refresh;
- cache/CDN fase 2.

Non introdurre cache prima di avere snapshot published stabile.

## 8. Migration Strategy Dal Lab CMS v2

| Elemento attuale | Strategia |
| --- | --- |
| `cms_v2_pages` | Dormiente; non migrare in place in WP2. |
| `cms_v2_modules` | Dormiente; usabile solo come riferimento concettuale. |
| `/admin/cms-v2/*` | Non espandere come API finale; WP2 progetta route Site V3 nuove. |
| `/public/cms-v2/*` | Non usare per renderer finale. |
| `frontend-v2` token flow | Eliminare. |
| `frontend-v2` registry | Usabile come riferimento; non importare direttamente. |
| `frontend-v3/` | Nuova app public renderer, ownership WP4. |

## 9. Tests/Gate

Gate backend:

- admin draft save non modifica public response;
- publish crea/aggiorna snapshot;
- public endpoint non ritorna draft;
- validation blocca modulo sconosciuto;
- validation blocca title_code non pubblicabile;
- rich text unsafe viene rifiutato/sanitizzato;
- RBAC admin richiesto;
- audit event registrato per save/publish.

Gate frontend:

- builder usa admin auth esistente;
- save draft attiva dirty state e poi torna saved;
- publish disabilitato se validation error;
- renderer pubblico visualizza solo published;
- V1 lobby ancora funziona.

## 10. Stop-Before-Code

Fermarsi se:

- public endpoint puo' vedere draft;
- RBAC usa fallback impliciti;
- HTML viene salvato/renderizzato senza policy;
- il builder richiede un nuovo login separato;
- si tenta di modificare `cms_v2_*` invece di lasciarlo dormiente;
- si tenta di aprire WP2 senza brief Parte A CTO con DDL/API/payload/error codes/test plan.
