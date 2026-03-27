# CasinoKing - Documento 22

Vincoli e priorita' operative del sito web player

Stato del documento

- Questo documento e' operativo e vincolante per l'implementazione del sito web player.
- Non sostituisce `docs/SOURCE_OF_TRUTH.md` o i documenti canonici piattaforma/prodotto.
- Va letto insieme a Documento 20 e `docs/PRODUCT_CLOSURE_BACKLOG.md`.

## 1. Obiettivo

Definire in modo esplicito i vincoli del sito player, separandoli dai vincoli del modulo gioco e del backoffice.

## 2. Vincoli assoluti

1. Il sito player e il modulo gioco non sono la stessa cosa.
2. Il sito deve portare il giocatore al gioco, non inglobare il gioco in una UI confusa.
3. `Account` e' area personale del giocatore, non hub misto di navigazione.
4. Il percorso player non deve essere contaminato da elementi backoffice.

## 3. Ordine di priorita'

1. Chiarezza delle aree: lobby, gioco, account.
2. Percorso di accesso semplice: login, registrazione, demo quando previsto.
3. Credibilita' del sito come casino web first-party.
4. Somiglianza estetica ai riferimenti di mercato.
5. Polish grafico secondario.

## 4. Aree del sito player

### 4.1 Lobby

La lobby deve contenere:

- brand
- promo/banner
- categoria `Casino`
- icona/card del gioco Mines
- accesso login/register o stato autenticato

### 4.2 Account

L'account deve contenere solo:

- dati del giocatore
- wallet/balance
- estratto conto
- history delle giocate
- dettaglio mani o sessioni

L'account non deve contenere:

- CTA spurie verso aree non coerenti
- pannelli tecnici di debug
- blocchi duplicati rispetto alla lobby

### 4.3 Auth

Login e register devono stare su pagine dedicate, non dentro il frame del gioco.

## 5. No-go espliciti

- niente login/register dentro Mines
- niente backoffice nel percorso player
- niente account concepito come console tecnica
- niente blocchi duplicati tra lobby e account
- niente messaggi di debug o di integrazione locale nel percorso player finale

## 6. Regola di separazione

Se un elemento appartiene alla navigazione del sito, resta nel sito.

Se un elemento appartiene al gioco, resta nel gioco.

Se un elemento appartiene alla gestione del giocatore, resta in account.

## 7. Cosa fare in caso di dubbio

Se una schermata mescola piu' responsabilita', va semplificata.

Se una CTA non ha una collocazione evidente, non va aggiunta automaticamente.

Se una scelta rende il sito piu' rumoroso o meno leggibile, va fermata e ripensata.
