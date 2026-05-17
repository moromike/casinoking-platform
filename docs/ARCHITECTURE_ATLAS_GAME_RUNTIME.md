Status: ACTIVE
Last meaningful update: 2026-05-16

# CasinoKing - Architecture Atlas Game Runtime

Mappa operativa del runtime frontend comune che permette a un gioco proprietario
di partire senza copiare il wrapper di Mines.

## Stato

- Tipo: atlas operativo.
- Stato: attivo dopo BOOT-2A.6.
- Ambito: frontend Game Boot Shell, helper route/storage, launch context, audio
  preferences e checklist per il secondo gioco.
- Non sostituisce: `docs/GAME_ARCHITECTURE_OVERVIEW.md`,
  `docs/ARCHITECTURE_ATLAS_MINES.md`, `docs/SOURCE_OF_TRUTH.md` o i documenti
  canonici Word.

## Confine

Questo atlas descrive il runtime frontend comune. Non descrive il Game Runtime
Layer backend/platform, che resta il dominio di launch token, access session,
table session, platform rounds e settlement.

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

## File Runtime Comuni

| Blocco | Responsabilita' | File |
| --- | --- | --- |
| Route boot request | Legge e normalizza `title_code`, `mode=demo`, `preview`, `embed` e `wallet_source` dalla URL. | `frontend/app/ui/game-runtime/game-boot-request.ts` |
| Storage boot | Incapsula localStorage legacy con namespace gioco, senza rinominare chiavi esistenti. | `frontend/app/ui/game-runtime/game-storage.ts` |
| Launch context | Espone lo stato boot/launch/runtime/fatal e le transizioni minime per montare il gameplay solo quando pronto. | `frontend/app/ui/game-runtime/use-game-launch-context.ts` |
| Boot shell visuale | Avvolge il gioco con theme provider, table gate, provider intro, how-to-play, overlay runtime e mount del gameplay. | `frontend/app/ui/game-runtime/game-boot-shell.tsx` |
| Decision flow visuale | Orchestration visuale comune del flow Table Balance Gate -> Provider Intro -> How To Play -> gameplay. Riceve dal wrapper gioco solo booleans, ReactNode e callback gia' incapsulate nei nodi specifici. | `frontend/app/ui/game-runtime/game-boot-decision-flow.tsx` |
| Audio preferences | Gestisce preferenze FX comuni (`ck.audio.effectsMuted`) e volume runtime esposti al gioco. | `frontend/app/ui/game-runtime/use-game-audio-preferences.ts` |

Il runtime comune non deve importare file `frontend/app/ui/mines/*`.
BOOT-2A.6 aggiunge un test contract dedicato per questo confine.

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

BOOT-2A.6 estrae il decision flow visuale in `game-runtime/` con boundary
approvato dal CTO:

- componenti comuni: `GameBootDecisionFlow`, `GameProviderIntroGate`,
  `GameTableBalanceGate`, `GameHowToPlayGate`;
- `GameHowToPlayGate` usa il suffisso `Gate` per coerenza con gli altri passi,
  perche' blocca il gameplay finche' il player non prosegue;
- il wrapper gioco resta responsabile di stato specifico, copy, contenuti,
  table session API e callback;
- il runtime comune riceve booleans e `ReactNode`, non conosce Mines;
- nessuna responsabilita' su wallet, ledger, RNG, payout, fairness o math.

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

## Decision Flow Estratto

Il decision flow visuale Balance Gate / Intro / How To Play e' stato estratto in
BOOT-2A.6 con boundary conservativo. La shell comune decide solo quale superficie
visuale montare; Mines continua a calcolare booleans, stato, copy, contenuti e
callback specifiche. Questo evita astrazioni su table session, wallet source,
copy Mines o gameplay.

## Checklist Per `NewGameStandalone`

Usare questa checklist quando Michele autorizzera' un secondo gioco proprietario.

1. Aprire un piano dedicato per il nuovo gioco. Non iniziare codice solo perche'
   BOOT-2A e' chiuso.
2. Creare un wrapper `NewGameStandalone` specifico del gioco, senza copiare
   `MinesStandalone`.
3. Usare `readGameBootRequestFromLocation` tramite `useGameLaunchContext`.
4. Definire namespace storage del nuovo gioco e preservare eventuali chiavi
   legacy se il gioco ne avra'.
5. Montare `GameBootShell` e passare table gate, provider intro, how-to-play,
   error dialog, runtime overlay e gameplay come superfici del nuovo gioco.
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
14. Aggiornare questo atlas e l'atlas del nuovo gioco se nascono nuove
    responsabilita' comuni.

## Cross Reference

- Mines runtime concreto: `docs/ARCHITECTURE_ATLAS_MINES.md`.
- Overview Platform/Game: `docs/GAME_ARCHITECTURE_OVERVIEW.md`.
- Debiti post BOOT-2A: `docs/MINES_PENDING_TOPICS.md`.
