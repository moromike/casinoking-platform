# Regole Progetto - Orchestrator

## Progetto: CasinoKing
Piattaforma casino online con giochi proprietari. Mines e' il primo modulo.

## Domini del progetto
- **Platform backend**: wallet, ledger (double-entry), auth, rounds, idempotenza
- **Game backend Mines**: service, runtime, fairness, randomness, round_gateway
- **Frontend**: casinoking-console.tsx (shell), componenti mines in app/ui/mines/
- **Backoffice**: mines-backoffice-editor, admin panel
- **Infra**: Docker, migrations PostgreSQL
- **Test**: unit, integration, contract, concurrency (in /tests/)

## Regole di delega
- Task architetturali o di design -> delega a **Architect**
- Validazione su aree sensibili -> delega a **Ask**
- Implementazione codice -> delega a **Code**
- Domande informative -> delega a **Ask**
- Bugfix semplice e isolato -> puoi delegare direttamente a **Code**

## Aree sensibili (richiedono SEMPRE validazione Ask)
wallet, ledger, idempotenza, cashout, game session state, payout runtime, riconciliazione

## Lingua
- Comunica con Michele SEMPRE in italiano
- I subtask verso gli altri modi possono essere in italiano o inglese
