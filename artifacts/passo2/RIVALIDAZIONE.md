PARTE 1 — CHIUSO

1. **CHIUSO.** Il fatto 3 limita la serializzazione a integrazione/collaudo nell'albero
   servito; analisi, scrittura e revisione possono restare parallele.
2. **CHIUSO.** MET-05 e' limitato alle corse mirate, non a suite, migrazioni e lavoro umano.
3. **CHIUSO.** PASSO 2 e' 2A/2B; PASSO 4 e' 4A/4B/4C, ciascuno con misura e cancello.
4. **CHIUSO.** `CONTRATTO_PASSO2.md` esiste ed e' firmato; fu scritto dopo la sfida.

PARTE 2 — NON CHIUSO

## a) Numeri rilanciati

- I due collaudi nominati: uscita 0, **2 passed in 1.15s**.
- Prima della suite completa: **426/426** payout uguale alla puntata, scostamenti 0;
  **426/426** transazioni con debiti uguali ai crediti, sbilanciate 0.
- Tutti i 426 erano `mines` chiusi per `access_session_timeout`: non sono 426 prove
  indipendenti di BOXE/HI-LO. La suite ha poi aggiunto dati, quindi il DB vivo e' mutato.
- Confermato: `refund_no_progress` e `manual_cashout` producono entrambi `status='won'`.
- Le cinque ricerche dell'allarme sono a zero; `critical` non attiva notifiche: manca.

## b) Verdetto 2A

**Non giustifica la frase generale “scatta sempre quando deve”.** I 426 provano importo
e quadratura dei rimborsi avvenuti, non i rimborsi dovuti ma mai creati. I due test provano
la chiusura esplicita senza progresso di BOXE e HI-LO; la conclusione difendibile va
ristretta a quei percorsi, non all'universalita' del rimborso automatico.

## c-d) P2-03

Non e' latente. `backend/app/modules/account/service.py` espone `pr.status` come `result`;
`frontend-v3/app/ui/player-account-page.tsx` traduce `won` in **“Vinto”** nello
storico/estratto conto del giocatore. Le controricerche cercavano solo calcoli RTP/win-rate
e hanno mancato un consumatore attivo. Era giusto non ripararlo dentro una verifica: serve
un passo separato, ratificato, con migrazione e cambio di specifica; non va pero' rinviato
come problema soltanto futuro.

## e) Cinque cancelli

1. **VERDE** — 2/2 collaudi nominati.
2. **ROSSO** — `02-denaro-nel-registro.md` conserva output ma non le SQL: ha un segnaposto.
3. **ROSSO** — P2-03 dichiara un esito sostanzialmente falso (“latente”).
4. **VERDE** — autotest 28/28; gate completo verde, 692 eseguiti/947 raccolti.
5. **VERDE** — diff `84b9878^..84b9878 -- tests/` vuoto.

Il passo e' partito col gate d'ingresso ancora `BLOCCA/in corso`: questo via libera non e' retroattivo.
