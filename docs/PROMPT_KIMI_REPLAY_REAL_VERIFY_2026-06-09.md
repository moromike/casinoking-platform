# PROMPT KIMI — Giro verifica REPLAY a denaro reale (3 giochi)

> Incollare in KIMI. **Solo VERIFICA visiva, NIENTE modifiche di codice/commit.** Frontend su `:3000` (main). Gate CTO sulle evidenze.

## Obiettivo
Aprire il replay di un round **REALE (denaro reale, NON demo)** per ciascun gioco (Mines / BOXE / HI-LO) e verificare che renda correttamente. Uno screenshot per gioco.

## SEMPLIFICAZIONI (vincolanti — NON trasformarlo in un progetto)
- Usa il **percorso più breve** per arrivare a un replay reale. Se in DB locale esistono già round reali (da smoke/partite precedenti), **apri quelli, non rigiocare**.
- **BOXE: basta UNO screenshot** del replay reale. NON replicare la sequenza/piramide.
- Se per un gioco non esiste un round reale e crearne uno richiede setup non banale → **NON costruire infrastruttura**: segna quel gioco come **DEBITO** ("replay reale non verificato: serve round reale") e vai avanti.
- Tetto di sforzo ragionevole. Se balloon → debito e stop, non insistere.

## Check per gioco
- **MINES (priorità — Michele sospetta clipping):** il replay/board è **TAGLIATO/clippato**? Misura il clipping del contenitore board (bounding box, `overflowX`/`overflowY`, scrollbar, celle tagliate ai bordi). Screenshot.
- **BOXE:** uno screenshot del replay reale; conferma render corretto (piramide non clippata, celle a dimensione, non a contenuto).
- **HI-LO:** screenshot del replay reale; sanity (carte/importi/moltiplicatore corretti, non clippati).

## Vincoli
- **Verifica, non fix.** Se trovi un bug **NON correggerlo**: riportalo con screenshot + `file:line` sospetto; lo valuta il CTO.
- Nessuna modifica di codice, nessun commit. (`git status` deve restare pulito sul tracked.)
- Replay **REALE**, non demo: usa un round con wallet reale (player loggato), non un round demo/anonimo.

## Output (auto-attestazione)
1. Per ciascun gioco: **screenshot del replay reale** + verdetto **OK** / **ISSUE**(descrizione) / **DEBITO**(motivo).
2. **MINES:** misura DOM esplicita del clipping (box board, `overflowX/Y`, scrollbar, celle ai bordi) + verdetto **tagliato sì/no**.
3. Come hai raggiunto il replay reale (round esistente vs round creato) per ciascun gioco.
4. Conferma: nessuna modifica di codice, nessun commit.

**Clausola forzante:** ogni evidenza esplicita. Se manca lo screenshot reale di un gioco → dichiaralo **DEBITO**, non spacciare done. NON ballonare: sforzo ragionevole, poi debito.
