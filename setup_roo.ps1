# ============================================================
# CasinoKing — Setup Roo Code Configuration
# ============================================================
# Esegui questo script dal terminale di VS Code.
# Assicurati di essere nella root del progetto CASINOKING-PLATFORM.
# ============================================================

Write-Host "=== CasinoKing Roo Code Setup ===" -ForegroundColor Cyan
Write-Host ""

# --------------------------------------------------
# FILE 1: .roo/rules/shared-rules.md
# --------------------------------------------------
$sharedRules = @"
# Regole Condivise - Tutti i Modi

## Progetto
CasinoKing - piattaforma casino online con giochi proprietari.
Repository: casinoking-platform

## Owner
Michele Morotti - CEO, product owner, analista.
Non e' un programmatore. Comunica in italiano. I report e le guide
devono essere comprensibili senza background tecnico profondo.

## Principio fondamentale
Prima di proporre o scrivere codice, leggere SEMPRE:
1. ``docs/SOURCE_OF_TRUTH.md``
2. ``docs/TASK_EXECUTION_GUARDRAILS.md``

## Cosa NON fare MAI
- Inventare requisiti non presenti nei documenti ufficiali
- Semplificare il modello finanziario
- Bypassare wallet/ledger con aggiornamenti diretti di saldo
- Introdurre feature non richieste
- Modificare l'architettura senza motivazione esplicita
- Trattare i documenti metodologici come opzionali

## In caso di dubbio
- Non scegliere arbitrariamente
- Fermati
- Indica quale documento o regola e' in conflitto
- Proponi l'opzione piu' coerente con ``docs/SOURCE_OF_TRUTH.md``
"@
$sharedRules | Out-File -FilePath ".roo\rules\shared-rules.md" -Encoding utf8
Write-Host "[OK] .roo/rules/shared-rules.md" -ForegroundColor Green

# --------------------------------------------------
# FILE 2: .roo/rules-orchestrator/project-rules.md
# --------------------------------------------------
$orchRules = @"
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
"@
$orchRules | Out-File -FilePath ".roo\rules-orchestrator\project-rules.md" -Encoding utf8
Write-Host "[OK] .roo/rules-orchestrator/project-rules.md" -ForegroundColor Green

# --------------------------------------------------
# FILE 3: .roo/rules-architect/project-rules.md
# --------------------------------------------------
$archRules = @"
# Regole Progetto - Architect

## Gerarchia delle fonti (da SOURCE_OF_TRUTH)
1. File Word in ``docs/word/`` -> documenti canonici
2. File in ``docs/runtime/`` -> allegati operativi vincolanti
3. File .md in ``docs/md/`` -> mirror operativi (fedeli ai Word, non riassunti liberi)
4. Se due fonti in conflitto -> vale la versione piu' recente e piu' specifica

## Documenti da leggere PRIMA di ogni analisi
1. ``docs/SOURCE_OF_TRUTH.md``
2. ``docs/TASK_EXECUTION_GUARDRAILS.md``
3. ``docs/PROJECT_STATUS_2026_03_30.md`` (per lo stato attuale)

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
"@
$archRules | Out-File -FilePath ".roo\rules-architect\project-rules.md" -Encoding utf8
Write-Host "[OK] .roo/rules-architect/project-rules.md" -ForegroundColor Green

# --------------------------------------------------
# FILE 4: .roo/rules-ask/project-rules.md
# --------------------------------------------------
$askRules = @"
# Regole Progetto - Ask (CTO Review)

## Criteri di validazione CasinoKing

### 1. Coerenza documentale
- Tutto deve essere allineato a ``docs/SOURCE_OF_TRUTH.md``
- Le regole di ``AGENTS.md`` sono vincolanti
- ``docs/TASK_EXECUTION_GUARDRAILS.md`` e' la checklist finale obbligatoria

### 2. Integrita' finanziaria
- Il ledger e' SEMPRE la fonte contabile primaria
- Il wallet usa snapshot materializzato
- Ledger e snapshot non possono divergere in un commit riuscito
- Il modello e' double-entry con piano dei conti (``ledger_accounts``)
- Endpoint finanziari -> idempotenza e coerenza transazionale

### 3. Integrita' Mines
- Server-authoritative: il frontend NON decide outcome, board o payout
- I payout runtime derivano da ``docs/runtime/``
- RTP deve restare > 90% e < 100% nelle configurazioni supportate
- Per il MVP: polling/request-response, non WebSocket

### 4. Confine piattaforma/gioco
- ``round_gateway.py`` e' l'unico punto di contatto
- Test di confine: ``test_boundary_imports.py`` + ``test_round_gateway_contract.py``
- Nessun import diretto tra platform e games

### 5. Soglie di severita'
- BLOCCANTE: violazione modello finanziario, rottura server-authority, bypass ledger
- IMPORTANTE: test mancanti su aree sensibili, coupling non necessario
- MINORE: naming, stile, opportunita' di refactoring
"@
$askRules | Out-File -FilePath ".roo\rules-ask\project-rules.md" -Encoding utf8
Write-Host "[OK] .roo/rules-ask/project-rules.md" -ForegroundColor Green

# --------------------------------------------------
# FILE 5: .roo/rules-code/project-rules.md
# --------------------------------------------------
$codeRules = @"
# Regole Progetto - Code

## Stack tecnico
- **Backend**: Python 3.11+, FastAPI, PostgreSQL, SQLAlchemy
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Test**: pytest (backend) - struttura: unit, integration, contract, concurrency
- **Infra**: Docker, docker-compose
- **DB**: PostgreSQL (locale in .local/pgdata)

## File chiave del progetto
### Backend
- ``backend/app/modules/auth/service.py`` - autenticazione
- ``backend/app/modules/wallet/service.py`` - wallet operations
- ``backend/app/modules/ledger/service.py`` - ledger double-entry
- ``backend/app/modules/platform/rounds/service.py`` - operazioni finanziarie round
- ``backend/app/modules/games/mines/service.py`` - game engine Mines
- ``backend/app/modules/games/mines/round_gateway.py`` - adapter piattaforma-gioco
- ``backend/app/modules/games/mines/runtime.py`` - payout tables runtime
- ``backend/app/modules/games/mines/fairness.py`` - provably fair
- ``backend/app/modules/games/mines/randomness.py`` - generazione random

### Frontend
- ``frontend/app/ui/casinoking-console.tsx`` - shell piattaforma
- ``frontend/app/ui/mines/mines-standalone.tsx`` - componente principale gioco Mines
- ``frontend/app/ui/mines/mines-backoffice-editor.tsx`` - editor backoffice
- ``frontend/app/lib/types.ts`` - tipi condivisi
- ``frontend/app/lib/api.ts`` - client API condiviso

### Test di confine (DEVONO SEMPRE PASSARE)
- ``tests/contract/test_boundary_imports.py``
- ``tests/contract/test_round_gateway_contract.py``

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
- Verifica che ``test_boundary_imports.py`` passi dopo ogni modifica
- MAI fare shortcut o semplificazioni

## Comandi utili
``cd backend; pytest`` - tutti i test
``cd backend; pytest tests/unit/`` - solo unit
``cd backend; pytest tests/contract/`` - solo contract (confine)
``cd backend; pytest tests/concurrency/`` - solo concorrenza
``cd frontend; npm run build`` - build frontend
``cd frontend; npm run dev`` - dev server frontend

## Guida test utente
Ricorda: Michele non e' un programmatore. Le istruzioni per il test manuale
devono essere scritte come tutorial passo-passo con:
- URL da aprire
- Cosa cliccare
- Cosa aspettarsi
- Come verificare che non ci siano regressioni
"@
$codeRules | Out-File -FilePath ".roo\rules-code\project-rules.md" -Encoding utf8
Write-Host "[OK] .roo/rules-code/project-rules.md" -ForegroundColor Green

# --------------------------------------------------
# FINE
# --------------------------------------------------
Write-Host ""
Write-Host "=== FATTO! 5 file creati nella cartella .roo ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Prossimo passo: configurare i modi nell'interfaccia di Roo Code." -ForegroundColor Yellow
Write-Host "Segui la guida SETUP_GUIDE.md per i dettagli." -ForegroundColor Yellow
