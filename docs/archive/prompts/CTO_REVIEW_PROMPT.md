# CTO Review Prompt

Usa questo prompt per una revisione tecnica completa del repository `casinoking-platform`.

## Prompt

Sei un CTO / principal engineer incaricato di fare una review architetturale e operativa del progetto CasinoKing.

Obiettivi della review:

1. capire cosa e' gia' solido
2. individuare i coupling ancora aperti
3. distinguere i problemi di architettura dai problemi di UX o polish
4. proporre una sequenza realistica per continuare il progetto senza aumentare il rischio di regressioni
5. valutare in modo esplicito il confine tra:
   - platform backend
   - game backend Mines
   - web / aggregator frontend
   - admin / backoffice

Vincoli importanti:

- i documenti canonici sono in `docs/word/`
- i mirror operativi sono in `docs/md/`
- partire sempre da `docs/SOURCE_OF_TRUTH.md`
- considerare il ledger come fonte contabile primaria
- considerare Mines come server-authoritative
- non proporre semplificazioni che rompano il modello finanziario
- non trattare il frontend attuale come target finale: distinguere tra stato transitorio e target corretto

Ordine di lettura richiesto:

1. `docs/SOURCE_OF_TRUTH.md`
2. `docs/PROJECT_STATUS_2026_03_30.md`
3. `docs/md/CasinoKing_Documento_33_Stato_Progetto_Analisi_CTO_Guida_Migrazione.md`
4. `docs/md/CasinoKing_Documento_36_CTO_Reading_Order_Esecutivo.md`
5. `docs/md/CasinoKing_Documento_30_Separazione_Prodotti_Piattaforma_Gioco_Aggregatore.md`
6. `docs/md/CasinoKing_Documento_31_Contratto_Tra_Platform_Backend_E_Mines_Backend.md`
7. `docs/md/CasinoKing_Documento_35_Mappatura_Codebase_Attuale_E_Split_Target.md`
8. poi il codebase reale

File del codebase da leggere sicuramente:

Backend:

- `backend/app/modules/auth/service.py`
- `backend/app/modules/wallet/service.py`
- `backend/app/modules/ledger/service.py`
- `backend/app/modules/platform/game_launch/service.py`
- `backend/app/modules/platform/rounds/service.py`
- `backend/app/modules/games/mines/runtime.py`
- `backend/app/modules/games/mines/fairness.py`
- `backend/app/modules/games/mines/randomness.py`
- `backend/app/modules/games/mines/service.py`
- `backend/app/modules/games/mines/round_gateway.py`
- `backend/app/modules/games/mines/backoffice_config.py`

Frontend:

- `frontend/app/ui/casinoking-console.tsx`
- `frontend/app/ui/mines-standalone.tsx`
- `frontend/app/ui/mines-board.tsx`
- `frontend/app/globals.css`

Migration / persistence:

- `backend/migrations/sql/0011__mines_backoffice_draft_publish_assets.sql`

Durante la review, produci:

1. un executive summary tecnico
2. una classificazione dei problemi in:
   - architettura
   - boundary
   - debt tecnico
   - UX / presentation
3. i 5 rischi principali
4. una proposta di roadmap in fasi
5. una valutazione esplicita se il progetto e' recuperabile senza rewrite e in quali condizioni

Richiesta importante:

non fermarti ai bug visivi correnti. Voglio capire:

- qual e' il modello target corretto
- quali parti del progetto sono gia' allineate al target
- quali file stanno ancora rallentando il progetto
- quale sequenza di lavoro minimizza regressioni e coupling
