# Coins — SPEC (lato piattaforma)

**Stato:** integrazione in corso (PASSO 3-bis, 11/09/2026). Coins e' un gioco
**esterno** di M&M Games: matematica, RNG, esiti e interfaccia vivono nel
repository del fornitore (`m-and-m-games`), non qui. Questo documento fissa il
contratto che la piattaforma garantisce verso Coins; i piani storici di
prodotto restano in `docs/games/coins/COINS_PHASE_0_1_PLAN_2026-05-25.md` e
negli altri documenti della stessa cartella.

## Identita' nel catalogo

- Motore `coins`, fornitore `m-and-m-games` (migrazione
  `backend/migrations/sql/0065__catalogo_coins.sql`).
- Titoli: `coins` (master, nascosto) e `coins001` (visibile, solo modalita'
  reale: nessun demo servito dalla piattaforma).
- `runtime_module` dichiara `external:m-and-m-games/coins`: nessun modulo di
  gioco gira dentro la piattaforma.

## Lancio

1. La piattaforma emette il launch-token (JWT HS256) con `wallet_type` e
   `currency` **decisi dalla piattaforma** (letti dal conto del giocatore,
   mai dal client): `backend/app/modules/platform/game_launch/service.py`.
2. Il token arriva a M&M nell'intestazione `X-Launch-Token`. Mai nella URL.
3. M&M **non riceve `jwt_secret`**: verifica il token chiamando
   `POST /api/v1/providers/launch/introspect`
   (`backend/app/api/routes/providers.py`), autenticandosi come fornitore con
   lo schema HMAC esistente (`X-Provider-ID` + `X-Signature-HMAC`):
   422 intestazione di firma assente, 401 fornitore ignoto o firma falsa,
   403 token scaduto/non valido/di un gioco non suo. Risposta 200:
   `{user_id, game_session_id, game_code, wallet_type, currency, expires_at}`.

## Denaro

Ogni movimento passa dal confine seamless (`/api/v1/seamless/wallet/reserve`,
`commit`, `rollback`) con chiave di idempotenza `(provider_code, tx_id)` su
`platform_rounds`/ledger. Coins **non** usa `game_idempotency_keys` (0063):
quella tabella serve le azioni interne di boxe/hi_lo/mines.

## RTP e matematica

L'RTP e la matematica del gioco sono responsabilita' del fornitore e vivono
nel repository M&M. La piattaforma verifica contabilmente ogni round via
ledger (`backend/app/modules/platform/rounds/service.py`).
