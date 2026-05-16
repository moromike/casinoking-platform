# CasinoKing - Mines skin SKIN-X0 audit

## Stato

Audit tecnico SKIN-X0 completato il 2026-05-10.

Questo documento e' l'output operativo richiesto da
`docs/MINES_SKIN_EXTENDED_CUSTOMIZATION_PLAN.md` prima di aprire SKIN-X1.
Non introduce codice e non cambia comportamento runtime.

Verdetto: SKIN-X1 puo' partire, ma solo rispettando i vincoli obbligatori sotto.
L'audit conferma che il registry Title attuale non e' ancora pronto per la skin
estesa senza migration, validator per-kind e resolver theme aggiornato.

## Fonti lette

Documenti effettivamente letti:

- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/README.md`
- `docs/AI_CRITICAL_JUDGMENT_RULES.md`
- `docs/ARCHITECTURE_ATLAS_MINES.md`
- `docs/THEME_SYSTEM_PLAN.md`
- `docs/ASSET_REGISTRY_PLAN.md`
- `docs/MINES_IN_GAME_TITLE_PLAN.md`
- `docs/MINES_SKIN_EXTENDED_CUSTOMIZATION_PLAN.md`

Codice effettivamente letto:

- `backend/app/modules/platform/asset_registry/service.py`
- `backend/app/modules/platform/asset_registry/storage.py`
- `backend/app/api/routes/admin_assets.py`
- `backend/app/modules/platform/catalog/theme_service.py`
- `backend/app/api/routes/title_theme.py`
- `backend/app/main.py`
- `backend/migrations/sql/0026__title_assets.sql`
- `backend/app/modules/platform/site_cms/service.py`
- `frontend/app/lib/theme/title-theme-provider.tsx`
- `frontend/app/lib/types.ts`
- `frontend/app/ui/mines/mines-standalone.tsx`
- `frontend/app/ui/mines/mines.css`
- `frontend/app/ui/mines/mines-board-assets-editor.tsx`
- `frontend/app/ui/mines/mines-backoffice-editor.tsx`
- `tests/integration/test_asset_registry.py`
- `tests/contract/test_admin_assets_contract.py`
- `tests/contract/test_title_theme_contract.py`
- `tests/integration/test_admin_audit_log.py`

File individuati ma non letti integralmente:

- documenti Word canonici in `docs/word/`
- allegati runtime Mines in `docs/runtime/`

Motivo: SKIN-X0 riguarda asset/theme/backoffice visuale. Non cambia gameplay,
RNG, fairness, payout, RTP, wallet, ledger o settlement.

## Checklist SKIN-X0

| Area | Esito | Evidenza codice | Impatto SKIN-X1 |
| --- | --- | --- | --- |
| Nuovi asset kind `title_logo`, `game_area_background`, `cell_face_down_background` | NO | `0026__title_assets.sql` consente solo `logo`, `background`, `symbol_safe`, `symbol_mine`, `audio_win`, `audio_lose`, `audio_click`, `font`. | Serve migration DB per estendere il check constraint. |
| Uploadable title image kinds | NO per nuovi kind | `IMAGE_ASSET_KINDS = {"logo", "background", "symbol_safe", "symbol_mine"}`. | Aggiungere i 3 kind espliciti V1 senza rompere i legacy. |
| Lettura asset legacy | SI | `resolve_title_theme` pubblica `assets` da `list_title_assets`, mappando ogni `asset_kind` attivo. | `logo` e `background` restano leggibili. Il nuovo editor non deve scriverli. |
| MIME PNG | SI | `IMAGE_MIME_EXTENSIONS` contiene `image/png`. | Confermato. |
| MIME WebP su Title assets | NO | `IMAGE_MIME_EXTENSIONS` non contiene `image/webp`. | SKIN-X1 deve aggiungere WebP per i nuovi kind skin. |
| MIME SVG su Title assets legacy | SI | `IMAGE_MIME_EXTENSIONS` contiene `image/svg+xml`; test esistente carica SVG su `symbol_mine`. | Non aprire SVG sui nuovi kind. Non cancellare compatibilita' legacy in questo cantiere. |
| Sanitizzazione SVG | NO | Nessun sanitizer asset trovato; `FilesystemAssetStorage.write_if_missing` scrive bytes raw; static serving via `StaticFiles`. | Confermata decisione: SVG escluso dalla V1 skin. |
| Serving sandbox/CSP per SVG | NO | `/static/games` serve da `StaticFiles` standard, senza route dedicata sandbox/CSP. | Non usare SVG per nuovi asset skin. |
| Cap immagini title registry | PARZIALE | `MAX_IMAGE_BYTES = 512 * 1024` globale per tutti gli image asset. | Servono cap per-kind: 150 KB, 400 KB, 256 KB. |
| Cap UI board assets legacy | PARZIALE | Backoffice board assets limita frontend a 150 KB e accetta SVG/PNG. | La nuova UI skin deve avere copy/cap propri, non ereditare il limite legacy 150 KB. |
| Estensione file derivata dal MIME | SI | `_extension_for_mime` usa la mappa MIME, non il filename utente. | Buona base da riusare. |
| Path traversal storage | SI | `FilesystemAssetStorage._resolve` rifiuta path assoluti e `..`. | Buona base da riusare. |
| Audit upload/delete asset | SI | `upload_title_asset` e `delete_title_asset` scrivono `title_asset_upload` / `title_asset_delete` se hanno admin id; route admin lo passa. | SKIN-X1/X3 deve continuare su questo pattern. |
| Audit theme publish | SI | `publish_admin_title_theme` scrive `theme_publish` in `admin_audit_log`. | Publish skin/theme deve restare auditato. |
| Theme source attuale | PARZIALE | `theme_tokens_json` / `draft_theme_tokens_json` esistono ma il validator accetta solo token flat. | Serve validator documento theme: token flat + `skin` strutturato controllato. |
| Public theme `tokens` flat | SI | `TitleThemeProvider` passa `theme.tokens` come `CSSProperties`. | Il resolver deve pubblicare solo CSS variables flat dentro `tokens`. |
| Oggetti nested in `tokens` | BLOCCATI oggi | `validate_theme_tokens` rifiuta valori non stringa e token non allowlistati. | Bene come guardrail, ma SKIN-X1 deve gestire `skin` fuori dallo style React. |
| Default theme | SI | `DEFAULT_THEME_TOKENS`; test `test_title_theme_returns_default_tokens`. | SKIN-X4 deve aggiungere smoke visuale `mines_classic` senza blocco `skin`. |
| Target CSS area gioco | SI | Runtime usa `<article className="board-shell mines-stage-board">`. | `game_area_background` deve agganciarsi a `.mines-stage-board`. |
| Rail parametri separato | SI | Runtime usa `.mines-control-rail`; header usa `.mines-stage-card`. | Lo sfondo non deve finire su rail/header/modali/replay. |
| WCAG contrast check | NO | Nessun validator contrasto trovato per theme/skin. | Da implementare prima del publish UI SKIN-X3/X4. |
| Button preset skin | NO | Nessun `button_density`, `button_radius`, `button_style`, `button_emphasis` nel codice. | SKIN-X1 deve introdurre enum, non CSS value liberi. |
| Master read-only per theme/assets | SI | Route admin asset/theme chiamano `ensure_title_is_mutable`. | La nuova UI deve mantenere lo stesso vincolo. |

## Decisioni tecniche per SKIN-X1

1. Estendere `title_assets` con migration non distruttiva.

   Nuovi kind:

   - `title_logo`
   - `game_area_background`
   - `cell_face_down_background`

   Legacy:

   - `logo` e `background` restano leggibili.
   - `symbol_safe` e `symbol_mine` restano invariati.
   - Nessuna migration cancella o converte asset esistenti.

2. Passare da validator immagine globale a validator per-kind.

   Regole richieste:

   | Kind | MIME V1 | Cap V1 |
   | --- | --- | --- |
   | `title_logo` | PNG/WebP | 150 KB |
   | `game_area_background` | PNG/WebP | 400 KB |
   | `cell_face_down_background` | PNG/WebP | 256 KB |

   SVG resta consentito solo dove gia' esiste legacy, non nei nuovi kind skin.

3. Aggiornare `theme_service.py` senza far entrare oggetti nested in React style.

   Persistenza:

   - `theme_tokens_json` resta source of truth.
   - Puo' contenere una sezione `skin` strutturata e validata.

   Payload pubblico:

   - `tokens` deve restare `Record<string, string>` con sole CSS variables finali.
   - eventuali informazioni semantiche devono stare in un campo tipizzato
     separato, non dentro `tokens`.

4. Mantenere i fallback default.

   Title senza `skin` deve comportarsi come oggi. Il test API default esiste, ma
   manca ancora lo smoke visuale desktop/mobile su `mines_classic` master.

5. Separare la nuova UI skin dal pannello legacy Board assets.

   Il pannello legacy oggi parla di "SVG o PNG" e applica 150 KB. La skin estesa
   deve avere copy, accept MIME e limiti propri: PNG/WebP, cap V1 per-kind.

6. Applicare `game_area_background` solo al container confermato.

   Target:

   ```text
   article.board-shell.mines-stage-board
   ```

   Non target:

   - `.mines-control-rail`
   - `.mines-stage-card`
   - modali rules/replay
   - lobby

7. Aggiungere test mirati.

   Minimo SKIN-X1:

   - migration accetta i nuovi kind;
   - upload `title_logo` PNG/WebP ok;
   - upload SVG su `title_logo` rifiutato;
   - upload `game_area_background` sopra 400 KB rifiutato;
   - legacy `logo`/`background` leggibili nel public theme assets;
   - theme validator accetta `skin` enum validi e rifiuta CSS arbitrario;
   - public `tokens` resta flat;
   - audit log asset/theme resta presente.

## Rischi rilevati

| Rischio | Valutazione | Mitigazione |
| --- | --- | --- |
| SVG legacy senza sanitizer | Reale, ma pre-esistente. | Non estenderlo ai nuovi kind; V2 SVG solo con piano sicurezza. |
| WebP non supportato da title registry | Blocco tecnico SKIN-X1. | Aggiungere `image/webp` per nuovi kind skin. |
| `skin` annidato dentro `tokens` React | Rischio di bug frontend. | Resolver pubblica solo CSS variables finali in `tokens`. |
| Default skin regressiva | Rischio prodotto alto. | Smoke obbligatorio `mines_classic` senza blocco `skin`. |
| Limiti asset incoerenti fra legacy e skin | Rischio UX/backoffice. | UI skin separata dal pannello board assets legacy. |

## Go / No-Go

SKIN-X0 e' chiuso.

Go per SKIN-X1 con questi no-go interni:

- non aggiungere SVG ai nuovi kind;
- non salvare valori CSS liberi per button styling;
- non pubblicare nested object dentro `tokens`;
- non migrare o cancellare asset legacy;
- non applicare background fuori da `.mines-stage-board`.
