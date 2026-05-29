Status: ACTIVE
Last meaningful update: 2026-05-29

# Site V3 - Module Taxonomy And Content Model

## 0. Scopo

Questo documento definisce quali moduli Site V3 esistono nel MVP, quali sono
futuri, e quale contratto ogni modulo deve rispettare.

Regola chiave: un modulo non e' solo un componente React. Un modulo e':

- manifest;
- schema config;
- validazione;
- admin editor;
- admin preview;
- public renderer;
- mobile behavior;
- asset policy;
- i18n policy;
- test/gate.

## 1. Module Manifest Contract

Ogni modulo Site V3 deve dichiarare:

| Campo | Obbligatorio | Descrizione |
| --- | --- | --- |
| `module_code` | Si' | Identificatore stabile, es. `hero_banner`. |
| `schema_version` | Si' | Versione config, serve per migrazioni future. |
| `label` | Si' | Nome admin leggibile. |
| `category` | Si' | `layout`, `hero`, `games`, `promo`, `content`, `compliance`. |
| `surfaces` | Si' | Dove puo' comparire: `homepage`, `lobby`, `static_page`. |
| `config_schema` | Si' | Campi editabili con tipo, required, maxLength, help. |
| `validation_rules` | Si' | Required, formato, asset required, CTA validi. |
| `asset_kinds` | Se serve | Kind asset ammessi e vincoli upload/render. |
| `admin_preview_renderer` | Si' | Preview dentro builder. |
| `public_renderer` | Si' | Renderer player-quality. |
| `mobile_behavior` | Si' | Come scala/reordina su mobile. |
| `fallback_behavior` | Si' | Cosa succede se config/asset mancano. |
| `i18n_mode` | Si' | `localized_fields` o `locale_agnostic`. |

## 2. MVP Module Set

Decisione lockata 2026-05-25 - Michele approved, aggiornata dalle tranche
WP5/WP-MIG3: il set built-in contiene questi 9 moduli.

| Modulo | Categoria | MVP | Uso | Note |
| --- | --- | --- | --- | --- |
| `global_header` | layout | Si' | Header sito V3 | Link login/account alla shell player Site V3; i link gioco aprono shell Site V3 con runtime legacy incapsulato. |
| `hero_banner` | hero | Si' | Prima impressione homepage | Immagine/video futuro, CTA verso gioco o pagina. |
| `game_grid` | games | Si' | Lista giochi pubblicati | Consuma catalogo, non duplica dati. |
| `game_grid_4x` | games | Si' | Lista giochi pubblicati con card grandi | Stessi title e asset del catalogo, quattro card per riga desktop. |
| `featured_game` | games | Si' | Evidenza singolo title | Se title nascosto/non disponibile mostra fallback. |
| `promo_band` | promo | Si' | Promo editoriale | Asset + copy + CTA. |
| `system_registration_form` | system | Si' | Config pagina `/register` | Copy, campi opzionali, step documenti e redirect; non cambia auth/wallet/ledger ne' persiste documenti. |
| `rich_text_safe` | content | Si' limitato | Blocchi testo semplici | HTML solo sanitizzato/allowlist. |
| `global_footer` | layout | Si' | Footer sito V3 | Link legali/account; account punta alla shell player Site V3. |

## 3. Phase 2 Modules

| Modulo | Categoria | Perche' non MVP |
| --- | --- | --- |
| `game_detail` | games | Richiede design e content model per singolo gioco. |
| `static_page_body` | content | Serve quando apriamo Terms/FAQ/Responsible Gaming in V3. |
| `responsible_gaming_panel` | compliance | Importante, ma meglio con copy/legal review. |
| `seo_metadata_block` | meta | Da gestire a livello page, non come modulo visuale. |
| `promo_carousel` | promo | Più complesso di un promo band; rischio visual polish. |
| `provider_strip` | games | Utile quando esistono provider/brand multipli. |

## 4. Field Type Registry

Il builder non deve inventare input ad hoc per modulo. Serve un piccolo registry
di field type.

Decisione lockata 2026-05-25 - Michele approved: il model i18n deve esistere
da subito tramite `locale`; il content MVP viene popolato solo in italiano.

| Field type | Esempio | Admin control | Validazione |
| --- | --- | --- | --- |
| `text` | titolo hero | input | required/maxLength |
| `textarea` | descrizione promo | textarea | required/maxLength |
| `rich_text_safe` | copy pagina | editor limitato | allowlist HTML |
| `select` | CTA target type | select | enum |
| `game_title_ref` | title_code | picker catalogo | title esistente/non archiviato |
| `asset_ref` | image/video | asset picker | kind/mime/dimensioni |
| `url_path` | link interno | input con helper | path safe |
| `boolean` | mostra badge | toggle | boolean |
| `number` | ordine/peso | input numerico | min/max |
| `color_token` | tema opzionale | token picker | solo token ammessi |

## 5. Asset Policy Per Moduli MVP

| Modulo | Asset kind | Vincoli minimi da mostrare in UI |
| --- | --- | --- |
| `hero_banner` | `site_v3_hero_media` | PNG/JPEG/WebP; max 2 MB; consigliato 1920x720; render `cover`, crop possibile. |
| `promo_band` | `site_v3_promo_image` | PNG/JPEG/WebP; max 1 MB; consigliato 1200x480; render `cover`. |
| `featured_game` | game title assets | read-only dal title asset registry | Non uploada asset propri salvo override futuro. |
| `game_grid` | game title assets | read-only dal title asset registry | Usa lobby card/title assets pubblicati. |
| `global_header/footer` | nessuno MVP | n/a | Link e copy, non asset. |

## 6. Game Catalog Consumption

I moduli games devono consumare il catalogo esistente:

- `/games/library` per player-visible published titles;
- catalog/admin endpoints solo nel builder;
- `title_code` resta source of truth;
- demo/real enabled restano sul publishing game title;
- V3 non crea copie locali del gioco.

Regola: se un modulo contiene `title_code`, la validazione deve verificare che
quel title sia ancora disponibile per il sito.

## 7. Rich Text Safety

`rich_text_safe` non puo' accettare HTML libero.

Allowlist MVP raccomandata:

- `p`;
- `strong`;
- `em`;
- `ul`;
- `ol`;
- `li`;
- `a` solo con href interno o https;
- `br`;
- `h2`, `h3`.

Vietati:

- `script`;
- inline event handlers;
- style arbitrario;
- iframe;
- form;
- input;
- SVG inline non sanitizzato.

## 8. Mobile Contract

Ogni modulo deve dichiarare:

| Breakpoint | Regola |
| --- | --- |
| Desktop | layout pieno, max-width coerente col design V3 |
| Tablet | colonne ridotte, CTA ancora visibili |
| Mobile portrait | no overflow orizzontale, testi a capo, asset con aspect ratio stabile |
| Mobile landscape | nessun contenuto critico fuori viewport senza intenzione |

Barre di scorrimento orizzontali non sono accettabili salvo area editor admin
esplicitamente tabellare. Sul player pubblico sono vietate.

## 9. Module Green Definition

Un modulo e' green solo se tutte le righe sono vere:

| Layer | Green se |
| --- | --- |
| Manifest | campi/versione/categorie dichiarati |
| Content | copy/config reali, non placeholder |
| Admin editor | controlli leggibili, validazione, help |
| Admin preview | preview fedele al player per layout essenziale |
| Public renderer | bello, responsive, published-only |
| Assets | upload/picker/constraints/render policy coerenti |
| i18n | campi localizzati dove serve |
| Tests | validation + renderer smoke |
| Product Owner | walkthrough su `:3000` e `:3001` |

## 10. Stop-Before-Code

Fermarsi se:

- qualcuno vuole aggiungere un modulo senza manifest;
- qualcuno vuole aggiungere moduli oltre i 7 MVP senza nuova approvazione;
- un modulo salva config non validata;
- il renderer pubblico usa `dangerouslySetInnerHTML` senza sanitizzazione;
- il modulo games duplica catalogo giochi;
- l'asset upload non mostra formato/dimensioni/render policy;
- il player pubblico richiede token admin;
- mobile produce overflow orizzontale.
