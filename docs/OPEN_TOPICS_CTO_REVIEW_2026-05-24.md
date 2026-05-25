Status: ACTIVE
Last meaningful update: 2026-05-24

# Open Topics - CTO Review 2026-05-24

Scope: triage dei temi segnalati dopo la chiusura operativa HI-LO: finance/replay,
CMS v2 e moltiplicatore corrente HI-LO.

## Executive Verdict

I tre temi sono separabili e lavorabili in parallelo, ma non hanno la stessa
criticita'.

| Stream | Priorita' CTO | Verdetto | Prossima azione |
| --- | --- | --- | --- |
| Finance / replay / retention | P0 | Gap piattaforma reale: player account e backend sono piu' avanti dell'admin finance. | Audit+fix registry replay multi-gioco, poi retention policy. |
| CMS v2 | P1 deferred | Non continuare acriticamente: ci sono artefatti lab e codice non ancora integrato in modo pulito. Michele ha chiesto di parlarne dopo. | Rescue audit futuro: salvare, cestinare o rifare. |
| HI-LO moltiplicatore corrente | P2 | Feature UX locale, dati server gia' disponibili. | Implementazione piccola con layout stabile desktop/mobile. |

## Stream A - Finance / Replay / Retention

### Finding

Il player account supporta replay per tutti e tre i giochi:

- `frontend/app/ui/player-account-page.tsx:11-19` importa Mines, BOXE e HI-LO replay viewer.
- `frontend/app/ui/player-account-page.tsx:729-736` renderizza viewer game-specific.
- `frontend/app/ui/player-account-page.tsx:1636-1643` risolve endpoint Mines, BOXE e HI-LO.

Il backend espone endpoint admin replay per tutti e tre:

- Mines: `backend/app/api/routes/mines.py:801-809`
- BOXE: `backend/app/api/routes/boxe.py:225-233`
- HI-LO: `backend/app/api/routes/hi_lo.py:253-261`

Il pannello finance admin invece e' parziale:

- `frontend/app/ui/admin-finance-panel.tsx:7-10` importa solo BOXE e HI-LO.
- `frontend/app/ui/admin-finance-panel.tsx:76` tipizza solo `BoxeRoundReplay | HiLoRoundReplay`.
- `frontend/app/ui/admin-finance-panel.tsx:540` abilita replay solo per `boxe` e `hi_lo`.
- `frontend/app/ui/admin-finance-panel.tsx:614-618` usa fallback implicito a BOXE per ogni gioco non HI-LO.

### CTO Risk

Il fallback a BOXE e' il punto pericoloso: quando entra un nuovo gioco, se il
codice dimentica la branch esplicita, rischia di chiamare un endpoint sbagliato
invece di disabilitare la funzione. Questo e' un bug di piattaforma, non solo
una mancanza UI.

### Required Fix Direction

1. Estrarre o introdurre un registry replay admin/player:
   `game_code -> endpoint builder -> viewer`.
2. Rimuovere fallback impliciti: gioco non registrato = replay non disponibile
   con messaggio chiaro.
3. Aggiungere Mines nel finance admin usando l'endpoint admin gia' esistente.
4. Verificare end-to-end:
   - player account replay Mines/BOXE/HI-LO;
   - admin finance replay Mines/BOXE/HI-LO;
   - round/session details e importi ledger coerenti.
5. Separare retention DB da retention UI:
   - ledger finanziario: non si cancella come "replay";
   - replay payload/audit: conservazione da decidere prima della produzione;
   - UI backoffice: paginazione/limite di lista non e' retention legale.

Il contratto strutturale e' ora in
`docs/GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md` e deve diventare
input obbligatorio per il prossimo gioco.

### CTO Decision

Aprire WP dedicato prima del prossimo gioco:

`WP-FINANCE-REPLAY-REGISTRY-RETENTION`

Parte A doc/audit breve, Parte B fix registry + Mines admin replay + policy
retention MVP. Non fare cancellazioni fisiche finche' non c'e' una decisione
legale/prodotto.

## Stream B - CMS v2

Status product 2026-05-24: deferred. Non iniziare codice o rescue operativo
finche' Michele non riapre esplicitamente il tema sito/CMS.

### Finding

Il CMS v2 e' ancora un laboratorio, non una feature pronta:

- `docs/CMS_V2_MODULE_COMPOSER_PLAN.md:21-27` dichiara che builder e sito v2
  sono invertiti: il builder sta in `frontend-v2`, mentre dovrebbe stare dentro
  l'admin su porta 3000.
- `backend/app/api/routes/cms_v2.py:11-63` espone CRUD e publish CMS v2, ma con
  logica ancora minimale.
- `backend/app/modules/platform/cms_v2/service.py:72-119` salva il draft
  cancellando e reinserendo i moduli della pagina.
- `frontend-v2/app/page.tsx:181-252` e' esplicitamente un `CMS v2 / Module
  Composer Lab`.
- `frontend-v2/app/lib/modules/registry.ts:48-119` contiene un registry moduli
  utile, ma ancora piccolo e lab-oriented.
- `frontend-v2/` contiene anche `.next` e `node_modules`, quindi l'artefatto non
  va accettato in repo cosi' com'e'.

### CTO Risk

Il rischio non e' che il CMS v2 sia inutile. Il rischio e' continuare sopra una
base con confini sbagliati:

- builder nella app sbagliata;
- sito player v2 non ancora separato;
- publish/draft troppo grezzo;
- dependency/build artifacts dentro al materiale non tracciato;
- nessuna definizione finale del perimetro CMS.

### Required Fix Direction

1. Freeze: niente nuovo codice CMS v2 finche' non si decide perimetro.
2. Rescue audit:
   - cosa si salva: registry, picker/editor, preview?
   - cosa si butta: build artifacts, app lab se incompatibile;
   - cosa si rifà: integrazione admin 3000 e sito player 3001.
3. Definire perimetro minimo:
   - homepage/lobby modulare;
   - global layout;
   - asset/media;
   - preview draft;
   - publish live;
   - rollback/versioning, se serve.
4. Solo dopo: migrazione pulita dentro `frontend/app/ui/admin/site-v2`.

### CTO Decision

Aprire:

`WP-CMS-V2-RESCUE-SCOPE`

Questo WP deve essere doc-first e severo. Se l'audit dice "rifare", si rifà:
non si porta avanti roba Gemini solo perche' esiste.

## Stream C - HI-LO Current Multiplier

### Finding

Il dato esiste gia' nel contratto runtime:

- `frontend/app/ui/hi-lo/use-hi-lo-runtime.ts:69-70` espone
  `multiplier_current` e `payout_current`.
- `backend/app/modules/games/hi_lo/service.py:763-765` li restituisce nella
  response server-authoritative.
- `frontend/app/ui/hi-lo/hi-lo-gameplay.tsx:172` legge gia'
  `payout_current`, ma non lo mostra come informazione primaria.
- La roadmap HI-LO registra il bisogno a
  `docs/games/hi-lo/HI_LO_GAMEPLAY_UX_AND_RECOVERY_ROADMAP_2026-05-23.md:19`
  e impone slot stabile a `:79`.

### CTO Risk

Rischio basso, ma va fatto bene: se il badge compare/scompare e muove carta o
bottoni, reintroduce il difetto gia' corretto sul rebet. Deve avere spazio
riservato sempre.

### Required Fix Direction

1. Aggiungere un badge/pannello stabile nella sola area HI-LO gameplay.
2. Mostrare:
   - moltiplicatore corrente, es. `Moltiplicatore 2.30x`;
   - vincita corrente potenziale, es. `Incasso 11.50 CHIP`;
   - stato vuoto pre-hand, es. `1.00x / 0.00 CHIP` o copy equivalente.
3. Usare solo dati backend: `round.multiplier_current`, `round.payout_current`,
   `bet_amount` per fallback pre-hand.
4. Gate visual:
   - desktop 1365x768;
   - mobile 390x844;
   - terminal rebet visibile senza layout shift.

### CTO Decision

Aprire:

`WP-HILO-CURRENT-MULTIPLIER-BADGE`

Questo puo' andare in parallelo al rescue audit CMS e all'audit Finance, perche'
tocca solo HI-LO gameplay.

Nota implementativa: il badge deve essere gradevole ma conservativo. Non deve
spostare carta, prediction controls, skip, incassa o rebet; usare spazio
riservato e dati server-authoritative.

## Parallelization Plan

| WP | Parallelizzabile | Note |
| --- | --- | --- |
| WP-FINANCE-REPLAY-REGISTRY-RETENTION | Si, con attenzione | Tocca admin finance/player account/forse registry shared. Non deve toccare CMS o HI-LO gameplay salvo viewer import. |
| WP-CMS-V2-RESCUE-SCOPE | Si | Doc/audit first. Non toccare produzione finche' non si decide il perimetro. |
| WP-HILO-CURRENT-MULTIPLIER-BADGE | Si | Piccolo, locale HI-LO. Deve fare build e screenshot. |

## CTO Review

La priorita' vera e' Finance/Replay, non perche' sia piu' visibile, ma perche'
tocca soldi, audit e verificabilita' delle sessioni. Il fatto che il player
account abbia Mines/BOXE/HI-LO e l'admin finance no e' un classico segnale di
feature cresciuta per aggiunte successive invece che per registry di piattaforma.

Il CMS v2 va trattato con freddezza: c'e' materiale probabilmente recuperabile,
ma oggi il confine architetturale e' sbagliato. Portarlo avanti senza rescue
audit rischia di creare un secondo backoffice parallelo.

Il moltiplicatore HI-LO e' una correzione di esperienza: importante per Michele,
ma non deve bloccare il lavoro di piattaforma. Va fatto presto, piccolo e con
gate visual, non trasformato in redesign.

## Recommended Next Step

Procedere in parallelo con:

1. `WP-FINANCE-REPLAY-REGISTRY-RETENTION` - audit/fix P0.
2. `WP-CMS-V2-RESCUE-SCOPE` - doc-only rescue decision.
3. `WP-HILO-CURRENT-MULTIPLIER-BADGE` - implementazione UX piccola.

Se bisogna sceglierne uno solo da fare per primo: Finance/Replay.
