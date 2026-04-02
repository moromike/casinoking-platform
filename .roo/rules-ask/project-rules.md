# Regole Progetto - Ask (CTO Review)

## Criteri di validazione CasinoKing

### 1. Coerenza documentale
- Tutto deve essere allineato a `docs/SOURCE_OF_TRUTH.md`
- Le regole di `AGENTS.md` sono vincolanti
- `docs/TASK_EXECUTION_GUARDRAILS.md` e' la checklist finale obbligatoria

### 2. Integrita' finanziaria
- Il ledger e' SEMPRE la fonte contabile primaria
- Il wallet usa snapshot materializzato
- Ledger e snapshot non possono divergere in un commit riuscito
- Il modello e' double-entry con piano dei conti (`ledger_accounts`)
- Endpoint finanziari -> idempotenza e coerenza transazionale

### 3. Integrita' Mines
- Server-authoritative: il frontend NON decide outcome, board o payout
- I payout runtime derivano da `docs/runtime/`
- RTP deve restare > 90% e < 100% nelle configurazioni supportate
- Per il MVP: polling/request-response, non WebSocket

### 4. Confine piattaforma/gioco
- `round_gateway.py` e' l'unico punto di contatto
- Test di confine: `test_boundary_imports.py` + `test_round_gateway_contract.py`
- Nessun import diretto tra platform e games

### 5. Soglie di severita'
- BLOCCANTE: violazione modello finanziario, rottura server-authority, bypass ledger
- IMPORTANTE: test mancanti su aree sensibili, coupling non necessario
- MINORE: naming, stile, opportunita' di refactoring
