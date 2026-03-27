# CasinoKing - Documento 21

Vincoli e priorita' operative del modulo gioco Mines

Stato del documento

- Questo documento e' operativo e vincolante per l'implementazione del modulo gioco Mines.
- Non sostituisce `docs/SOURCE_OF_TRUTH.md` o i documenti canonici Mines.
- Va letto insieme a Documento 06, Documento 07 v2, Documento 09 v2, Documento 10 e agli allegati runtime.

## 1. Obiettivo

Definire in modo esplicito i vincoli di priorita' del gioco Mines, per evitare deviazioni UX o di prodotto incompatibili con la direzione del progetto.

## 2. Vincoli assoluti

1. Mines e' un modulo gioco separabile dal sito.
2. Il frame del gioco non deve dipendere concettualmente dalla lobby CasinoKing.
3. Il frame del gioco deve poter essere integrato in futuro anche su altri siti o shell esterne.
4. Mines resta server-authoritative.
5. Outcome, board, payout e cashout non sono decisi dal frontend.
6. Il gioco non deve contenere elementi di marketing, CMS o navigazione sito non indispensabili al gameplay.

## 3. Ordine di priorita'

1. Separazione tra gioco e sito.
2. Correttezza del flusso di gioco rispetto ai vincoli server-authoritative.
3. Giocabilita' reale e leggibilita' del tavolo.
4. Somiglianza grafica al riferimento prodotto.
5. Polish visivo secondario.

## 4. Shell di gioco consentita

Dentro il frame di gioco possono stare solo elementi coerenti con un tavolo di gioco:

- brand/wordmark del gioco
- controlli di configurazione della puntata
- board
- pulsanti gameplay essenziali
- balance / win / stato round
- pannello regole
- hand report se resta coerente con l'esperienza prodotto
- pulsante uscita dal gioco

## 5. No-go espliciti

Dentro il frame di gioco non devono comparire:

- login
- register
- call to action marketing
- promo sito
- route account
- route lobby
- blocchi backoffice
- controlli wallet `cash/bonus` lato tavolo
- fallback UX inventati senza approvazione

## 6. Regole UX specifiche

1. La griglia deve essere visibile subito.
2. La preview della griglia deve aggiornarsi immediatamente quando cambiano `grid size` o `mines`.
3. Il gioco non deve aspettare `Bet` per mostrare la nuova configurazione visuale.
4. Il pannello regole deve aprirsi come overlay o schermata dedicata chiudibile.
5. Le regole non devono essere lasciate come testo buttato nella pagina.
6. Il saldo deve essere coerente con la modalita' player/demo attiva.

## 7. Modalita' demo

La demo e' consentita, ma:

- non deve diventare una simulazione client-side arbitraria
- deve restare compatibile con il backend reale
- deve partire da 1000 CHIP
- deve resettere il saldo demo all'uscita o alla riapertura del gioco

## 8. Cosa fare in caso di dubbio

Se una scelta migliora l'aspetto ma riduce la separazione tra gioco e sito, va rifiutata.

Se una scelta semplifica il flusso ma introduce elementi pubblici nel frame del gioco, va rifiutata.

Se una scelta non e' esplicitamente richiesta e puo' cambiare la natura del frame Mines, va fermata e discussa prima.
