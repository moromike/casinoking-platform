# Regole Progetto - Architect

## Gerarchia delle fonti (da SOURCE_OF_TRUTH)
1. File Word in `docs/word/` -> documenti canonici
2. File in `docs/runtime/` -> allegati operativi vincolanti
3. File .md in `docs/md/` -> mirror operativi (fedeli ai Word, non riassunti liberi)
4. Se due fonti in conflitto -> vale la versione piu' recente e piu' specifica

## Documenti da leggere PRIMA di ogni analisi
1. `docs/SOURCE_OF_TRUTH.md`
2. `docs/TASK_EXECUTION_GUARDRAILS.md`
3. `docs/PROJECT_STATUS_2026_03_30.md` (per lo stato attuale)

## Documenti per dominio
- **Financial core**: Documento 05 v3, 11 v2, 12 v3, 13 v3
- **Mines**: Documento 06, 07 v2, allegati runtime, 08 v2, 09 v2, 10
- **Infra**: Documento 14 v2
- **Execution**: Documento 15

## Vincoli architetturali non negoziabili
- Ledger = fonte contabile primaria (double-entry)
- Wallet = snapshot materializzato (non puo' divergere dal ledger in un commit)
- Mines = server-authoritative (frontend non decide outcome)
- Payout runtime = derivano da docs/runtime/
- MVP = polling, non WebSocket
- Separazione netta piattaforma/gioco (round_gateway e' l'unico ponte)

## Formato output
Ogni piano o analisi DEVE includere:
1. Contesto e obiettivo
2. Stato attuale vs stato target
3. Piano di azione con task granulari
4. Rischi e mitigazioni
5. Indicazione se serve validazione Ask
6. TODO list per Code (se applicabile)
