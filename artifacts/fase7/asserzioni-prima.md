# MAN-03 — i file da ricucire, e il metro per non annacquarli

## Correzione di un numero del contratto

`CONTRATTO_FASE_7.md` dice *136 funzioni in 28 file*. Quel conteggio prendeva ogni file
che **cita** una rotta di gioco. Misurando meglio — solo i file che eseguono davvero
un'azione che muove denaro (`start`, `reveal`, `cashout`, `launch-token`, ...) — il
perimetro vero e' piu' piccolo:

| | |
|---|---|
| File da ricucire | **19** |
| Funzioni di test dentro quei file | **100** |
| Asserzioni da preservare | **905** |
| Chiamate a rotte di gioco da sostituire | **71** |

Cinque file in piu' **citano** una rotta di gioco dentro un'asserzione di instradamento
(`test_admin_contract`, `test_game_reporting_registry`, `test_gmp3_host_neutral_descriptors`,
`test_site_v3_public_renderer_contract`, `test_gmp3_host_neutral_demo_launch`): non muovono
soldi e **non vanno toccati**.

## Il metro

Dopo la ricucitura ogni file deve avere **almeno le stesse asserzioni** di adesso.
Perdere asserzioni significa aver cambiato *cosa* il test verifica, non solo il veicolo.
Un file che ne perde va spiegato per iscritto o rimesso com'era.

| File | azioni di gioco | test | asserzioni (minimo dopo) |
|---|---|---|---|
| `contract/test_api_contract.py` | 6 | 15 | **100** |
| `contract/test_gmp5_game_module_manifest.py` | 1 | 5 | **42** |
| `contract/test_title_editor_agnostic.py` | 1 | 11 | **112** |
| `integration/test_8b_demo_anonymous_invariants.py` | 6 | 6 | **18** |
| `integration/test_account_wallet_movements.py` | 5 | 6 | **111** |
| `integration/test_admin_financial_reports.py` | 4 | 6 | **85** |
| `integration/test_admin_force_close_sessions.py` | 5 | 4 | **52** |
| `integration/test_admin_ledger_report.py` | 2 | 3 | **32** |
| `integration/test_admin_ledger_transactions_access.py` | 1 | 1 | **6** |
| `integration/test_admin_session_drilldown.py` | 1 | 1 | **16** |
| `integration/test_game_library_publication.py` | 5 | 11 | **80** |
| `integration/test_game_table_sessions.py` | 7 | 7 | **44** |
| `integration/test_game_title_archive_restore.py` | 1 | 4 | **37** |
| `integration/test_platform_access_sessions.py` | 6 | 4 | **41** |
| `integration/test_player_account_statement_browser_smoke.py` | 8 | 2 | **20** |
| `integration/test_reconciliation_integrity.py` | 3 | 3 | **8** |
| `integration/test_session_cascade_close.py` | 2 | 6 | **49** |
| `integration/test_title_code_propagation.py` | 6 | 4 | **41** |
| `integration/test_wallet_detail_access.py` | 1 | 1 | **11** |
