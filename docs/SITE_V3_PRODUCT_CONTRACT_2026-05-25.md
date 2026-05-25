Status: ACTIVE
Last meaningful update: 2026-05-25

# Site V3 - Product And Boundary Contract

## 0. Scopo

Site V3 e' un nuovo sito/CMS parallelo al sito attuale, non una patch del V1 e
non una promozione del lab Gemini `frontend-v2`.

Questo documento fissa il contratto prima del codice:

- cosa deve fare V3;
- cosa non deve toccare;
- dove vive il builder;
- dove vive il renderer pubblico;
- quali decisioni product servono prima di implementare.

## 1. Decisione Di Boundary

| Surface | Owner | V3 puo' toccare? | Regola |
| --- | --- | --- | --- |
| Sito player V1 su `:3000` | `frontend/` attuale | No in MVP | Deve restare operativo e regressione zero. |
| Admin/backoffice su `:3000` | `frontend/` attuale | Si' | Qui vive il builder Site V3. |
| Public Site V3 su `:3001` | nuova app `frontend-v3/` | Si' | Qui vive solo il renderer pubblico published-only. |
| Game runtime | Mines/BOXE/HI-LO standalone | No | V3 linka/lancia giochi, non li ingloba. |
| Wallet/ledger/cashier | Platform finance | No | V3 non inventa flussi finanziari. |
| Catalogo giochi | Platform catalog | Consume only | V3 non duplica `game_titles` o pubblicazione lobby. |

## 2. Intento Product

Site V3 deve permettere di costruire e testare un sito casino piu' moderno,
modulare e pubblicabile, senza rompere quello esistente.

Il risultato desiderato non e' "un editor tecnico di moduli", ma:

- un builder admin comprensibile e ordinato;
- un renderer pubblico bello, responsive, da validare a vista;
- moduli riutilizzabili;
- draft/live/publish chiari;
- asset gestiti dal backoffice;
- regole di sicurezza e rollback sufficienti per non avere paura di pubblicare.

## 3. MVP Scope Raccomandato

| Area | Default CTO | Motivazione |
| --- | --- | --- |
| Homepage modulare | Si' | E' la prima superficie pubblica da rifare. |
| Game lobby/library | Si' | Serve testare il sito reale con i giochi pubblicati dal CMS. |
| Header/footer | Si' | Un sito senza shell globale non e' testabile bene. |
| Promo/banner editoriali | Si' | Caso d'uso principale di un CMS casino. |
| Rich text limitato | Si', con sanitizzazione | Serve per piccoli testi, ma e' rischioso se libero. |
| Pagine statiche | Fase 2 | Terms/FAQ/Responsible Gaming possono arrivare dopo MVP. |
| Game detail page | Fase 2 | Utile, ma non blocca homepage/lobby MVP. |
| Login/register/account nuovo | No MVP | Restano V1 per evitare duplicazione auth/player shell. |
| Cashier nuovo | No MVP | Troppo sensibile; link a V1. |
| Game runtime embedded | No | I giochi restano standalone. |
| Multilingua | Data model con `locale` da subito; content MVP solo `it` | Evita refactor DB dopo, ma non blocca il primo visual. |

## 4. Builder Admin

Il builder vive dentro l'admin esistente su `localhost:3000`.

Responsabilita':

- lista pagine Site V3;
- editor pagina;
- module picker;
- module config editor;
- preview draft;
- validation display;
- save draft;
- publish live;
- stato draft/live;
- audit trail leggibile;
- asset picker/upload dove serve.

Non deve:

- aprire un'app esterna con token in query string;
- duplicare login admin;
- usare localStorage come fonte di verita' per privilegi admin;
- pubblicare contenuti non validati;
- confondere draft e live.

## 5. Renderer Pubblico

Il renderer pubblico vive su `localhost:3001`.

Responsabilita':

- leggere solo pagine published;
- renderizzare moduli player-quality;
- essere responsive da MVP;
- linkare giochi tramite routing attuale;
- mostrare fallback puliti se un modulo non e' disponibile;
- non mostrare controlli admin;
- non leggere draft.

Non deve:

- diventare builder;
- accedere ad API admin;
- dipendere da token admin;
- duplicare wallet/login/cashier.

## 6. V1 Isolation Gate

Ogni WP Site V3 deve dichiarare:

```text
V1 isolation impact: none / adapter read-only / requires migration
```

Per MVP sono ammessi solo:

- `none`;
- `adapter read-only`.

`requires migration` blocca il WP e richiede approvazione esplicita.

## 7. Product Owner Gate

Site V3 non puo' diventare green solo perche' builda o perche' i test passano.

Ogni closure deve avere:

- walkthrough builder su `localhost:3000/admin`;
- walkthrough renderer su `localhost:3001`;
- check mobile;
- check che V1 sia ancora raggiungibile e funzionante;
- screenshot evidence pre/post per le superfici toccate.

## 8. Locked Decision Brief

Decisione lockata 2026-05-25 - Michele approved.

| Decisione | Scelta lockata |
| --- | --- |
| Nome pubblico del workstream | Site V3; non usare piu' CMS v2 nei nuovi doc/UI. |
| Builder dentro admin `:3000` | Si', dentro admin esistente. |
| Renderer pubblico `:3001` | Si', nuova app `frontend-v3/`. |
| `frontend-v2/` | Lab temporaneo; cestinato in WP6. |
| Data model | Nuove tabelle `site_v3_pages`, `site_v3_page_versions`, `site_v3_modules`; `cms_v2_*` dormienti. |
| Content pages statiche | Phase 2; MVP resta homepage/lobby. |
| Game detail pages | Phase 2; MVP linka direttamente al gioco. |
| Login/account/cashier | V1 link/route. |
| Multilingua | Model con `locale` da subito; content MVP solo `it`. |
| Moduli MVP | `global_header`, `hero_banner`, `game_grid`, `featured_game`, `promo_band`, `rich_text_safe`, `global_footer`. |
| Versioning | Published snapshot + history list in admin; revert UI Phase 2. |
| Audit | Riusare `admin_audit_events` con `source=site_v3`; no tabella audit dedicata. |

## 9. Stop-Before-Code

Fermarsi prima del codice se:

- qualcuno propone di usare `frontend-v2` come prodotto senza cleanup;
- il builder resta su `:3001`;
- il public renderer legge draft;
- serve toccare wallet/login/account;
- i moduli consentono HTML/JS arbitrario senza sanitizzazione;
- V1 richiede modifiche non read-only;
- qualcuno riapre le decisioni lockate senza nuova approvazione CTO/Michele;
- si tenta di aprire WP2 senza brief Parte A CTO.

## 10. Capability Matrix

| Capability | Contract MVP | Stato |
| --- | --- | --- |
| V1 isolation | obbligatorio | da verificare per WP |
| Builder admin `:3000` | obbligatorio | da implementare |
| Renderer public `:3001` | obbligatorio | da implementare |
| Draft/live separation | obbligatorio | da implementare |
| Published-only public API | obbligatorio | da implementare |
| Module registry | obbligatorio | da progettare |
| Asset governance | obbligatorio per moduli media | da progettare |
| i18n model | obbligatorio nel data model | da progettare |
| Product Owner walkthrough | obbligatorio | gate |
