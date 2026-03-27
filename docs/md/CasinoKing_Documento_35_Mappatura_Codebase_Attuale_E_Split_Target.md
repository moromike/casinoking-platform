# CasinoKing - Documento 35

Mappatura del codebase attuale e split target tra platform, game e aggregator

Stato del documento

- Documento operativo nuovo.
- Serve come ponte tra analisi architetturale e refactor del codice.
- Va letto insieme ai Documenti 30, 31, 32, 33 e 34.

## 1. Obiettivo

Dire in modo esplicito:

- quali file attuali appartengono gia' al dominio giusto
- quali file sono temporaneamente misti
- quale destinazione target devono avere

## 2. Backend

## 2.1 Gia' nel dominio piattaforma corretto

- [backend/app/modules/auth/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/auth/service.py)
- [backend/app/modules/wallet/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/wallet/service.py)
- [backend/app/modules/ledger/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/ledger/service.py)
- [backend/app/modules/admin/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/admin/service.py)

## 2.2 Gia' nel dominio gioco corretto

- [backend/app/modules/games/mines/fairness.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/fairness.py)
- [backend/app/modules/games/mines/runtime.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/runtime.py)
- [backend/app/modules/games/mines/randomness.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/randomness.py)

## 2.3 File misto da spezzare

- [backend/app/modules/games/mines/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/service.py)
- [backend/app/modules/games/mines/round_gateway.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/round_gateway.py)

### Motivo

`service.py` contiene ancora sia:

- technical game lifecycle
- financial lifecycle della round

`round_gateway.py` e' il primo boundary introdotto per togliere a `service.py` la conoscenza diretta delle operazioni wallet/ledger.

Non e' ancora la separazione finale platform/game via API.

E' un adapter interno transitorio che prepara il refactor successivo.

### Split target

#### `mines-backend`

- `validate_game_config`
- `open_game_round_after_platform_acceptance`
- `reveal_cell`
- `compute_final_payout`
- `close_game_round_state`

#### `platform-backend`

- `authorize_game_launch`
- `open_financial_round`
- `settle_financial_round`
- `close_play_session`

## 3. Frontend

## 3.1 File legacy web container

- [frontend/app/ui/casinoking-console.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/ui/casinoking-console.tsx)

### Stato

Contenitore legacy ancora usato da:

- [frontend/app/page.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/page.tsx)
- [frontend/app/account/page.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/account/page.tsx)
- [frontend/app/login/page.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/login/page.tsx)
- [frontend/app/register/page.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/register/page.tsx)
- [frontend/app/admin/page.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/admin/page.tsx)

### Split target

#### `web-platform`

- lobby
- auth pages
- player account
- eventuale catalogo giochi

#### `admin`

- login backoffice
- finance
- player admin
- casino admin

## 3.2 Primo file gia' nel dominio giusto

- [frontend/app/ui/mines-standalone.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/ui/mines-standalone.tsx)

### Stato

E' il primo estratto corretto del prodotto gioco.

### Direzione

Deve diventare nucleo della futura app `frontend/mines`.

## 4. Sequenza di refactor raccomandata

1. lasciare stabile `mines-standalone.tsx`
2. rimuovere definitivamente ogni residuo Mines da `casinoking-console.tsx`
3. introdurre il gateway `platform_round_gateway` nel backend Mines
4. introdurre i service piattaforma per `open_round` e `settle_round`
5. solo dopo spostare la UI web verso app dedicate

## 4.1 Stato avanzamento

Ad oggi il passo 3 e' iniziato:

- il gateway interno di round esiste gia' in [round_gateway.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/round_gateway.py)
- `service.py` usa gia' quel boundary per apertura round e cashout win

Il passo ancora da fare e' il successivo:

- spostare davvero il settlement nel dominio platform, mantenendo il gateway come adapter verso il nuovo service

## 5. Regola di sicurezza operativa

Se un task tocca uno di questi file misti:

- `frontend/app/ui/casinoking-console.tsx`
- `backend/app/modules/games/mines/service.py`

bisogna prima dichiarare se il cambiamento appartiene a:

- platform
- game
- aggregator

Se non e' chiaro, il task va fermato e ripensato.
