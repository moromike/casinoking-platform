Status: ACTIVE
Last meaningful update: 2026-05-25

# CasinoKing - Architecture Atlas Game Runtime

Mappa operativa del runtime frontend comune che permette a un gioco proprietario
di partire senza copiare il wrapper di Mines.

## Stato

- Tipo: atlas operativo.
- Stato: attivo dopo BOOT-2A.6.
- Ambito: frontend Game Boot Shell, helper route/storage, launch context, audio
  preferences e checklist per ogni nuovo gioco.
- Non sostituisce: `docs/GAME_ARCHITECTURE_OVERVIEW.md`,
  `docs/ARCHITECTURE_ATLAS_MINES.md`, `docs/SOURCE_OF_TRUTH.md` o i documenti
  canonici Word.

## Confine

Questo atlas descrive il runtime frontend comune. Non descrive il Game Runtime
Layer backend/platform, che resta il dominio di launch token, access session,
table session, platform rounds e settlement.

Nota 2026-05-18: il backend platform adapter e' stato reso game-agnostic come
prerequisito BOXE 2D. Le API interne platform round usano ora nomi
`*_game_round_*`, il game launch/table session layer valida `game_code` tramite
whitelist centrale e finance/account statement serializzano da
`platform_rounds.game_code` con extra opzionali per gioco.

Nota 2026-05-18: il frontend game-runtime e' stato reso namespace-agnostic come
prerequisito BOXE 3A. `game-storage.ts` valida i namespace tramite whitelist
`ALLOWED_GAME_NAMESPACES = ["mines", "boxe"]`; Mines conserva le chiavi
localStorage storiche, mentre BOXE usa chiavi dedicate per evitare collisioni.

Regola breve:

```text
Frontend Game Boot Runtime
  route/query, storage locale, stato boot, theme shell, intro/how-to-play,
  preferenze audio e mount del gameplay

Backend Game Runtime Layer
  launch token, access session, table session, platform round e settlement
```

Il frontend boot runtime non possiede wallet, ledger, payout, RNG, fairness o
settlement.

## Backend Adapter Note

Questo documento resta centrato sul frontend runtime, ma il confine con il
backend e' rilevante per ogni nuovo gioco:

| Capability | Contratto corrente |
| --- | --- |
| Whitelist giochi | `backend/app/modules/platform/game_codes.py` espone `ALLOWED_GAME_CODES = ("mines", "boxe")`. |
| Round adapter platform | `backend/app/modules/platform/rounds/service.py` espone API game-agnostic (`open_game_round`, `settle_game_round_win`, `settle_game_round_loss`) e richiede `game_code` esplicito. |
| Launch token | `backend/app/modules/platform/game_launch/service.py` accetta giochi whitelisted e valida title/site contro `engine_code`. |
| Table session | `backend/app/modules/platform/table_sessions/service.py` conserva lifecycle e limiti esistenti, ma non blocca piu' i giochi diversi da Mines se whitelisted. |
| Finance/account statement | I report leggono sempre `platform_rounds.game_code`; gli extra game-specific sono opzionali e dispatchati per gioco. |

Regola per i prossimi giochi: prima della Fase 2 va verificato che il gioco sia
supportabile dal platform adapter game-agnostic senza nuovi campi shared o
mutazioni dirette wallet/ledger.

## File Runtime Comuni

| Blocco | Responsabilita' | File |
| --- | --- | --- |
| Route boot request | Legge e normalizza `title_code`, `mode=demo`, `preview`, `embed` e `wallet_source` dalla URL. | `frontend/app/ui/game-runtime/game-boot-request.ts` |
| Storage boot | Incapsula localStorage legacy con namespace gioco, senza rinominare chiavi esistenti. | `frontend/app/ui/game-runtime/game-storage.ts` |
| Launch context | Espone lo stato boot/launch/runtime/fatal e le transizioni minime per montare il gameplay solo quando pronto. | `frontend/app/ui/game-runtime/use-game-launch-context.ts` |
| Embed bridge | Gestisce il contratto postMessage game-agnostic per iframe host: close e fullscreen-state, con compat legacy Mines. | `frontend/app/ui/game-runtime/use-game-embed-bridge.ts` |
| Boot shell visuale | Avvolge il gioco con theme provider, table gate, provider intro, how-to-play, overlay runtime e mount del gameplay. | `frontend/app/ui/game-runtime/game-boot-shell.tsx` |
| Decision flow visuale | Orchestration visuale comune del flow Table Balance Gate -> Provider Intro -> How To Play -> gameplay. Riceve dal wrapper gioco booleans, implementazioni shared configurate con contenuti/callback specifiche e superfici runtime residue. | `frontend/app/ui/game-runtime/game-boot-decision-flow.tsx` |
| Provider bootstrap visuale | Implementazione condivisa del provider intro moromike lab: video/poster, preload, progress bar, skip e durata minima. | `frontend/app/ui/game-runtime/game-provider-bootstrap.tsx`, `frontend/app/ui/game-runtime/game-runtime.css` |
| How-to-play visuale | Implementazione condivisa dell'overlay How To Play: panel, grid, step badges, CTA, stacking e CSS; i giochi passano title/intro/cards/visual specifici. | `frontend/app/ui/game-runtime/game-how-to-play-gate.tsx`, `frontend/app/ui/game-runtime/game-runtime.css` |
| Table balance visuale | Implementazione condivisa del gate Table Balance: form, wallet picker, importo, quick chips, metriche, busy/error UI e layout. Il submit resta callback game-specific per preservare lifecycle/API diverse tra giochi. | `frontend/app/ui/game-runtime/game-table-balance-gate.tsx`, `frontend/app/ui/game-runtime/game-runtime.css` |
| Gameplay control rail | Primitive condivise per rail gameplay: settings slot, bet input, quick chips, Bet/Collect, balance/win footer e stack/sheet mobile. I giochi mantengono stato e contenuti specifici via props/children. | `frontend/app/ui/game-runtime/game-control-rail.tsx`, `game-settings-panel.tsx`, `game-bet-panel.tsx`, `game-quick-chips.tsx`, `game-action-buttons.tsx`, `game-balance-footer.tsx`, `game-mobile-control-stack.tsx`, `game-mobile-settings-sheet.tsx`, `frontend/app/ui/game-runtime/game-runtime.css` |
| Game info / rules shell | Overlay dialog condiviso per il pulsante runtime `i`: shell, close, overlay click, tab API e semantica dialog sono comuni; contenuto regole e replay restano adapter game-specific. Mines mantiene output visuale esistente; BOXE usa lo stesso shell con sezioni rules proprie e replay tab collegata al viewer BOXE quando disponibile. | `frontend/app/ui/game-runtime/game-info-rules-modal.tsx`, `frontend/app/ui/mines/mines-rules-modal.tsx`, `frontend/app/ui/boxe/boxe-rules-modal.tsx` |
| Audio preferences | Gestisce preferenze FX comuni (`ck.audio.effectsMuted`) e volume runtime esposti al gioco. | `frontend/app/ui/game-runtime/use-game-audio-preferences.ts` |

Il runtime comune non deve importare file `frontend/app/ui/mines/*` o
`frontend/app/ui/boxe/*`. I giochi non devono importarsi tra loro.
BOOT-2A.6 aggiunge un test contract dedicato per questo confine; BOXE 3A
estende il contract test anche al boundary BOXE.

## Embed Bridge Contract

Dal 2026-05-25 Mines, BOXE e HI-LO consumano lo stesso bridge:

```ts
useGameEmbedBridge({ gameCode, enabled: isEmbeddedView })
```

Contratto host iframe:

| Direction | Message | Payload |
| --- | --- | --- |
| game -> host | `casinoking:game-close` | `{ type, gameCode }` |
| host -> game | `casinoking:game-fullscreen-state` | `{ type, gameCode, active }` |
| legacy compatibility | `casinoking:<game>-close`, `casinoking:<game>-fullscreen-state` | kept for Mines launcher compatibility |

Origin policy: same-origin by default. A third-party host must pass
`embed_origin=<absolute-origin-url>` on the iframe URL so the game can target and
accept the host origin without direct parent DOM access.

## Game Namespace Whitelist

`frontend/app/ui/game-runtime/game-storage.ts` espone:

```ts
export const ALLOWED_GAME_NAMESPACES = ["mines", "boxe"] as const;
export type GameStorageNamespace = (typeof ALLOWED_GAME_NAMESPACES)[number];
```

Regole:

| Namespace | Storage policy |
| --- | --- |
| `mines` | Backward compatible: tutte le chiavi storiche restano identiche. |
| `boxe` | Chiavi dedicate `casinoking.boxe_*` / `ck_boxe_*`, nessuna collisione con Mines. |
| Altro | `getGameStorageKeys(namespace)` deve rifiutare con errore esplicito. |

Audit WP-FRONTEND-GAME-RUNTIME-AGNOSTIC:

| File | Hardcoding game-specific trovato | Azione |
| --- | --- | --- |
| `game-storage.ts` | `MINES_GAME_STORAGE_NAMESPACE`, `MINES_STORAGE_KEYS`, reject di ogni namespace diverso da `mines`. | Refactor whitelist + chiavi BOXE dedicate. |
| `use-game-launch-context.ts` | Nessun hardcoding gioco; usa solo `storageNamespace` ricevuto. | Nessuna modifica. |
| `game-boot-request.ts` | Nessun hardcoding gioco; normalizza query comuni. | Nessuna modifica. |
| `game-boot-shell.tsx` | Nessun hardcoding gioco. | Nessuna modifica. |
| `game-boot-decision-flow.tsx` | Nessun hardcoding gioco. | Nessuna modifica. |
| `game-short-viewport-gate.tsx` | Nessun hardcoding gioco. | Nessuna modifica. |
| `use-game-audio-preferences.ts` | Preferenze audio comuni, nessun hardcoding gioco. | Nessuna modifica. |

Generalization candidate: pre-Fase 3A, la mappatura frontend deve verificare
hardcoding `game-runtime/` per ogni nuovo gioco. Se il namespace o il boot
storage sono accoppiati a un gioco, aprire un WP platform frontend prima della
3A del gioco.

## Game-Agnosticity Audit Pattern

BOXE closure confirms a three-part audit pattern for every new game:

| Audit | Layer | Outcome from BOXE |
| --- | --- | --- |
| Backend platform adapter | Round adapter, launch, table sessions, finance/account serialization | Refactored to `ALLOWED_GAME_CODES` and `*_game_round_*` APIs before BOXE 2D. |
| Frontend runtime storage | `game-runtime/` namespace, storage keys, launch context, boot helpers | Refactored to `ALLOWED_GAME_NAMESPACES` before BOXE 3A. |
| Title Editor shell | Registry, generic editor props, command bar actions, config loading, diagnostics slot | Refactored to engine registry and `EngineEditorProps<TConfig>` before BOXE 4A. |

The Playbook v1 makes these audits mandatory before Phase 2D, Phase 3A and
Phase 4A respectively. If hardcoding is found, open a platform WP before the
game-specific WP consumes the shared layer.

## Contratto Implementato

### `GameBootRequest`

Shape locale implementata:

```ts
type GameBootRequest = {
  titleCode: string;
  forceDemoMode: boolean;
  previewToken: string;
  isEmbeddedView: boolean;
  walletSource: "cash" | "bonus" | null;
};
```

Nota: questa e' la shape reale dopo BOOT-2A.4b, non un invito a introdurre
nuovi tipi. Eventuali estensioni per un secondo gioco richiedono design dedicato.

### `GameBootStatus`

Stati esportati dal launch context:

```ts
type GameBootStatus =
  | { kind: "boot" }
  | ({ kind: "launch_ready" } & GameLaunchContext)
  | ({ kind: "runtime_ready" } & GameLaunchContext)
  | ({ kind: "fatal"; reason: GameBootFatalReason } & Partial<GameLaunchContext>);
```

Transizioni ammesse:

```text
boot -> launch_ready -> runtime_ready
boot -> fatal
launch_ready -> fatal
```

Il gameplay non va montato prima di `runtime_ready`.

### `GameBootRuntime`

`GameBootRuntime` e' il nome documentale del bundle di dati che un wrapper gioco
deve avere pronto prima di montare il gameplay: request normalizzata, storage
snapshot, config runtime, theme shell, stato fatal/overlay e preferenze audio.

BOOT-2A.6 non cambia questo punto: non esiste un tipo codice esportato con
questo nome. Il contratto reale resta quello dei file implementati.

### `GameBootDecisionFlow`

BOOT-2A.6 ha estratto il decision flow visuale in `game-runtime/`; il WP
`WP-PLATFORM-PREGAME-SHELL-EXTRACTION` ha poi promosso le implementazioni
pre-game reali da Mines-local a shared. Boundary approvato dal CTO:

- componenti comuni: `GameBootDecisionFlow`, `GameProviderIntroGate`,
  `GameTableBalanceGate`, `GameHowToPlayGate`;
- `GameHowToPlayGate` usa il suffisso `Gate` per coerenza con gli altri passi,
  perche' blocca il gameplay finche' il player non prosegue;
- il wrapper gioco resta responsabile di stato specifico, copy, contenuti,
  table/session API e callback;
- dopo WP-PLATFORM-PREGAME-SHELL-EXTRACTION Step 1/2/3, provider intro,
  how-to-play e table balance visuale non sono piu' implementazioni
  Mines-local: il runtime comune possiede video intro, overlay how-to,
  layout/CSS e form table balance, mentre i giochi passano contenuti/visual
  specifici e callback di submit;
- nessuna responsabilita' su wallet, ledger, RNG, payout, fairness o math.

Nota 2026-05-19, WP-PLATFORM-PREGAME-SHELL-EXTRACTION Step 1: il provider
intro non e' piu' una implementazione Mines-local. `GameProviderBootstrap`
vive in `game-runtime/` e viene consumato da Mines e BOXE con la stessa sorgente
media moromike lab e lo stesso comportamento video/poster/progress.

Nota 2026-05-19, WP-PLATFORM-PREGAME-SHELL-EXTRACTION Step 2:
`GameHowToPlayGate` ora vive in `game-runtime/` come implementazione visuale
condivisa. Mines e BOXE forniscono contenuti e visual card specifici, ma
overlay, panel, grid, step badge, CTA e CSS sono shared.

Nota 2026-05-19, WP-PLATFORM-PREGAME-SHELL-EXTRACTION Step 3:
`GameTableBalanceGate` ora vive in `game-runtime/` come implementazione visuale
condivisa. Mines passa la callback che conserva il lifecycle completo
`/table-sessions` e `table_session_id`; BOXE passa una callback placeholder
front-end-only fino al WP dedicato `WP-BOXE-TABLE-SESSION-INTEGRATION`.
Il pattern approvato e': shell visual shared, submit lifecycle game-specific.

## Mines Come Primo Adapter

Mines usa il runtime comune cosi':

```text
frontend/app/mines/page.tsx
  -> MinesStandalone
     -> useGameLaunchContext("mines")
     -> GameBootShell
        -> GameBootDecisionFlow
           -> Table Balance Gate real-mode
           -> Provider Intro
           -> How To Play Gate
        -> MinesGameplay
```

`MinesStandalone` resta export pubblico stabile e wrapper Mines-specific. Tiene
orchestrazione API/session/token/config necessaria a Mines.

`MinesGameplay` contiene gameplay, replay, effetti, ladder, audio bridge verso
`useMinesSounds` e interazioni round. Non importa `game-runtime/` e non importa
`@/app/lib/api`.

## BOXE Come Secondo Consumer Verificato

BOXE usa le stesse implementazioni shared di `frontend/app/ui/game-runtime/`:

```text
frontend/app/boxe/page.tsx
  -> BoxeStandalone
     -> useGameLaunchContext("boxe")
     -> GameBootShell
        -> GameProviderBootstrap
        -> GameHowToPlayGate con card/visual BOXE
        -> GameTableBalanceGate con callback BOXE
        -> BoxeGameplay
```

Verifiche chiuse durante BOXE:

| Capability comune | Verifica BOXE |
| --- | --- |
| Namespace storage | `ALLOWED_GAME_NAMESPACES = ["mines", "boxe"]`; BOXE usa chiavi dedicate. |
| Theme runtime | `GameBootShell` carica theme da `title_code`, indipendente dal gioco. |
| Audio preferences | BOXE consuma `useGameAudioPreferences` via callback shell, senza infra nuova. |
| Provider intro | BOXE consuma `GameProviderBootstrap` condiviso con video/poster/progress moromike lab. |
| How-to-play | BOXE consuma `GameHowToPlayGate`; layout/animazioni sono shared, card/visual sono game-specific. |
| Table balance | BOXE consuma `GameTableBalanceGate`; visual/form sono shared, submit resta callback game-specific placeholder fino a `WP-BOXE-TABLE-SESSION-INTEGRATION`. |
| Gate sequencing | BOXE real cash/bonus replica Mines: Table Balance -> Provider Intro -> How-To -> Gameplay. Demo replica Mines demo: Provider Intro -> How-To -> Gameplay, senza table gate pre-game. |
| Rotation gate | BOXE mantiene portrait/mobile e landscape-short gate senza shell edits. |
| Boundary imports | Contract test vieta `game-runtime/* -> boxe/*` e `boxe/* -> mines/*`. |

Il completamento BOXE e il WP shell extraction confermano che la shell e'
game-agnostic non solo nel wrapper boot, theme, audio prefs e routing
title-based, ma anche nelle implementazioni visuali pre-game condivise.

## Decision Flow Estratto

Il decision flow visuale Balance Gate / Intro / How To Play e' stato estratto
in BOOT-2A.6 con boundary conservativo; dopo il WP shell extraction le superfici
pre-game sono implementazioni shared configurate dai giochi. La shell comune
fornisce provider intro, how-to-play layout e table balance visuale. I wrapper
gioco continuano a calcolare booleans, stato, copy, contenuti/visual
game-specific e callback di submit. Questo evita sia fork locali nascosti sia
astrazioni premature su table session, wallet source, copy Mines o gameplay.

## Checklist Per `NewGameStandalone`

Usare questa checklist quando Michele autorizzera' un nuovo gioco proprietario.

1. Aprire un piano dedicato per il nuovo gioco. Non iniziare codice solo perche'
   BOOT-2A e' chiuso.
2. Creare un wrapper `NewGameStandalone` specifico del gioco, senza copiare
   `MinesStandalone`.
3. Usare `readGameBootRequestFromLocation` tramite `useGameLaunchContext`.
4. Definire namespace storage del nuovo gioco e preservare eventuali chiavi
   legacy se il gioco ne avra'.
5. Montare `GameBootShell` e consumare `GameProviderBootstrap`,
   `GameHowToPlayGate` e `GameTableBalanceGate`; passare solo contenuti/visual,
   copy, error dialog, runtime overlay, gameplay e callback specifiche.
6. Caricare config/runtime del gioco solo dopo `launch_ready`.
7. Chiamare `markRuntimeReady` solo quando request, token/sessione e config
   runtime sono coerenti.
8. Montare `NewGameGameplay` solo quando lo status e' `runtime_ready`.
9. Usare le preferenze audio comuni esposte da `GameBootShell`; tenere i suoni
   specifici dentro la cartella del gioco.
10. Vietare import dal nuovo gameplay verso `frontend/app/ui/game-runtime/` se
    trasformano il gameplay in orchestratore boot.
11. Vietare import da `frontend/app/ui/mines/*` nel runtime comune o nel nuovo
    gioco, salvo componenti esplicitamente promossi a libreria comune con piano
    CTO separato.
12. Aggiungere smoke boot minimi: title mancante, title mismatch, demo, real,
    preview token, embed e runtime config lenta.
13. Aggiungere smoke gameplay minimi del nuovo gioco senza toccare wallet,
    ledger, RNG/fairness o payout Mines.
14. Verificare l'hardcoding in `game-runtime/` prima di Fase 3A: namespace,
    storage keys, audio, theme, gates e route helpers non devono nominare il
    gioco precedente.
15. Aggiornare questo atlas e l'atlas del nuovo gioco se nascono nuove
    responsabilita' comuni.

## Cross Reference

- Mines runtime concreto: `docs/ARCHITECTURE_ATLAS_MINES.md`.
- BOXE runtime concreto: `docs/ARCHITECTURE_ATLAS_BOXE.md`.
- Overview Platform/Game: `docs/GAME_ARCHITECTURE_OVERVIEW.md`.
- Debiti post BOOT-2A: `docs/MINES_PENDING_TOPICS.md`.
