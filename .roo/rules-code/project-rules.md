# Regole Progetto - Code

## Stack tecnico
- **Backend**: Python 3.11+, FastAPI, PostgreSQL, SQLAlchemy
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Test**: pytest (backend) - struttura: unit, integration, contract, concurrency
- **Infra**: Docker, docker-compose
- **DB**: PostgreSQL (locale in .local/pgdata)

## File chiave del progetto
### Backend
- `backend/app/modules/auth/service.py` - autenticazione
- `backend/app/modules/wallet/service.py` - wallet operations
- `backend/app/modules/ledger/service.py` - ledger double-entry
- `backend/app/modules/platform/rounds/service.py` - operazioni finanziarie round
- `backend/app/modules/games/mines/service.py` - game engine Mines
- `backend/app/modules/games/mines/round_gateway.py` - adapter piattaforma-gioco
- `backend/app/modules/games/mines/runtime.py` - payout tables runtime
- `backend/app/modules/games/mines/fairness.py` - provably fair
- `backend/app/modules/games/mines/randomness.py` - generazione random

### Frontend
- `frontend/app/ui/casinoking-console.tsx` - shell piattaforma
- `frontend/app/ui/mines/mines-standalone.tsx` - componente principale gioco Mines
- `frontend/app/ui/mines/mines-backoffice-editor.tsx` - editor backoffice
- `frontend/app/lib/types.ts` - tipi condivisi
- `frontend/app/lib/api.ts` - client API condiviso

### Test di confine (DEVONO SEMPRE PASSARE)
- `tests/contract/test_boundary_imports.py`
- `tests/contract/test_round_gateway_contract.py`

## Regola TASK_EXECUTION_GUARDRAILS (riassunto)
- Implementa SOLO cio' che e' richiesto
- NON aggiungere testi, badge, hint, helper copy, label, pulsanti non richiesti
- Se un miglioramento sembra utile ma non e' richiesto: PROPONI, non implementare
- NON mischiare copy, layout, comportamento e architettura in un singolo fix
- NON dichiarare un task concluso senza verifica reale
- Se anche UN punto della checklist non e' rispettato -> task rifiutato, correggi

## Test obbligatori per aree sensibili
Per wallet, ledger, idempotenza, cashout, session state, payout, riconciliazione:
- Scrivi SEMPRE test
- Esegui SEMPRE i test di concorrenza esistenti
- Verifica che `test_boundary_imports.py` passi dopo ogni modifica
- MAI fare shortcut o semplificazioni

## Comandi utili
`cd backend; pytest` - tutti i test
`cd backend; pytest tests/unit/` - solo unit
`cd backend; pytest tests/contract/` - solo contract (confine)
`cd backend; pytest tests/concurrency/` - solo concorrenza
`cd frontend; npm run build` - build frontend
`cd frontend; npm run dev` - dev server frontend

## Guida test utente
Ricorda: Michele non e' un programmatore. Le istruzioni per il test manuale
devono essere scritte come tutorial passo-passo con:
- URL da aprire
- Cosa cliccare
- Cosa aspettarsi
- Come verificare che non ci siano regressioni
