# CasinoKing - Stato operativo al 2026-03-30

Questo documento non sostituisce i documenti canonici in `docs/word/`.
Serve come fotografia operativa del repository per revisione tecnica e pianificazione.

## 1. Stato generale

Il progetto ha fondamenta backend gia' buone e una parte frontend ancora in transizione.

Punti solidi:

- backend FastAPI con auth, wallet, ledger, admin
- modello finanziario con ledger fonte primaria e wallet snapshot
- Mines server-authoritative con runtime payout ufficiale, fairness e polling MVP
- primi boundary espliciti platform/game per `game_launch` e `rounds`

Punti ancora instabili:

- frontend Mines
- embedded desktop del gioco dalla lobby
- shell mobile del gioco
- backoffice Mines ospitato ancora nel contenitore admin legacy

## 2. Backend attuale

Domini piu' maturi:

- `backend/app/modules/auth/`
- `backend/app/modules/wallet/`
- `backend/app/modules/ledger/`
- `backend/app/modules/admin/`
- `backend/app/modules/platform/game_launch/`
- `backend/app/modules/platform/rounds/`

Domini Mines principali:

- `backend/app/modules/games/mines/runtime.py`
- `backend/app/modules/games/mines/fairness.py`
- `backend/app/modules/games/mines/randomness.py`
- `backend/app/modules/games/mines/service.py`
- `backend/app/modules/games/mines/round_gateway.py`
- `backend/app/modules/games/mines/backoffice_config.py`

Valutazione:

- `runtime`, `fairness` e `randomness` sono nel dominio corretto
- `service.py` resta ancora il file con coupling residuo piu' importante
- `backoffice_config.py` introduce un flusso corretto `draft/published`, ma appartiene ancora al modulo Mines dentro il monolite attuale

## 3. Frontend attuale

Shell legacy:

- `frontend/app/ui/casinoking-console.tsx`

Prodotto gioco gia' separato in parte:

- `frontend/app/ui/mines-standalone.tsx`
- `frontend/app/ui/mines-board.tsx`
- route `frontend/app/mines/page.tsx`

Valutazione:

- `mines-board.tsx` e' un miglioramento strutturale corretto
- `mines-standalone.tsx` resta troppo grande e contiene ancora troppi concern insieme
- desktop, mobile ed embed sono ancora troppo vicini nello stesso file

## 4. Backoffice Mines attuale

Capacita' presenti:

- bozza e pubblicazione live
- regole HTML
- subset pubblicato di griglie e mine count
- default mine count per griglia
- label demo/real
- asset board `safe` e `mine`

Persistenza:

- migrazione `backend/migrations/sql/0011__mines_backoffice_draft_publish_assets.sql`
- servizio `backend/app/modules/games/mines/backoffice_config.py`

Limite attuale:

- il backoffice vive ancora nella shell admin legacy, quindi UX e manutenzione sono piu' fragili di quanto dovrebbero

## 5. Principali rischi tecnici

1. Regressioni frontend Mines dovute a file troppo grandi e patch troppo ampie.
2. Coupling tra admin legacy e backoffice Mines.
3. Coupling residuo in `backend/app/modules/games/mines/service.py`.
4. Difficolta' a distinguere fix di layout da fix di comportamento se non si lavora a strati.

## 6. Direzione consigliata

Ordine consigliato:

1. stabilizzare frontend Mines con componenti piu' piccoli
2. separare il backoffice Mines dalla shell admin legacy
3. continuare il boundary backend platform/game
4. usare il backoffice solo con flusso `draft -> publish live`
5. evitare modifiche UX non richieste e patch trasversali troppo grandi

## 7. Lettura consigliata

Per un CTO o revisore tecnico:

1. `docs/SOURCE_OF_TRUTH.md`
2. `docs/md/CasinoKing_Documento_33_Stato_Progetto_Analisi_CTO_Guida_Migrazione.md`
3. `docs/md/CasinoKing_Documento_36_CTO_Reading_Order_Esecutivo.md`
4. `docs/md/CasinoKing_Documento_30_Separazione_Prodotti_Piattaforma_Gioco_Aggregatore.md`
5. `docs/md/CasinoKing_Documento_31_Contratto_Tra_Platform_Backend_E_Mines_Backend.md`
6. `docs/md/CasinoKing_Documento_35_Mappatura_Codebase_Attuale_E_Split_Target.md`

## 8. Nota di metodo

Per proseguire in modo sano:

- niente nuove feature “implicite”
- niente messaggi UI o copy non richiesti
- controllo obbligatorio della checklist in `docs/TASK_EXECUTION_GUARDRAILS.md`
- fix separati per contenuto, layout, comportamento e architettura
