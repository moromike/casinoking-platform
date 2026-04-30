# CasinoKing — Project Status (2026-03-30)

## Stato generale

Tutte e 4 le fasi del **MINES_EXECUTION_PLAN** sono state completate:

- **Phase 1**: Frontend stabilization — estrazione componenti, shared types/api, fix UX
- **Phase 2**: Backend boundary hardening — helper functions, gateway docstring, 8 boundary tests
- **Phase 3**: Frontend product separation — Mines in `frontend/app/ui/mines/`, backoffice estratto, console ridotta
- **Phase 4**: Schema split & contract — `platform_rounds` + `mines_game_rounds`, migrazioni 0012/0013

### Metriche chiave
| Metrica | Prima | Dopo |
|---------|-------|------|
| Console piattaforma (righe) | 5.329 | 3.122 |
| Componenti Mines | 1 monolite | 9 componenti in `frontend/app/ui/mines/` |
| Schema DB | `game_sessions` unica | `platform_rounds` + `mines_game_rounds` + vista compat |
| Test di confine | 0 | 8 (boundary imports + gateway contract) |

---

## Backend attuale

- [`platform/rounds/service.py`](../backend/app/modules/platform/rounds/service.py) ora opera su `platform_rounds` (non più `game_sessions`)
- [`service.py`](../backend/app/modules/games/mines/service.py) ora opera su `mines_game_rounds` con helper functions e crea correttamente il record correlato in `platform_rounds` durante lo start round
- [`round_gateway.py`](../backend/app/modules/games/mines/round_gateway.py) documentato con docstring e `get_round_start_snapshot()`
- 8 test di confine:
  - [`test_boundary_imports.py`](../tests/contract/test_boundary_imports.py) — verifica che i moduli non importino cross-boundary
  - [`test_round_gateway_contract.py`](../tests/contract/test_round_gateway_contract.py) — verifica il contratto del gateway
- Migrazioni:
  - [`0012__schema_split_platform_rounds.sql`](../backend/migrations/sql/0012__schema_split_platform_rounds.sql) — crea `platform_rounds` e `mines_game_rounds`
  - [`0013__migrate_game_sessions_data.sql`](../backend/migrations/sql/0013__migrate_game_sessions_data.sql) — data migration + vista `game_sessions_compat`

---

## Frontend attuale

- [`mines-standalone.tsx`](../frontend/app/ui/mines/mines-standalone.tsx) (~850 righe) + 7 componenti estratti:
  - `mines-board.tsx`, `mines-stage-header.tsx`, `mines-rules-modal.tsx`
  - `mines-balance-footer.tsx`, `mines-action-buttons.tsx`
  - `mines-mobile-settings-sheet.tsx`, `index.ts` (barrel)
- [`mines-backoffice-editor.tsx`](../frontend/app/ui/mines/mines-backoffice-editor.tsx) (853 righe) — componente autonomo backoffice
- [`casinoking-console.tsx`](../frontend/app/ui/casinoking-console.tsx) (3.122 righe) — solo piattaforma, zero codice gioco Mines
- Shared:
  - [`types.ts`](../frontend/app/lib/types.ts) — tipi condivisi piattaforma + gioco
  - [`api.ts`](../frontend/app/lib/api.ts) — client API condiviso
  - [`helpers.ts`](../frontend/app/lib/helpers.ts) — utility condivise
- Fix recente: rail sinistro desktop di Mines stabilizzato con layout opzioni deterministico; banner errore reso non distruttivo per il layout

---

## Rischi residui

1. **CSS globale ancora in un unico file** (3.7k+ righe) — non ancora modularizzato
2. **`game_sessions` table ancora presente** (non droppata) — serve per transizione graduale
3. **Stile Mines ancora dipendente da `globals.css`** — il fix del rail desktop ha ridotto il rischio ma non ha ancora separato il CSS di prodotto
4. **Test di integrazione non ancora eseguiti** con il nuovo schema e con il fix round-start finale

---

## Prossimi step consigliati

1. Eseguire test di integrazione completi con Docker up
2. Verificare manualmente il gioco su `/mines` (desktop + mobile) dopo il fix round-start + rail desktop
3. Verificare backoffice admin
4. Valutare isolamento CSS Mines dal file globale
5. Valutare se droppare `game_sessions` o mantenerla come backup

---

*Ultimo aggiornamento: 2026-03-31*
