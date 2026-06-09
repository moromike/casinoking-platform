# Cross-Game Parity Audit â€” Mines vs BOXE vs HI-LO (2026-06-04)

**Tipo:** Audit READ-ONLY (nessuna modifica a codice / DB / migration).
**Esecutore:** KIMI. **Gate:** Claude (CTO).
**Origine:** Michele, 2026-06-04 â€” "se abbiamo fatto 1000 diff non abbiamo mai analizzato i database???". La cosa grave non e' la divergenza: e' non averla rilevata. Bonifica retroattiva + regola permanente (vedi `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` da aggiornare in B7).

## Obiettivo

Mappare **TUTTE** le divergenze architetturali tra i 3 giochi proprietari a livello di:
DB-schema, modello demo, service-architecture, launch-token, settlement/access-session, identita'/auth, layering modulo.
Output = **matrice divergenze** con **target canonico** per ogni asse + stima effort di bonifica.
Questo audit **precede e informa** l'Opzione B (unificazione Mines verso il canonico). Non si unifica verso un target non mappato.

## Vincoli (HARD)

- **READ-ONLY assoluto.** Nessun edit a codice, nessuna migration, nessun DROP/ALTER, nessun fix "al volo". Solo lettura + analisi + scrittura di QUESTO doc.
- **Evidence-based.** Ogni cella della matrice deve citare la prova: `file:line`, numero migration, nome tabella. Niente "credo/sembra".
- **Niente assunzioni.** Se un comportamento non e' verificabile leggendo il codice, marcalo `DA VERIFICARE` con la domanda precisa, non inventare.
- **Severita' onesta.** Classifica ogni divergenza per gravita' reale (vedi scala sotto), senza minimizzare.

## Ipotesi di partenza del CTO (da CONFERMARE o SMENTIRE con prove)

Trovate in ricognizione preliminare â€” KIMI le verifica, non le da' per buone:

- **H1 â€” Demo model:** BOXE/HI-LO usano il servizio condiviso `app.modules.platform.demo_wallet.service` (`open_demo_session`, `debit_for_bet`) con path unico + guard `wallet_source=="demo"`. Mines usa implementazione bespoke: tabelle `demo_mines_game_rounds`/`demo_play_sessions`/`demo_round_events` (migration 0027) + funzioni separate `start_demo_session`/`reveal_demo_cell`/`cashout_demo_session` + `DemoPlatformGameClient`. â†’ Mines = outlier.
- **H2 â€” wallet_source:** BOXE/HI-LO supportano `{"cash","bonus","demo"}`. Mines supporta bonus? (sospetto NO). â†’ divergenza capability.
- **H3 â€” Round/session tables:** Mines = `platform_rounds`+`mines_game_rounds`+`game_access_sessions`+`game_table_sessions`. BOXE = `boxe_sessions`+`boxe_rounds`+`boxe_picks`+`boxe_idempotency_keys` (0039). HI-LO = `hi_lo_rounds`+`hi_lo_actions`+`hi_lo_idempotency_keys` (0043). â†’ forme diverse: BOXE ha tabella `*_sessions` propria, HI-LO no, Mines usa access/table sessions condivise.
- **H4 â€” Access-session (money-safety):** la rete di sicurezza (access-session 3-min timeout + auto-settlement refund/cashout su close) sembra cablata a livello router SOLO in Mines (`access-sessions/latest`, cascade close). BOXE/HI-LO accettano `access_session_id` come parametro service ma **va verificato** se creano/forzano l'access-session e se hanno auto-settlement equivalente. **Questo e' l'asse piu' critico: se BOXE/HI-LO non hanno la rete di sicurezza, e' un buco soldi.**
- **H5 â€” Launch-token:** dopo i WP recenti, BOXE e Mines inviano `X-Game-Launch-Token` SOLO allo start (validato), resto via round+bearer+ownership. HI-LO? â†’ verificare se HI-LO ha gia' il pattern canonico o e' divergente.
- **H6 â€” Layering modulo:** BOXE/HI-LO hanno `repository.py`+`state_machine.py`+`round_gateway.py` (architettura a strati). Mines ha `service.py`+`runtime.py`+`round_gateway.py`, NO repository/state_machine. â†’ Mines architettura di modulo piu' vecchia/diversa.
- **H7 â€” Ownership:** tutti e 3 enforce ownership su reveal/cashout/letture? Mines via `user_id`-scoped + `_ensure`/`session_belongs_to_user`; BOXE via `_ensure_round_owner`; HI-LO? â†’ verificare HI-LO.

## Assi della matrice (righe) â€” da riempire per ogni gioco

1. **Tabelle round** (platform_rounds + game-specific): quali, migration.
2. **Tabelle session** (game_access_sessions / game_table_sessions / *_sessions proprie): quali.
3. **Modello demo**: bespoke (tabelle+funzioni proprie) vs shared `demo_wallet` service.
4. **Tabelle demo dedicate**: quali (se esistono).
5. **wallet_source supportati**: cash / bonus / demo â€” quali sono accettati.
6. **Path demo vs real**: funzioni separate vs path unico con guard `wallet=="demo"`.
7. **Launch-token**: emesso dove, validato dove, inviato su quali azioni (start-only vs ogni azione).
8. **Access-session lifecycle**: creata? enforced? **auto-settlement su close/timeout (refund/cashout)?** â€” CRITICO soldi.
9. **Settlement/ledger reale**: come apre/chiude platform_rounds + ledger; demo lo evita come?
10. **Ownership enforcement**: meccanismo su reveal/cashout/letture (per gioco).
11. **Idempotency**: tabella dedicata (`*_idempotency_keys`) vs altro.
12. **Layering modulo**: presenza di repository.py / state_machine.py / round_gateway.py / runtime.py.
13. **platform_client**: forma dell'astrazione (firma, demo client separato vs unico).

## Formato output (da scrivere in QUESTO file, sezione "RISULTATI")

Per ogni asse 1-13, una tabella:

| Asse | Mines | BOXE | HI-LO | Canonico (target) | Divergenza? | Severita' |
|------|-------|------|-------|-------------------|-------------|-----------|

Poi, per ogni divergenza trovata:
- **ID** (es. DIV-01), **asse**, **descrizione**, **prove** (`file:line` / migration / tabella), **gioco/i outlier**, **target canonico raccomandato**, **stima effort bonifica** (S/M/L + righe ~), **rischi**.

Infine:
- **Sintesi**: quante divergenze per severita'; chi e' l'outlier dominante.
- **Target canonico complessivo**: quale gioco/pattern e' il riferimento per asse.
- **Ordine di bonifica raccomandato** (cosa unificare prima, dipendenze).

### Scala severita'

- **CRITICA**: rischio soldi / sicurezza / dato (es. un gioco senza rete auto-settlement; demo che potrebbe toccare ledger reale).
- **ALTA**: divergenza architetturale strutturale che blocca un pattern unico (es. modello demo bespoke vs shared).
- **MEDIA**: divergenza di forma/layering che genera duplicazione/manutenzione doppia.
- **BASSA**: cosmetico/naming, nessun impatto funzionale.

## Definition of Done

- [ ] Tutti i 13 assi compilati per Mines/BOXE/HI-LO con prove citate.
- [ ] Tutte le ipotesi H1-H7 confermate o smentite con prova.
- [ ] H4 (access-session/auto-settlement) verificata esplicitamente per BOXE e HI-LO (e' la piu' critica).
- [ ] Lista divergenze DIV-xx con severita', prove, target canonico, effort.
- [ ] Sintesi + target canonico complessivo + ordine bonifica.
- [ ] ZERO modifiche a codice/DB/migration (solo questo doc).
- [ ] Stop CTO al termine (no esecuzione bonifica).

---

## RISULTATI (da compilare da KIMI)

### Esito ipotesi H1-H7

| Ipotesi | Esito | Prove |
|---|---|---|
| H1 - Demo model | SMENTITA nella forma originale. Mines usa funzioni demo separate ma passa dal `DemoPlatformGameClient` che usa `demo_wallet`; HI-LO usa direttamente `demo_wallet`; BOXE non usa `demo_wallet` nel backend e mantiene saldo demo lato frontend. | Mines: `backend/app/modules/games/mines/service.py:184`, `backend/app/modules/games/mines/service.py:1139`, `backend/app/modules/games/mines/service.py:1255`, `backend/app/modules/games/mines/platform_client.py:16-18`, `backend/app/modules/games/mines/platform_client.py:354`, `backend/app/modules/games/mines/platform_client.py:379-384`. HI-LO: `backend/app/modules/games/hi_lo/service.py:54-61`, `backend/app/modules/games/hi_lo/service.py:193-199`, `backend/app/modules/games/hi_lo/service.py:578-579`. BOXE: `backend/app/modules/games/boxe/service.py:195`, `frontend-v3/app/ui/boxe/boxe-gameplay.tsx:196`, `frontend-v3/app/ui/boxe/boxe-gameplay.tsx:595-656`. |
| H2 - wallet_source | CONFERMATA solo come differenza di validazione. Tutti supportano cash/bonus/demo nei flussi runtime, ma BOXE/HI-LO hanno whitelist esplicita; Mines normalizza `wallet_type` e delega a wallet/table/demo path. | BOXE: `backend/app/modules/games/boxe/service.py:64`, `backend/app/modules/games/boxe/service.py:1015-1019`. HI-LO: `backend/app/modules/games/hi_lo/service.py:68`, `backend/app/modules/games/hi_lo/service.py:910-916`, `backend/migrations/sql/0043__hi_lo_round_tables.sql:53-54`. Mines: `backend/app/api/routes/mines.py:78`, `backend/app/api/routes/mines.py:536-538`, `backend/app/modules/games/mines/service.py:63`, `frontend-v3/app/ui/mines/mines-standalone.tsx:137-147`, `frontend-v3/app/ui/mines/mines-standalone.tsx:1485-1491`. |
| H3 - Round/session tables | CONFERMATA. Le forme sono diverse: Mines `platform_rounds` + `mines_game_rounds`; BOXE `boxe_sessions` + `boxe_rounds` + `boxe_picks`; HI-LO `hi_lo_rounds` + `hi_lo_actions`, senza `*_sessions` propria. | `backend/migrations/sql/0012__schema_split_platform_rounds.sql:14`, `backend/migrations/sql/0012__schema_split_platform_rounds.sql:49`; `backend/migrations/sql/0039__boxe_session_tables.sql:11`, `backend/migrations/sql/0039__boxe_session_tables.sql:45`, `backend/migrations/sql/0039__boxe_session_tables.sql:136`; `backend/migrations/sql/0043__hi_lo_round_tables.sql:10`, `backend/migrations/sql/0043__hi_lo_round_tables.sql:101`. |
| H4 - Access-session / auto-settlement | SMENTITA per la parte piu' critica: BOXE e HI-LO hanno handler di auto-settlement su close/timeout. Confermata una divergenza residua: nei router l'enforcement avviene solo se `access_session_id` e' passato; il frontend real lo crea e lo passa. | Timeout 3 minuti: `backend/app/modules/platform/access_sessions/service.py:24`, loop: `backend/app/main.py:16`, `backend/app/main.py:67-71`. Handler: `backend/app/modules/platform/access_sessions/service.py:654`, `backend/app/modules/platform/access_sessions/service.py:731`, `backend/app/modules/platform/access_sessions/service.py:826`, registry `backend/app/modules/platform/access_sessions/service.py:933-935`. BOXE/HI-LO router: `backend/app/api/routes/boxe.py:166-170`, `backend/app/api/routes/hi_lo.py:89-93`. Frontend crea/passa: `frontend-v3/app/ui/boxe/use-boxe-runtime.ts:204-211`, `frontend-v3/app/ui/boxe/boxe-gameplay.tsx:488`, `frontend-v3/app/ui/hi-lo/use-hi-lo-runtime.ts:211-216`, `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx:324`. |
| H5 - Launch-token | CONFERMATA come divergenza. Mines e BOXE hanno endpoint launch-token e inviano/validano header sullo start real; HI-LO non ha endpoint/header launch-token nel router/runtime letto. | Mines backend/frontend: `backend/app/api/routes/mines.py:575`, `backend/app/api/routes/mines.py:400`, `frontend-v3/app/ui/mines/mines-standalone.tsx:1055-1069`. BOXE backend/frontend: `backend/app/api/routes/boxe.py:86`, `backend/app/api/routes/boxe.py:135`, `frontend-v3/app/ui/boxe/boxe-gameplay.tsx:368-382`, `frontend-v3/app/ui/boxe/use-boxe-runtime.ts:281`. HI-LO: router mutazioni senza `X-Game-Launch-Token` in `backend/app/api/routes/hi_lo.py:77-196`, runtime start senza launch token in `frontend-v3/app/ui/hi-lo/use-hi-lo-runtime.ts:264-284`. |
| H6 - Layering modulo | CONFERMATA. BOXE/HI-LO hanno `repository.py`, `state_machine.py`, `round_gateway.py`; Mines ha `service.py`, `runtime.py`, `round_gateway.py`, `platform_client.py`, ma non repository/state_machine. | File list: `backend/app/modules/games/mines/service.py`, `backend/app/modules/games/mines/runtime.py`, `backend/app/modules/games/mines/round_gateway.py`; `backend/app/modules/games/boxe/repository.py`, `backend/app/modules/games/boxe/state_machine.py`, `backend/app/modules/games/boxe/round_gateway.py`; `backend/app/modules/games/hi_lo/repository.py`, `backend/app/modules/games/hi_lo/state_machine.py`, `backend/app/modules/games/hi_lo/round_gateway.py`. |
| H7 - Ownership | CONFERMATA: tutti e 3 fanno ownership enforcement su mutazioni/letture, con meccanismi diversi. | Mines SQL/user scope: `backend/app/modules/games/mines/service.py:895`, `backend/app/modules/games/mines/service.py:1899-1923`, `backend/app/modules/games/mines/service.py:1344-1352`. BOXE: `backend/app/modules/games/boxe/service.py:317`, `backend/app/modules/games/boxe/service.py:504`, `backend/app/modules/games/boxe/service.py:617`, `backend/app/modules/games/boxe/service.py:965-966`. HI-LO: `backend/app/modules/games/hi_lo/service.py:330`, `backend/app/modules/games/hi_lo/service.py:461`, `backend/app/modules/games/hi_lo/service.py:544`, `backend/app/modules/games/hi_lo/service.py:954-955`. |

### Matrice 13 assi

| Asse | Mines | BOXE | HI-LO | Canonico (target) | Divergenza? | Severita' |
|------|-------|------|-------|-------------------|-------------|-----------|
| 1. Tabelle round | `platform_rounds` + `mines_game_rounds` (`backend/migrations/sql/0012__schema_split_platform_rounds.sql:14`, `:49`). | `boxe_rounds` + `boxe_picks`, piu' mirror `platform_rounds` creato da repository (`backend/migrations/sql/0039__boxe_session_tables.sql:45`, `:136`; `backend/app/modules/games/boxe/repository.py:452`). | `hi_lo_rounds` + `hi_lo_actions`, piu' mirror `platform_rounds` (`backend/migrations/sql/0043__hi_lo_round_tables.sql:10`, `:101`; `backend/app/modules/games/hi_lo/repository.py:549`). | Game-specific round/action tables + platform round host-owned per real money. | Si | MEDIA |
| 2. Tabelle session | Usa `game_access_sessions` e `game_table_sessions`; nessuna tabella session propria (`backend/migrations/sql/0016__game_access_sessions.sql:3`, `backend/migrations/sql/0020__game_table_sessions.sql:3`). | Ha `boxe_sessions` con FK access/table (`backend/migrations/sql/0039__boxe_session_tables.sql:11-15`). | Nessuna `hi_lo_sessions`; `hi_lo_rounds` contiene access/table (`backend/migrations/sql/0043__hi_lo_round_tables.sql:10-15`). | Access/table session platform + evitare `*_sessions` propria salvo bisogno prodotto esplicito. | Si | MEDIA |
| 3. Modello demo | Funzioni separate `start_demo_session`/`reveal_demo_cell`/`cashout_demo_session` con `DemoPlatformGameClient` (`backend/app/modules/games/mines/service.py:184`, `:1139`, `:1255`; `backend/app/modules/games/mines/platform_client.py:354`). | Backend non usa `demo_wallet`: se `normalized_wallet == "demo"` salta `open_platform_round` (`backend/app/modules/games/boxe/service.py:195`) e frontend mantiene `demoBalance` locale (`frontend-v3/app/ui/boxe/boxe-gameplay.tsx:196`, `:595-656`). | Path unico con branch demo e `demo_wallet` (`backend/app/modules/games/hi_lo/service.py:54-61`, `:193-199`, `:578-579`). | HI-LO-style: path unico + `demo_wallet` server-side + game state con `demo_session_id`. | Si | CRITICA |
| 4. Tabelle demo dedicate | `demo_play_sessions`, `demo_round_events`, `demo_mines_game_rounds` (`backend/migrations/sql/0027__demo_sessions.sql:3`, `:27`, `:44`). | Nessuna tabella demo BOXE dedicata trovata; `boxe_rounds.platform_round_id` e' nullable (`backend/migrations/sql/0039__boxe_session_tables.sql:48`) e demo vive in `boxe_rounds`. | `hi_lo_rounds.demo_session_id` verso `demo_play_sessions` (`backend/migrations/sql/0043__hi_lo_round_tables.sql:16`). | Shared `demo_play_sessions`/`demo_round_events`; game table con nullable `demo_session_id`, non tabella demo bespoke per gioco. | Si | ALTA |
| 5. wallet_source supportati | Frontend tipizza cash/bonus e demo path (`frontend-v3/app/ui/mines/mines-standalone.tsx:137-147`, `:1485-1491`); backend usa `wallet_type` e normalizza senza whitelist esplicita (`backend/app/api/routes/mines.py:78`, `backend/app/modules/games/mines/service.py:63`). | Whitelist `{"cash","bonus","demo"}` (`backend/app/modules/games/boxe/service.py:64`, `:1015-1019`). | Whitelist `{"cash","bonus","demo"}` (`backend/app/modules/games/hi_lo/service.py:68`, `:910-916`). | Whitelist esplicita `cash|bonus|demo` in ogni service. | Si | MEDIA |
| 6. Path demo vs real | Route/service separati per demo e real (`backend/app/api/routes/mines.py:417-419`, `:536-538`, `backend/app/modules/games/mines/service.py:184`, `:49`). | Path unico `start_round`, ma demo salta solo platform open (`backend/app/modules/games/boxe/service.py:135`, `:195`). | Path unico `start_round`, demo usa `open_demo_session`/`debit_for_bet`, real usa platform round (`backend/app/modules/games/hi_lo/service.py:121`, `:191-221`). | Path unico con branch controllato su `wallet_source`. | Si | ALTA |
| 7. Launch-token | Endpoint `/launch-token`; start riceve `X-Game-Launch-Token`; reveal/cashout token opzionale o bearer + ownership (`backend/app/api/routes/mines.py:575`, `:400`, `:641`, `:810`; `frontend-v3/app/ui/mines/mines-standalone.tsx:1055-1069`). | Endpoint `/launch-token`; start riceve header opzionale e frontend lo invia quando presente (`backend/app/api/routes/boxe.py:86`, `:135`, `frontend-v3/app/ui/boxe/boxe-gameplay.tsx:368-382`, `frontend-v3/app/ui/boxe/use-boxe-runtime.ts:281`). | Nessun endpoint/header launch-token nel router/runtime letto (`backend/app/api/routes/hi_lo.py:77-196`, `frontend-v3/app/ui/hi-lo/use-hi-lo-runtime.ts:264-284`). | Start-only real launch-token per tutti; azioni successive bearer + round ownership. | Si | ALTA |
| 8. Access-session lifecycle | Frontend crea/pinga/chiude access-session (`frontend-v3/app/ui/mines/mines-standalone.tsx:662-710`, `:1242-1249`); route latest dedicata (`backend/app/api/routes/mines.py:311`); start valida se id passato (`backend/app/api/routes/mines.py:454-458`). Auto-settlement Mines esiste (`backend/app/modules/platform/access_sessions/service.py:654-722`). | Frontend crea e passa access-session (`frontend-v3/app/ui/boxe/use-boxe-runtime.ts:204-211`, `frontend-v3/app/ui/boxe/boxe-gameplay.tsx:488`); router valida se id passato (`backend/app/api/routes/boxe.py:166-170`). Auto-settlement BOXE esiste (`backend/app/modules/platform/access_sessions/service.py:731-822`). | Frontend crea e passa access-session (`frontend-v3/app/ui/hi-lo/use-hi-lo-runtime.ts:211-216`, `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx:324`); router valida se id passato (`backend/app/api/routes/hi_lo.py:89-93`). Auto-settlement HI-LO esiste (`backend/app/modules/platform/access_sessions/service.py:826-928`). | Access-session obbligatoria per real start, auto-settlement registrato per ogni gioco. | Si, enforcement opzionale lato router | ALTA |
| 9. Settlement/ledger reale | Real usa `open_game_round`/`settle_game_round_win/loss` via client (`backend/app/modules/games/mines/platform_client.py:163-191`, `:287-337`); demo usa `demo_wallet` via client (`backend/app/modules/games/mines/platform_client.py:379-384`, `:532-568`). | Real usa platform services e mirror `platform_rounds` (`backend/app/modules/games/boxe/platform_client.py:245-272`, `:311-365`; `backend/app/modules/games/boxe/repository.py:452-512`). Demo non apre platform round (`backend/app/modules/games/boxe/service.py:195`) e non mostra `demo_wallet` backend. | Real usa platform services + mirror; demo usa `demo_wallet` debit/loss/win (`backend/app/modules/games/hi_lo/platform_client.py:60-85`, `:123-172`; `backend/app/modules/games/hi_lo/service.py:193-199`, `:381-382`, `:578-579`). | Host platform owns real ledger; demo server-side `demo_wallet`, no ledger/platform real rows. | Si | CRITICA |
| 10. Ownership enforcement | SQL user-scope + `session_belongs_to_user` (`backend/app/modules/games/mines/service.py:895`, `:1899-1923`, `:1344-1352`). | `_ensure_round_owner` su reveal/cashout/replay (`backend/app/modules/games/boxe/service.py:317`, `:504`, `:617`, `:965-966`). | `_ensure_round_owner` su predict/skip/cashout/replay (`backend/app/modules/games/hi_lo/service.py:330`, `:461`, `:544`, `:641`, `:954-955`). | Tutti OK; preferibile helper esplicito uniforme. | Si, forma diversa | BASSA |
| 11. Idempotency | `platform_rounds.user_id,idempotency_key`; demo `demo_round_events` e `demo_mines_game_rounds` (`backend/migrations/sql/0012__schema_split_platform_rounds.sql:39-40`, `backend/migrations/sql/0027__demo_sessions.sql:41-42`, `:82-83`). | Dedicated `boxe_idempotency_keys` + per-pick uniqueness (`backend/migrations/sql/0039__boxe_session_tables.sql:165-189`; `backend/app/modules/games/boxe/repository.py:373-391`). | Dedicated `hi_lo_idempotency_keys` + per-action uniqueness (`backend/migrations/sql/0043__hi_lo_round_tables.sql:139-159`; `backend/app/modules/games/hi_lo/repository.py:472-490`). | Dedicated game idempotency table plus platform settlement idempotency. | Si | MEDIA |
| 12. Layering modulo | `service.py`, `runtime.py`, `round_gateway.py`, `platform_client.py`; no `repository.py`/`state_machine.py` in file list. | `repository.py`, `state_machine.py`, `round_gateway.py`, `platform_client.py` presenti. | `repository.py`, `state_machine.py`, `round_gateway.py`, `platform_client.py` presenti. | BOXE/HI-LO layering: repository + state_machine + round_gateway + platform_client. | Si | MEDIA |
| 13. platform_client | Class-based client + `DemoPlatformGameClient` separato (`backend/app/modules/games/mines/platform_client.py:79-149`, `:354`). | Typed adapter facade `PlatformGameAdapter` via `get_default_platform_adapter()` (`backend/app/modules/games/boxe/platform_client.py:75-122`, `:148-228`). | Direct function facade, no typed adapter class (`backend/app/modules/games/hi_lo/platform_client.py:60-85`, `:123-172`). | Typed adapter facade stile BOXE, con demo gestito dal service/shared demo wallet. | Si | MEDIA |

### Divergenze DIV-xx

**DIV-01 - Demo wallet BOXE non server-side**
- Asse: 3, 9.
- Descrizione: BOXE accetta `wallet_source="demo"` ma non usa `demo_wallet`; salta il platform round e aggiorna saldo demo nel frontend.
- Prove: `backend/app/modules/games/boxe/service.py:195`; assenza import `demo_wallet` nel top di `backend/app/modules/games/boxe/service.py:1-43`; `frontend-v3/app/ui/boxe/boxe-gameplay.tsx:196`, `:595-656`.
- Outlier: BOXE.
- Target canonico raccomandato: HI-LO pattern, `demo_wallet` server-side con debit/win/loss events.
- Effort: M/L, circa 250-500 righe + test demo/idempotency/replay.
- Rischi: CRITICO per coerenza dati demo e audit; basso rischio ledger reale perche' BOXE demo non apre `platform_rounds`.

**DIV-02 - Mines demo path separato e round demo bespoke**
- Asse: 3, 4, 6.
- Descrizione: Mines ha funzioni demo dedicate e tabella `demo_mines_game_rounds`, invece di path unico e `demo_session_id` su round table.
- Prove: `backend/app/modules/games/mines/service.py:184`, `:1139`, `:1255`; `backend/migrations/sql/0027__demo_sessions.sql:44`; `backend/app/modules/games/mines/platform_client.py:354`.
- Outlier: Mines.
- Target canonico raccomandato: path unico stile HI-LO, demo wallet shared, no nuova tabella demo bespoke.
- Effort: L, circa 600-1000 righe + migration/backfill se si decide di cambiare schema.
- Rischi: ALTA, replay/fairness/idempotency demo e compatibilita' sessioni esistenti.

**DIV-03 - Launch-token assente in HI-LO**
- Asse: 7.
- Descrizione: HI-LO non espone `/launch-token` e non invia/valida `X-Game-Launch-Token` su start real, mentre Mines/BOXE si sono allineati a start-only.
- Prove: Mines `backend/app/api/routes/mines.py:575`, BOXE `backend/app/api/routes/boxe.py:86`; HI-LO mutazioni `backend/app/api/routes/hi_lo.py:77-196`, frontend `frontend-v3/app/ui/hi-lo/use-hi-lo-runtime.ts:264-284`.
- Outlier: HI-LO.
- Target canonico raccomandato: endpoint launch-token + header start-only, azioni successive bearer+ownership.
- Effort: M, circa 180-350 righe + integration test.
- Rischi: ALTA, authority/title/site propagation non uniforme.

**DIV-04 - Access-session enforcement opzionale nel router**
- Asse: 8.
- Descrizione: tutti i router validano l'access-session solo se `access_session_id` viene passato. Il frontend real la crea e la passa, ma il backend non la rende obbligatoria in modo uniforme al boundary API.
- Prove: Mines `backend/app/api/routes/mines.py:454-458`; BOXE `backend/app/api/routes/boxe.py:166-170`; HI-LO `backend/app/api/routes/hi_lo.py:89-93`. Frontend passaggio real: `frontend-v3/app/ui/boxe/boxe-gameplay.tsx:488`, `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx:324`, `frontend-v3/app/ui/mines/mines-standalone.tsx:980-991`.
- Outlier: pattern comune fragile, non un singolo gioco.
- Target canonico raccomandato: real start richiede `access_session_id`; demo lo vieta/null.
- Effort: M, circa 150-300 righe + compat fallback decision CTO.
- Rischi: ALTA money-safety se client o host esterno omette access-session; auto-settlement esiste ma dipende dal link.

**DIV-05 - Session model non uniforme**
- Asse: 2.
- Descrizione: BOXE ha `boxe_sessions`, HI-LO no, Mines usa solo sessioni platform per grouping storico.
- Prove: `backend/migrations/sql/0039__boxe_session_tables.sql:11-15`; `backend/migrations/sql/0043__hi_lo_round_tables.sql:10-15`; `backend/migrations/sql/0016__game_access_sessions.sql:3`; `backend/migrations/sql/0020__game_table_sessions.sql:3`.
- Outlier: BOXE come session table propria; Mines/HI-LO forme diverse.
- Target canonico raccomandato: platform access/table session + game round direct, salvo bisogno esplicito.
- Effort: L se si rimuove `boxe_sessions`; S/M se si documenta come eccezione.
- Rischi: MEDIA, replay/history e reporting duplicati.

**DIV-06 - Round/platform mirror duplicato in BOXE/HI-LO**
- Asse: 1, 9.
- Descrizione: BOXE/HI-LO creano platform round via platform service e poi inseriscono un mirror `platform_rounds` nel repository; Mines inserisce platform round nel proprio service/client path. La forma e' diversa e aumenta rischio drift.
- Prove: BOXE `backend/app/modules/games/boxe/platform_client.py:245-272` + `backend/app/modules/games/boxe/repository.py:452-512`; HI-LO `backend/app/modules/games/hi_lo/platform_client.py:60-85` + `backend/app/modules/games/hi_lo/repository.py:549-609`; Mines `backend/app/modules/games/mines/service.py:1583-1617`.
- Outlier: tutti divergono nella forma.
- Target canonico raccomandato: unico adapter host che apre/settle platform round e restituisce ref; game repository non deve duplicare logica platform oltre FK/ref.
- Effort: M/L, circa 300-700 righe.
- Rischi: MEDIA/ALTA per audit finanziario se il mirror diverge.

**DIV-07 - wallet_source validation non uniforme**
- Asse: 5.
- Descrizione: BOXE/HI-LO whitelistano `cash|bonus|demo`; Mines non ha whitelist service equivalente sul `wallet_type` real.
- Prove: BOXE `backend/app/modules/games/boxe/service.py:64`, `:1015-1019`; HI-LO `backend/app/modules/games/hi_lo/service.py:68`, `:910-916`; Mines `backend/app/modules/games/mines/service.py:63`, `backend/app/api/routes/mines.py:78`.
- Outlier: Mines.
- Target canonico raccomandato: shared wallet source validator.
- Effort: S, circa 40-100 righe + tests.
- Rischi: MEDIA, input/API contract drift.

**DIV-08 - Idempotency model non uniforme**
- Asse: 11.
- Descrizione: Mines usa platform/demo constraints; BOXE/HI-LO usano tabelle dedicate `*_idempotency_keys`.
- Prove: Mines `backend/migrations/sql/0012__schema_split_platform_rounds.sql:39-40`, `backend/migrations/sql/0027__demo_sessions.sql:41-42`; BOXE `backend/migrations/sql/0039__boxe_session_tables.sql:172-189`; HI-LO `backend/migrations/sql/0043__hi_lo_round_tables.sql:146-159`.
- Outlier: Mines.
- Target canonico raccomandato: game-local idempotency result table + platform settlement idempotency.
- Effort: M, circa 200-400 righe.
- Rischi: MEDIA, retry/replay consistency.

**DIV-09 - Layering Mines legacy**
- Asse: 12, 13.
- Descrizione: Mines manca repository/state_machine e ha demo client separato; BOXE/HI-LO sono piu' stratificati.
- Prove: file list in `backend/app/modules/games/mines/*` vs `backend/app/modules/games/boxe/repository.py`, `backend/app/modules/games/boxe/state_machine.py`, `backend/app/modules/games/hi_lo/repository.py`, `backend/app/modules/games/hi_lo/state_machine.py`; Mines client `backend/app/modules/games/mines/platform_client.py:354`.
- Outlier: Mines.
- Target canonico raccomandato: repository + state_machine + typed platform adapter.
- Effort: L, circa 700-1200 righe se fatto davvero; S se solo documentato.
- Rischi: MEDIA, manutenzione e prossimi giochi.

**DIV-10 - platform_client adapter non uniforme**
- Asse: 13.
- Descrizione: BOXE usa adapter typed; HI-LO ha facade funzioni dirette; Mines ha classi e demo client.
- Prove: BOXE `backend/app/modules/games/boxe/platform_client.py:75-122`; HI-LO `backend/app/modules/games/hi_lo/platform_client.py:60-85`, `:123-172`; Mines `backend/app/modules/games/mines/platform_client.py:79-149`, `:354`.
- Outlier: Mines e HI-LO rispetto a BOXE.
- Target canonico raccomandato: BOXE typed adapter, poi esteso a tutti.
- Effort: M, circa 250-500 righe.
- Rischi: MEDIA, externalization/GMP future.

### Sintesi

- Divergenze CRITICHE: 2 (`DIV-01` e asse 9 demo/settlement; il rischio immediato soldi real per H4 e' smentito perche' BOXE/HI-LO hanno auto-settlement).
- Divergenze ALTE: 4 (`DIV-02`, `DIV-03`, `DIV-04`, parte di `DIV-06`).
- Divergenze MEDIE: 5 (`DIV-05`, `DIV-07`, `DIV-08`, `DIV-09`, `DIV-10`).
- Divergenze BASSE: ownership solo nella forma, nessuna ownership gap rilevata.
- Outlier dominante: Mines per layering/idempotency/demo shape; BOXE per demo wallet server-side mancante; HI-LO per launch-token assente.

### Target canonico complessivo

- Demo: HI-LO come target tecnico (`demo_wallet` server-side + `demo_session_id` su round game-specific), non BOXE.
- Real settlement: host platform owns ledger/open/settle; game state conserva solo ref e replay state.
- Access-session: pattern platform attuale con handler per tutti e 3, ma real start deve richiedere `access_session_id` al boundary API.
- Launch-token: Mines/BOXE B3 pattern, start-only real token; azioni successive bearer + ownership.
- Layering: BOXE/HI-LO repository + state_machine + round_gateway; platform adapter typed stile BOXE.
- Idempotency: tabelle dedicate game-local per risultato/replay + settlement idempotency platform.

### Ordine di bonifica raccomandato

1. BOXE demo server-side (`DIV-01`): prima del resto, per togliere l'anomalia piu' netta tra demo e audit.
2. Access-session API hardening (`DIV-04`): rendere obbligatorio `access_session_id` su real start per Mines/BOXE/HI-LO; mantenere demo null.
3. HI-LO launch-token (`DIV-03`): portare HI-LO al pattern start-only Mines/BOXE.
4. Definire target DB/sessioni (`DIV-05`, `DIV-06`) con decisione CTO prima di migration: non unificare Mines verso BOXE se `boxe_sessions` e' un'eccezione non desiderata.
5. Mines Opzione B demo/path unico (`DIV-02`) solo dopo aver chiuso target demo e session model.
6. Uniformare validator/idempotency/adapter/layering (`DIV-07`-`DIV-10`) come pacchetto architetturale, non come fix sparsi.

### Stop CTO

Audit concluso in READ-ONLY salvo questa sezione documentale. Nessuna bonifica eseguita. Prossimo passo: CTO decide il target canonico per demo/session/adapter prima di autorizzare Opzione B.
