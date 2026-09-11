# Coins — SPEC (lato piattaforma)

**Stato:** 3bA-3bE CHIUSI CON RISERVE (11/09/2026, commit piattaforma `16dcc17`,
M&M `33cdc38`). 3bF (riapertura produzione) in attesa di decisione di Michele.
Coins e' un gioco
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

## Firma del confine seamless (3bE, 11/09/2026)

La firma HMAC lega **metodo, operazione e corpo**: il messaggio firmato e'
`METODO\nTOKEN-OPERAZIONE\nCORPO` (fonte: `backend/app/modules/providers/auth.py`,
funzioni `messaggio_firmato()` e `token_da_percorso()`). Non il solo corpo:
una firma calcolata col vecchio schema (solo corpo) viene rifiutata con 401,
senza doppia accettazione.

**Token di operazione per rotta** (mappa in `auth.py:TOKEN_OPERAZIONE_PER_ROTTA`,
costruita dal prefisso di configurazione `settings.api_v1_prefix`):

| Token | Rotta |
|---|---|
| `wallet.reserve.v1` | `{prefisso}/seamless/wallet/reserve` |
| `wallet.commit.v1` | `{prefisso}/seamless/wallet/commit` |
| `wallet.rollback.v1` | `{prefisso}/seamless/wallet/rollback` |
| `launch.introspect.v1` | `{prefisso}/providers/launch/introspect` |

Il server verifica contro il token della rotta che **ha ricevuto** la
richiesta, mai contro un token dichiarato dal client. Il confronto del
percorso e' **esatto** (non `endswith`): un proxy o un mount diverso
cambiano `request.url.path`, e la mappa segue la configurazione.

**Codici di errore** (conservati da PIANO-v2 punto 4):

| Codice | Quando |
|---|---|
| 422 | Intestazione `X-Signature-HMAC` assente (FastAPI `Header(...)`) |
| 401 | Provider ignoto, firma falsa, o token di operazione sconosciuto |
| 403 | Token di lancio scaduto/non valido/scope diverso (solo introspezione) |

Il client M&M (`src/games/coins/platform_client.py`) porta una copia
manuale della mappa (`_TOKEN_OPERAZIONE`). Il punto di deriva e' noto;
il collaudo incrociato nel gate (`test_seamless_collaudo_incrociato.py`)
e' la guardia: se i token divergono, i collaudi diventano rossi.

## Denaro

Ogni movimento passa dal confine seamless (`/api/v1/seamless/wallet/reserve`,
`commit`, `rollback`) con chiave di idempotenza `(provider_code, tx_id)` su
`platform_rounds`/ledger. Coins **non** usa `game_idempotency_keys` (0063):
quella tabella serve le azioni interne di boxe/hi_lo/mines.

## RTP e matematica

L'RTP e la matematica del gioco sono responsabilita' del fornitore e vivono
nel repository M&M. La piattaforma verifica contabilmente ogni round via
ledger (`backend/app/modules/platform/rounds/service.py`).
