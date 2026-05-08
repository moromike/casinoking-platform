# Player Account UX Redesign Plan

Documento di progetto per review CTO.

## Stato del documento

- Tipo: piano UX/UI area account player.
- Stato: approvato; PA-UX-1 overview account completata frontend-only; PA-UX-3 estratto conto grouped/expandable completata frontend-only.
- Ambito: `/account`, profilo player, sicurezza/cambio password, cassa/wallet, estratto conto, storico sessioni, dettaglio espandibile.
- Non sostituisce: documenti financial core, ledger, wallet, atlas platform o backlog prodotto.

Aggiornamento 2026-05-08:

- PA-UX-1 completata senza modifiche backend: `/account` apre una tab
  `Overview` che riassume saldo disponibile da wallet snapshot, ultima sessione
  Mines dai dati gia' caricati, attivita' recente da transazioni esistenti e
  link rapidi alle sezioni Cassa, Estratto conto, Profilo e Sicurezza.
- PA-UX-3 completata senza modifiche backend: la tab `Estratto Conto`
  mostra le sessioni Mines come cards summary-first con accordion di dettaglio,
  mantiene il dettaglio round espanso con tabella desktop e card list mobile, e
  usa solo `statementGroups`/dati gia' caricati.
- Nessun endpoint, schema, wallet, ledger, payout, RNG o settlement e' stato
  modificato.

## Perche' esiste questo documento

L'area account player oggi funziona, ma parla ancora troppo da sviluppatore.

Il player vede wallet, sessioni, transazioni e dettagli tecnici in modo piuttosto grezzo. Questo e' utile durante lo sviluppo, ma non e' una buona esperienza prodotto.

L'obiettivo e' trasformare `/account` in una vera area personale:

1. prima vista riassuntiva;
2. dettagli solo quando il player li espande;
3. linguaggio comprensibile;
4. grafica coerente con la lobby e con Mines;
5. nessuna semplificazione del modello finanziario sottostante.

## Stato attuale osservato

File principale:

- `frontend/app/ui/player-account-page.tsx`

Comportamento attuale:

- tab `Profilo`;
- tab `Sicurezza`;
- tab `Cassa`;
- tab `Estratto Conto`;
- caricamento parallelo di `/auth/me`, `/wallets`, `/ledger/transactions`, `/games/mines/sessions`;
- storico Mines raggruppato per access session;
- dettaglio round espandibile;
- cambio password funzionante;
- transazioni recenti mostrate in forma tecnica.

Problemi principali:

- copy misto italiano/inglese;
- gerarchia visiva debole;
- estratto conto ancora table-heavy;
- transazioni ledger mostrate come eventi tecnici;
- profilo e sicurezza sembrano form di debug;
- la prima vista non risponde subito a "come sto andando?" e "cosa e' successo di recente?";
- mobile e responsive da rifinire;
- manca una distinzione chiara tra saldo, attivita' recente, sessioni e dettagli contabili.

## Principi UX

### 1. Summary first

La prima vista deve dire subito:

- saldo disponibile;
- ultimo gioco/sessione;
- risultato recente;
- stato account;
- azioni principali.

Il dettaglio arriva dopo, su click.

### 2. Linguaggio player, non ledger

Mostrare:

- "Giocato";
- "Vinto";
- "Risultato";
- "Sessione";
- "Saldo";
- "Movimenti".

Evitare come testo primario:

- `ledger_transactions`;
- `reference_type`;
- `transaction_type` raw;
- id lunghi;
- status tecnici senza traduzione.

I dettagli tecnici possono restare in pannelli espansi o in modalita' support/debug.

### 3. Verita' contabile intatta

La UI puo' aggregare, arrotondare e spiegare. Non puo':

- cambiare ledger;
- nascondere eventi economici obbligatori;
- inventare saldo;
- sommare in modo incoerente con wallet/ledger;
- perdere il riferimento a round/sessioni in caso di contestazione.

### 4. Progressive disclosure

Ogni sezione deve avere:

- riga o card riassuntiva;
- bottone dettaglio;
- dettaglio espandibile con dati completi;
- eventuale link a supporto futuro.

### 5. Mobile first

Le tabelle larghe vanno evitate nella prima view. Su mobile usare card, accordion o detail drawer.

## Architettura informativa target

```text
/account
  Overview
    - saldi
    - attivita' recente
    - ultima sessione Mines
    - sicurezza profilo

  Cassa
    - saldo real/bonus/demo se applicabile
    - ultimi movimenti
    - filtri semplici

  Estratto conto
    - gruppi per giorno/sessione
    - summary giocato/vinto/netto
    - dettaglio espandibile

  Sessioni di gioco
    - cards sessione
    - round summary
    - dettaglio round/fairness ids

  Profilo
    - dati personali
    - contatti
    - stato account

  Sicurezza
    - cambio password
    - stato sessione
    - future protezioni
```

## Vista target: Overview

Contenuti:

- card saldo principale;
- card saldo bonus se presente;
- card "Ultima sessione";
- card "Risultato ultimi 7 giorni" se i dati lo consentono;
- card "Sicurezza account";
- CTA leggere: vai a estratto conto, cambia password, continua a giocare.

Esempio contenuto:

```text
Saldo disponibile
1,000.00 CHIP

Ultima sessione Mines
3 round - risultato +12.40 CHIP

Attivita' recente
5 movimenti questa settimana
```

Nota:

- se i dati 7 giorni non sono disponibili in modo pulito, usare solo "ultime attivita'" calcolate client-side dalle sessioni caricate.

## Vista target: Cassa

Obiettivo:

- mostrare saldo e movimenti in modo leggibile.

Prima vista:

- saldo per wallet;
- variazione recente;
- ultimi 3-5 movimenti tradotti;
- stati vuoti chiari.

Dettaglio espandibile:

- tipo movimento;
- data;
- importo se disponibile;
- riferimento round/sessione;
- id tecnico abbreviato.

Nota importante:

- oggi `/ledger/transactions` potrebbe non esporre tutti gli importi in modo adatto alla UI player. Se manca dato utile, prima slice deve adattarsi ai dati disponibili e documentare l'eventuale endpoint futuro. Non si devono derivare importi ambigui con euristiche fragili.

## Vista target: Estratto conto

La sezione piu' importante va ridisegnata in due livelli.

### Livello 1: gruppi leggibili

Raggruppare per sessione o giorno:

```text
Mines - 8 maggio 2026
3 round
Giocato 15.00 CHIP
Vinto 22.40 CHIP
Risultato +7.40 CHIP
[Dettaglio]
```

### Livello 2: dettaglio espanso

Mostrare:

- round;
- orario;
- puntata;
- mine count;
- esito;
- payout;
- wallet;
- id round abbreviato;
- eventuale access session id;
- eventuale platform round/display id quando sara' definito.

La tabella puo' restare dentro il dettaglio su desktop, ma su mobile deve diventare card list.

## Vista target: Sessioni di gioco

Obiettivo:

- separare "estratto conto" da "storia gioco".

Session card:

- gioco/Title;
- stato sessione;
- inizio/fine;
- numero round;
- totale giocato;
- totale vinto;
- netto;
- dettaglio round.

Dettaglio round:

- configurazione Mines;
- safe reveals;
- stato finale;
- payout;
- link futuro a fairness/session detail;
- id tecnico solo come metadato.

Questa separazione evita che l'estratto conto diventi l'unico posto dove leggere sia finanza sia storia di gioco.

## Vista target: Profilo

Prima vista:

- nome;
- email;
- telefono;
- codice fiscale;
- stato account;
- data creazione account.

Interazione:

- per ora read-only se non esistono endpoint di modifica profilo player;
- se si aggiunge edit profilo, serve piano dedicato su validazione e audit.

## Vista target: Sicurezza

Obiettivo:

- rendere il cambio password meno grezzo e piu' chiaro.

Contenuti:

- box cambio password;
- requisiti minimi password;
- feedback successo/errore chiaro;
- stato sessione corrente;
- futuro: logout da tutti i dispositivi, 2FA, email verification.

Out of scope MVP:

- 2FA;
- KYC;
- upload documenti;
- gestione dispositivi reale;
- recovery avanzata.

## Slice operative

### PA-UX-0 - Audit UI e dati disponibili

Obiettivo:

- verificare endpoint, tipi dati, importi disponibili e stati reali;
- mappare cosa puo' essere mostrato senza backend change.

File da guardare:

- `frontend/app/ui/player-account-page.tsx`;
- `frontend/app/account/page.tsx`;
- `frontend/app/lib/types.ts`;
- route backend `/auth/me`, `/wallets`, `/ledger/transactions`, `/games/mines/sessions`.

Output:

- mini inventario dati;
- decisione se serve endpoint aggiuntivo.

### PA-UX-1 - Overview account

Stato: completata frontend-only.

Obiettivo:

- aggiungere una tab o sezione default `Overview`;
- mostrare saldi e attivita' recente come summary.

Scope:

- nessun backend change se possibile;
- nessun nuovo dato finanziario inventato;
- empty/loading/error states.

### PA-UX-2 - Cassa e movimenti

Obiettivo:

- ridisegnare tab Cassa;
- tradurre i movimenti recenti;
- esporre dettagli su click.

Possibile backend need:

- solo se `/ledger/transactions` non espone dati minimi per importo/segno/riferimento.

### PA-UX-3 - Estratto conto grouped/expandable

Stato: completata frontend-only.

Obiettivo:

- sostituire la tabella primaria con gruppi card/accordion;
- mantenere dettaglio round completo espandibile.

Regola:

- desktop puo' usare tabella nel dettaglio;
- mobile deve usare card list.

### PA-UX-4 - Session detail

Obiettivo:

- creare detail drawer o pannello dedicato per una sessione.

Contenuti:

- dati sessione;
- round;
- ids tecnici abbreviati;
- eventuale link fairness quando il flusso lo consente.

### PA-UX-5 - Profilo e sicurezza polish

Obiettivo:

- rendere profilo e cambio password coerenti con il resto dell'app;
- copy unico;
- feedback leggibile;
- validazione UI minima.

### PA-UX-6 - QA responsive e accessibilita'

Obiettivo:

- controllare desktop e mobile <= 375px;
- verificare focus, label, stati vuoti, loading e errori;
- evitare overlap e tabelle ingestibili.

## Endpoint e contratti dati

Preferenza:

- prima provare a usare gli endpoint esistenti;
- aggiungere endpoint solo se il frontend deve fare aggregazioni fragili o costose.

Endpoint futuro possibile:

```text
GET /account/summary
```

Payload concettuale:

```text
wallets[]
recent_activity[]
recent_game_sessions[]
security_status
```

Endpoint futuro possibile:

```text
GET /account/statement
```

Payload concettuale:

```text
groups[]
  date/session
  total_staked
  total_won
  net
  entries[]
```

Decisione:

- non introdurre questi endpoint finche' PA-UX-0 non dimostra che servono.

## Regole financial e compliance

Questo cantiere non deve:

- modificare ledger model;
- modificare wallet snapshot;
- cambiare double-entry;
- cambiare payout o session state;
- nascondere transazioni ledger necessarie;
- fare update diretti di saldo;
- introdurre deposito/prelievo reale.

Puo':

- cambiare layout;
- cambiare copy;
- aggregare dati gia' esistenti;
- abbreviare id tecnici in UI;
- mettere dettagli tecnici dietro espansione;
- aggiungere endpoint read-only se motivati.

## Criteri di accettazione

Il redesign e' accettabile se:

- la prima view e' riassuntiva;
- ogni summary ha dettaglio espandibile;
- il player capisce saldo, attivita' e ultime sessioni senza leggere id tecnici;
- gli stati empty/loading/error sono curati;
- mobile 375px non rompe layout;
- wallet/ledger reconciliation non e' toccata;
- nessun endpoint economico sensibile viene modificato senza test dedicati.

## Rischi

| Rischio | Mitigazione |
| --- | --- |
| Aggregazioni incoerenti con ledger | Usare dati backend o aggregazioni semplici e verificabili; non inventare importi mancanti. |
| UI bella ma meno trasparente | Tenere dettaglio espandibile con riferimenti tecnici. |
| Scope creep su KYC/depositi | Dichiarare out of scope MVP. |
| Tabelle non mobile-friendly | Card/accordion come primary pattern mobile. |
| Mischiare account player e admin finance | Linguaggio player e solo dati del player autenticato. |

## Decisioni da validare con CTO

| Decisione | Proposta |
| --- | --- |
| Default tab | Aggiungere `Overview` come prima vista. |
| Estratto conto | Card/accordion summary first, dettaglio espandibile. |
| Endpoint nuovi | Solo dopo audit PA-UX-0 se i dati attuali non bastano. |
| Profilo editabile | Out of scope finche' non esiste requisito dedicato. |
| Depositi/prelievi | Out of scope MVP; non simulare flussi finanziari nuovi. |
| Fairness link | Preparare spazio nel dettaglio, implementare solo se contract/UI e' chiaro. |

## Sequenza consigliata

1. PA-UX-0 audit dati e schermata attuale.
2. PA-UX-1 overview account.
3. PA-UX-3 estratto conto grouped/expandable.
4. PA-UX-5 profilo/sicurezza polish.
5. PA-UX-6 QA responsive.
6. PA-UX-2/4 se i dati movimento/sessione richiedono ulteriore separazione.

Motivo:

- l'overview sblocca subito il salto di qualita';
- l'estratto conto e' la parte piu' sentita dal player;
- PA-UX-3 precede deliberatamente PA-UX-2 anche se la cassa viene prima nell'architettura informativa: prima si stabilizza la lettura sessioni/round, poi si decide se i movimenti wallet richiedono dati o endpoint dedicati;
- profilo/sicurezza sono importanti ma meno rischiosi;
- gli endpoint nuovi vanno decisi solo dopo aver visto il limite reale dei dati attuali.
