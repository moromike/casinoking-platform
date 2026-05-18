Status: ACTIVE
Last meaningful update: 2026-05-18

# BOXE Manual Playthrough Checklist

Checklist locale per review finale BOXE su ambiente `localhost`.

## Pre-check

- [ ] Backend, frontend, PostgreSQL e Redis sono healthy.
- [ ] Branch validation corrente e database migrato includono BOXE 4B+5+6.
- [ ] Login admin disponibile.
- [ ] Login player disponibile con saldo cash e, se necessario, bonus.

## Admin - Title Editor

- [ ] Aprire Backoffice -> Games -> BOXE / `boxe001`.
- [ ] Verificare tab Overview caricato senza errori.
- [ ] In Game config, impostare `rows_enabled`, `default_rows`, `difficulty_enabled`, `default_difficulty`.
- [ ] In Copy & i18n, verificare le lingue `it`, `en`, `de`, `es`.
- [ ] In Rules HTML, verificare la sezione regole BOXE.
- [ ] Salvare draft.
- [ ] Pubblicare live.
- [ ] Riaprire l'editor e verificare che draft e published siano coerenti.

## Admin - Assets And Theme

- [ ] Aprire tab Assets / Lobby card.
- [ ] Caricare o verificare preview `game_card`.
- [ ] Caricare o verificare preview `symbol_safe`.
- [ ] Caricare o verificare preview `symbol_mine`.
- [ ] Provare un upload invalido e verificare errore di validazione.
- [ ] Verificare delete/restore o fallback asset se applicabile.
- [ ] Aprire tab Theme.
- [ ] Salvare draft theme.
- [ ] Pubblicare live theme.

## Admin - Site/Lobby

- [ ] Aprire Site/Lobby publication.
- [ ] Rendere visibile `boxe001`.
- [ ] Abilitare demo.
- [ ] Abilitare real.
- [ ] Verificare che il master title `boxe` resti hidden/non lanciabile.
- [ ] Salvare/pubblicare la configurazione sito.

## Player - Lobby And Launch

- [ ] Aprire lobby player.
- [ ] Verificare card BOXE visibile con immagine/fallback corretti.
- [ ] Cliccare BOXE e aprire Launch Cashier.
- [ ] Lanciare demo: URL atteso `/boxe?title_code=boxe001&mode=demo`.
- [ ] Lanciare real cash: URL atteso `/boxe?title_code=boxe001&mode=real_cash&wallet_source=real`.
- [ ] Lanciare real bonus: URL atteso `/boxe?title_code=boxe001&mode=real_bonus&wallet_source=bonus`.

## Player - Gameplay

- [ ] Completare boot: provider intro -> how-to-play -> table balance.
- [ ] Impostare rows/difficulty e bet.
- [ ] Demo: BET -> safe reveal -> COLLECT.
- [ ] Verificare stato `completed cashout`.
- [ ] Demo: nuovo round -> pick mine -> stato `failed mine`.
- [ ] Verificare reveal loss: solo riga corrente, righe superiori coperte.
- [ ] Demo: safe path fino top row -> stato `completed top row`.
- [ ] Real cash: round safe + cashout, saldo cash aggiornato.
- [ ] Real bonus: round safe + cashout, saldo bonus aggiornato.
- [ ] Simulare retry rete se possibile e verificare replay idempotente.
- [ ] Mobile portrait: gameplay usabile.
- [ ] Landscape short: rotation gate visibile.

## Replay, History, Finance

- [ ] Aprire replay di round BOXE chiuso.
- [ ] Verificare fairness artifacts e assenza di hidden active state.
- [ ] Aprire Account -> statement movements.
- [ ] Verificare movimenti BOXE bet/settlement con label coerente.
- [ ] Aprire Admin -> Financial sessions.
- [ ] Verificare sessione BOXE visibile.
- [ ] Aprire drilldown BOXE e confrontare bet, payout, wallet type e round metadata.

## Regression

- [ ] Mines lobby e launch ancora funzionanti.
- [ ] Mines smoke browser ancora verde.
- [ ] BOXE visual baseline verde.
- [ ] Mines visual baseline aggiornata post RTP 98% e verde.
