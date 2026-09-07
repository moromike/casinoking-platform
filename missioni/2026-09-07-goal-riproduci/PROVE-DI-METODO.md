# Le due prove di metodo, prima della prima corsa GOAL

Sezione 8 del contratto di esecuzione. Fatte il 7/09/2026, prima di lanciare.

## Prova 1 — la modalita' GOAL esiste come l'avevamo ricostruita? SI

Ricostruita dal database di stato e dalle stringhe del binario, senza documentazione.
Digitato `/goal` nella TUI, risposta:

```
Usage: /goal [<objective>|clear|edit|pause|resume]
No goal is currently set.
```

**Parola per parola la riga d'uso prevista dal contratto.** La ricostruzione regge, e
regge anche la tabella dello schema: `thread_goals` ha esattamente le colonne dichiarate
(`thread_id, goal_id, objective, status, token_budget, tokens_used, time_used_seconds,
created_at_ms, updated_at_ms`). La tabella e' **vuota**: nessun obiettivo e' mai stato
creato su questa macchina.

## Prova 2 — Codex arriva ai contenitori? NO, e vale anche per la TUI

Chiesto a Codex (`gpt-5.6-sol`, TUI, dentro `wt-goal-fase9`) di lanciare
`./scripts/ck-test.sh tests/integration/test_seamless_censimento.py -q`.

Risposta ricevuta:

```
[STOP] Lo stack non e' in piedi. Lancia prima ./scripts/ck-up.sh
```

**Ma lo stack era acceso.** Controprova, dalla stessa cartella, senza il suo ambiente
ristretto:

```
2 failed, 1 passed in 0.15s
```

Quindi: lo script funziona dal worktree, e cio' che manca a Codex e' **l'accesso a
Docker**. Il Fatto 2 del contratto — «GOAL non arriva ai contenitori» — vale anche per
la finestra interattiva, non solo per `codex exec`. **Il mandato resta quello scritto:
Codex scrive, la misura la fa chi a Docker ci arriva.**

## Il difetto trovato per caso, e curato subito

Il messaggio che Codex ha ricevuto **era una diagnosi sbagliata**: diceva «lo stack non
e' in piedi, accendilo», mentre lo stack era acceso e il guasto vero era l'accesso.

Non e' una sfumatura: manda a fare la cosa sbagliata. Un motore ubbidiente avrebbe
lanciato `ck-up.sh` su uno stack gia' in piedi, invece di dire «io a Docker non ci
arrivo» — e avremmo passato la serata a cercare un guasto nello stack.

`ck-test.sh` ora distingue i due guasti: prima chiede se Docker risponde, poi se lo stack
e' acceso. Entrambi i rami provati.

**E' il tipo di difetto che si trova solo mandando un agente ristretto a sbatterci
contro.** Non lo avrebbe trovato nessuna lettura del codice: dal terminale di casa quel
ramo non si percorre mai.
