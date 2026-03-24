# CasinoKing – Documento 07 v2

Mines – matematica congelata con policy numerica

## 1. Cosa cambia rispetto alla v1

- Il documento non resta più solo concettuale.
- Viene formalizzata la necessità di una payout table completa per tutte le combinazioni supportate.
- La house edge resta target, ma la matematica di prodotto è separata dalla filosofia UX.

## 2. Decisione

La v2 congela il metodo, i limiti operativi e il formato delle payout tables. I valori finali numerici completi saranno mantenuti in un artefatto tabellare versionato.

- Grid size supportate: 9, 16, 25, 36, 49.
- Mine count ammesso: per v1 prodotto, range configurabile per singola griglia.
- House edge target: 2.0% nominale, con tolleranza per rounding.
- Arrotondamento server-side a 4 decimali per multiplier e a 6 per importi interni.

## 3. Struttura obbligatoria della payout table

| grid_size | mine_count | safe_reveal_n | gross_multiplier | net_multiplier |
| --- | --- | --- | --- | --- |
| 25 | 3 | 1 | 1.1363 | 1.1136 |
| 25 | 3 | 2 | 1.2998 | 1.2738 |
| 25 | 3 | 3 | 1.4948 | 1.4649 |

## 4. Regola di implementazione

- Il backend non calcola payout da formule floating live per ogni chiamata se la table è già congelata.
- La formula serve a generare e validare la table.
- Il runtime usa table versionata per evitare drift numerico e mismatch cross-language.

## 5. Artefatti richiesti

- Tabella completa CSV/JSON versionata nel repository.
- Script di generazione payout da formula.
- Script di validazione edge e monotonicità.
- Test che verificano congruenza tra payout engine e tabella.
