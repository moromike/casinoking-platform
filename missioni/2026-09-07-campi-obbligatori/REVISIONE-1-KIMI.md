DA CORREGGERE

sha256 del testo riletto: a68b87eb8cc6c2fbc34182c1ab6b578cdb95aefdd046f666ec8c641cba9599c1
(ricalcolata estraendo il blocco fra INIZIO/FINE TESTO PROPOSTO da PROPOSTA-campi-obbligatori.md: coincide)

## 1. Fa quello che dice, e solo quello?

Si, sul file. Confronto riga per riga con il `router.py` attuale: le uniche differenze sono
l'import di `ConfigDict`, il modello `_RichiestaSeamless` (righe 102-125 del testo proposto),
l'eredita' nei tre modelli, `reserve_tx_id` su `CommitRequest` (riga 138) e `RollbackRequest`
(riga 143), e i commenti esplicativi. I tre handler (`reserve_funds`, `commit_funds`,
`rollback_funds`) sono byte-identici all'attuale: nessuna logica contabile toccata, come
dichiarato. I nuovi campi (`timestamp`, `nonce`, `currency`, `provider_code`) sono dichiarati
ma **mai letti dagli handler** — la proposta lo ammette in "Cosa NON copre" (POR-03 rimandato),
quindi e' coerente, ma va detto chiaro: questa patch da sola non lega nulla, obbliga solo la
presenza.

## 2. Rompe un chiamante legittimo esistente? SI.

`tests/integration/test_seamless_parita_contabile.py` — collaudo verde sul percorso del
denaro — spacca. Il suo payload di `reserve` (righe 14-22) manda solo
`user_id, game_session_id, game_code, wallet_type, tx_id, amount`: mancano
`provider_code, currency, timestamp, nonce`. Il suo `commit` (righe 41-49) manca anche di
`reserve_tx_id`. Entrambi i test si aspettano `status_code == 200` (righe 38 e 58); con la
proposta applicata ricevono **422** da pydantic. Il criterio di verifica della proposta
("nessuno degli altri collaudi deve peggiorare") fallisce cosi' com'e' scritta: la proposta
non dichiara di dover toccare quel file, e va corretta includendo l'aggiornamento dei payload
di `test_seamless_parita_contabile.py` (campi nuovi + `reserve_tx_id` nel commit).

`test_seamless_fornitore_sospeso.py` invece sopravvive: il suo `_payload` (righe 24-43)
include gia' tutti i campi nuovi, `reserve_tx_id` compreso.

## 3. extra="forbid" e' sicuro?

Per i chiamanti reali in repo, si: nessun test manda campi extra. L'unico documento che li
manderebbe (`docs/INT-04_Provider_Integration_API.md`, con `player_id`/`transaction_id`/
`win_amount`) e' gia' stale rispetto al codice attuale, quindi non e' un chiamante legittimo.
Su un percorso denaro forbid e' la scelta giusta; interagisce senza problemi con l'HMAC, che
firma il body grezzo prima della validazione. Nota minore: il 422 di FastAPI scatta prima del
confronto provider/game, quindi i test "saldo invariato" restano veri (niente scrittura
possibile su payload rifiutato).

## 4. Manca un campo obbligatorio?

No. L'insieme coincide con `PROTOCOL_REQUIRED_FIELDS` di `test_seamless_campi_obbligatori.py`
(righe 40-53) e con la tabella della proposta. `timestamp: str` (riga 123) non e' validato
come data e `nonce` non ha controllo di unicita': lacuna nota, esplicitamente rimandata a
POR-03, accettabile a patto che il gate di fase non tratti PRO-01 come anti-replay chiuso.

## Verdetto

**DA CORREGGERE**: la patch e' pulita e mirata, ma applicata cosi' fa passare i 6 rossi
nuovi e ne accende di uguali su `test_seamless_parita_contabile.py`, che la proposta non
menziona. Basta estendere la proposta con l'aggiornamento di quel file di collaudo; il codice
proposto in se' non ha difetti bloccanti.
