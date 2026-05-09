# Mines Visual Effects Plan

Documento di progetto per effetti visuali client-side in Mines.

## Stato

- Tipo: piano operativo Mines UX.
- Stato: VF-1/VF-2 implementate; VF-3 rinviata.
- Ambito: confetti/win effect, safe sparkle, mine burst, motion safety.
- Non sostituisce: `docs/ARCHITECTURE_ATLAS_MINES.md`, `docs/MINES_SOUND_ASSETS_PLAN.md`.

## Obiettivo

Aggiungere feedback visivo piu' soddisfacente senza toccare outcome, RNG, payout o settlement.

Effetti candidati:

| Evento | Effetto |
| --- | --- |
| Safe reveal | sparkle leggero sulla cella |
| Mine hit | burst/pulse danger sobrio |
| Collect/win | confetti o celebratory overlay breve |

## Decisione Tecnica

Gli effetti sono presentazionali e client-side.

Non devono:

- modificare `currentSession`;
- decidere outcome;
- cambiare reveal positions;
- ritardare settlement;
- bloccare cashout o refresh;
- ritardare il `setState` del reveal o lo sblocco del prossimo click.

## Aggiornamento 2026-05-09

Implementato:

- `MinesWinCelebration` per confetti leggero su cashout riuscito e auto-win;
- sparkle CSS sulla cella safe appena rivelata;
- pulse danger CSS sulla mina appena colpita;
- `prefers-reduced-motion`;
- overlay `pointer-events: none`;
- nessun cambio a backend, API, RNG, payout, wallet, ledger o settlement.

Resta fuori scope:

- VF-3 asset-based effects;
- configurazione effetti da backoffice.

Regola hard:

- l'animazione gira su layer separato, con CSS `transform`/`opacity` o canvas;
- non deve causare reflow/layout shift della board;
- non si attende `await` della fine animazione prima di aggiornare stato UI o
  permettere la prossima interazione valida.

## Slice VF-1 - Win Confetti

Stato: implementata.

Scope:

- effetto dopo `cashout` riuscito;
- effetto anche su round `won` automatico quando tutti i safe sono stati
  rivelati;
- durata breve;
- nessun suono incluso in questa slice;
- rispettare `prefers-reduced-motion`;
- non coprire bottoni critici dopo la fine dell'animazione.

Implementazione preferita:

- componente `MinesWinCelebration`;
- CSS/Canvas leggero;
- no libreria pesante salvo vantaggio evidente;
- montato dentro `MinesStandalone`.

## Slice VF-2 - Cell Effects

Stato: implementata.

Scope:

- safe reveal sparkle su cella appena rivelata;
- mine hit pulse quando si perde;
- animazioni CSS leggere;
- nessun asset esterno obbligatorio.

Nota:

- il comportamento gia' corretto "clic mine -> mostra tutte le mine subito" resta separato dalla grafica. Non va reintrodotto un delay che sembri tremolio.

## Slice VF-3 - Asset-Based Effects

Stato: rinviata.

Solo se serve piu' qualita':

- `effect_safe_sparkle`;
- `effect_mine_burst`;
- `effect_win_confetti`.

Questi potrebbero entrare in asset registry, ma non li aprirei subito: prima CSS/canvas.

## Out Of Scope

- animazioni che cambiano tempi di reveal lato server;
- WebSocket;
- effetti 3D pesanti;
- particelle continue;
- effetti configurabili da backoffice nella prima slice.

## Rischi

| Rischio | Mitigazione |
| --- | --- |
| UI piu' bella ma meno chiara | Animazioni brevi e leggibili. |
| Performance mobile | CSS/canvas leggero, test 375px. |
| Motion discomfort | `prefers-reduced-motion`. |
| Stato incoerente | Effetti derivano solo da stato gia' confermato dal backend. |

## Verifiche

- demo safe reveal;
- demo mine hit;
- demo collect/win;
- mobile 375px;
- `prefers-reduced-motion`;
- nessun overlap con popup errori;
- `npx tsc --noEmit`;
- `npm run build`.

## Criteri Di Accettazione

- Effetto win visibile ma non invadente.
- Effetto loss non sembra glitch o tremolio.
- Il player capisce subito cosa e' successo.
- Nessun cambio a API, payout, RNG, wallet o ledger.
