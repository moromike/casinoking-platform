Status: ACTIVE
Last meaningful update: 2026-05-25

# Prompt Codex - WP-EMBED-MODE-PARITY-BOXE-HILO

Workstream prerequisito a COINS. Chiude il debito embed mode: BOXE e HI-LO
devono raggiungere parità con Mines per supportare embedding in iframe da
sito esterno (non solo CasinoKing).

---

## Prompt da incollare in Codex

```
You are CTO assistant.

Parte A: validate approach, counter-propose if you see a gap.
Parte B: execution starts only after my approval of Parte A.

=== CONTEXT (current state, 2026-05-25) ===

Branch main. Mines, BOXE, HI-LO sono i 3 giochi proprietari deliverati. COINS
è il quarto gioco in Fase 0 (vedi
docs/games/coins/COINS_OPEN_QUESTIONS_2026-05-25.md).

Michele (product owner) ha esplicitato il requisito di autonomia del gioco
nell'iframe:

  "Il gioco include la shell. Se un domani CasinoKing non esisterà ma i
  giochi gireranno in un altro sito, dovrà esserci tutto a partire da DOPO
  il pannello di ingresso coin/valuta: dal launch fino a tutto il gioco con
  il suo iframe (assegnato dal sito nuovo esterno). Il gioco include la
  shell, tutto."

=== DEBITO DA CHIUDERE ===

Verifica codebase 2026-05-25:

**Mines** ha embed mode COMPLETO:
- CSS embed (mines-page-shell-embedded, mines-product-shell-embedded)
- flag isEmbeddedView propagato in mines-standalone.tsx, mines-gameplay.tsx,
  mines-stage-header.tsx
- postMessage handshake con parent:
  - frontend/app/ui/mines/mines-standalone.tsx:63-64 dichiara
    MINES_EMBED_CLOSE_MESSAGE = "casinoking:mines-close" e
    MINES_EMBED_FULLSCREEN_STATE_MESSAGE = "casinoking:mines-fullscreen-state"
  - frontend/app/ui/mines/mines-standalone.tsx:1437-1438 invia close al parent
  - frontend/app/ui/mines/mines-standalone.tsx:491 ascolta fullscreen-state
- casinoking-console.tsx (admin launcher) consuma gli stessi messaggi
  (linee 52-53, 626, 2136)

**BOXE** ha embed mode PARZIALE:
- CSS embed presente ma RIUSA classi Mines (mines-product-shell-embedded
  in boxe.css e boxe-standalone.tsx) — vedi se questo è OK o se serve
  classi BOXE-specific
- flag isEmbeddedView presente (boxe-standalone.tsx:145, boxe-gameplay.tsx:880)
- MANCA: postMessage handshake (close al parent, fullscreen-state listener)

**HI-LO** ha embed mode PARZIALE:
- CSS embed presente con classi proprie (hi-lo-page-shell-embedded,
  hi-lo-product-shell-embedded in hi-lo.css)
- flag isEmbeddedView presente (hi-lo-standalone.tsx:170-171)
- MANCA: postMessage handshake (close al parent, fullscreen-state listener)

=== REQUISITO PRODUCT ===

L'embed mode deve garantire che:
1. Il gioco, una volta lanciato, è autosufficiente nell'iframe assegnato
   dal sito host (CasinoKing o un futuro sito terzo).
2. La shell platform (GameBootShell, gates Provider Intro, How-To,
   Table Balance, Short Viewport, ecc.) vive DENTRO l'iframe del gioco,
   non fuori.
3. La comunicazione gioco ↔ sito host avviene solo via postMessage con
   contratto esplicito (almeno: close, fullscreen-state). Non via direct
   DOM access al parent.
4. Solo il pannello cassiere/valuta (LaunchCashierModal) sta fuori
   dall'iframe, perché è platform-side pre-launch.
5. Da fuori CasinoKing (futuro sito terzo) il gioco deve girare senza
   modifiche allo stesso contratto postMessage.

=== Parte A - OUTPUT ATTESO ===

Produrre documento di audit + piano in
docs/games/coins/EMBED_MODE_PARITY_AUDIT_<DATE>.md con:

1. **Audit attuale.** Per ogni gioco (Mines, BOXE, HI-LO) tabella:
   - CSS embed presente? quali classi?
   - flag isEmbeddedView propagato? a quali componenti?
   - postMessage send (close, fullscreen, altro): presente o no? file:line
   - postMessage receive: presente o no? file:line
   - Shell completa dentro iframe? gates esposti? close button gestito?
   - Header/footer/navigazione platform nascosti in embed? verifica DOM

2. **Contratto postMessage formalizzato.** Definire una versione
   game-agnostic del contratto attuale Mines:
   - eventi outbound: `casinoking:game-close`, `casinoking:game-fullscreen-state`,
     altri da identificare
   - eventi inbound: `casinoking:game-fullscreen-state` (da host),
     altri da identificare
   - chi è "casinoking:" - va rinominato a un namespace neutro per supportare
     siti terzi? Proposta: mantenere "casinoking:" + aggiungere alias o
     wildcard accettato.
   - origin validation policy

3. **Refactor proposto.** Decisione tra:
   - **Opzione A (preferita CTO Claude):** estrarre un hook/helper platform
     `useGameEmbedBridge(gameCode)` in
     `frontend/app/ui/game-runtime/use-game-embed-bridge.ts` che incapsula
     postMessage send/receive game-agnostic. Mines/BOXE/HI-LO/COINS lo
     consumano via prop o context. Niente "if game === mines" nel bridge.
   - **Opzione B:** duplicare la logica Mines in BOXE e HI-LO con
     namespace specifico (`casinoking:boxe-close`, ecc.). Sconsigliata
     perché aumenta debito.

4. **Validazione autonomia gioco.** Per ogni gioco proporre uno smoke test
   browser che:
   - apre il gioco con `?embed=1`
   - verifica che la shell (gates) sia visibile e funzionante nell'iframe
   - verifica che header platform sia nascosto
   - verifica che close button invii postMessage al parent invece di
     navigare
   - verifica che fullscreen-state listener risponda

5. **Rischi e blind spot.** Counter-proposal se vedi che il namespace
   "casinoking:" è bloccante per uso esterno, o che il bridge richiede
   anche eventi non ancora identificati (es. balance update push,
   round-state notify, ecc.).

6. **Stop-and-Ask** se trovi:
   - assunzioni Mines-only nel postMessage handshake che non sopravvivono
     a un sito terzo
   - dipendenze da casinoking-console.tsx (admin launcher) che andrebbero
     rispecchiate in un launcher pubblico generico
   - dipendenze cross-origin non gestite

NON eseguire codice in Parte A. Solo audit e piano.

=== Parte B - SOLO DOPO APPROVAZIONE CTO ===

Implementare il bridge embed game-agnostic:
- creare hook/helper in game-runtime/
- migrare Mines/BOXE/HI-LO a consumare il bridge
- normalizzare CSS embed (decidere se BOXE deve avere proprie classi o
  continuare a riusare quelle Mines)
- aggiungere browser smoke embed per ognuno dei 3 giochi
- aggiornare docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md con contratto
  postMessage formalizzato
- aggiornare docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md nello stesso PR
- aggiornare ACTIVE_OPEN_LOOPS.md per riflettere chiusura debito

=== CAPABILITY MATRIX ATTESA (Parte B) ===

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Game embed bridge - hook platform | n/a | n/a | n/a | n/a | NEW | n/a | NEW | UPDATE | TBD | |
| BOXE embed handshake | n/a | n/a | n/a | n/a | REFACTOR | REFACTOR | NEW | UPDATE | TBD | |
| HI-LO embed handshake | n/a | n/a | n/a | n/a | REFACTOR | REFACTOR | NEW | UPDATE | TBD | |
| Mines embed migration to bridge | n/a | n/a | n/a | n/a | REFACTOR | unchanged | UPDATE | UPDATE | TBD | |
| Browser smoke embed parity | n/a | n/a | n/a | n/a | n/a | n/a | NEW | n/a | TBD | per gioco |

=== VINCOLI HARD ===

- Mines embed mode deve continuare a funzionare identico post-refactor
  (zero behavior change visibile lato Mines).
- Casinoking-console.tsx (admin launcher) deve continuare a funzionare
  identico.
- Nessuna modifica a wallet/ledger/RNG/payout/fairness/math invariants.
- Pattern Rule 18 (no if-game-branch): il bridge deve essere
  game-agnostic, accetta `gameCode` come parametro, non `if game === "mines"`.
- Allineato a feedback_extraction_vs_visual_uniformity: shared component
  extraction è valida solo se il visual/funzionale è identico, non se è
  "container condiviso ma comportamento divergente".

=== INIZIA CON Parte A ===

Esegui l'audit e produci il documento di piano. Stop-and-Ask quando incontri
un gap che richiede decisione CTO o product owner.
```
