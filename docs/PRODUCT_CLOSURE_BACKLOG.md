# CasinoKing Product Closure Backlog

Nota

- Questo file e' un backlog operativo interno.
- Non sostituisce i documenti canonici in `docs/word/`.
- Le priorita' sotto derivano da `docs/SOURCE_OF_TRUTH.md`, dal Documento 06 Mines, dal Documento 11 API e dal Documento 15 Piano Implementazione.
- I vincoli operativi aggiuntivi sono fissati anche in:
  - `docs/md/CasinoKing_Documento_21_Vincoli_Priorita_Gioco_Mines.md`
  - `docs/md/CasinoKing_Documento_22_Vincoli_Priorita_Sito_Web_Player.md`
  - `docs/md/CasinoKing_Documento_23_Vincoli_Priorita_Backend_Piattaforma.md`

## Obiettivo Finale

Portare CasinoKing da MVP tecnico robusto a prodotto credibile e chiudibile:

- sito player con lobby e apertura giochi coerente
- Mines presentabile come gioco reale
- account player con wallet e storico partite
- backoffice admin usabile per bonus, adjustment, session inspection e reporting
- core finanziario e lifecycle Mines ancora protetti da test, idempotenza e controlli di concorrenza

## Principi Di Esecuzione

- Non rompere i vincoli finanziari o server-authoritative.
- Non inventare behavior documentali ancora aperti.
- Spingere forte sulla UX senza indebolire ledger, ownership o fairness.
- Lavorare per stream paralleli con commit piccoli e verifiche frequenti.

## Stream P0

### P0-A Shell Player E Revisione Grafica

Obiettivo:
Trasformare il frontend da console MVP a shell player credibile.

Sottoattivita':
1. Definire visual system operativo: palette, typography, spacing, card, button, badge, panel, empty state, modal.
2. Costruire home/lobby player con header, hero, card gioco Mines e call-to-action coerenti.
3. Separare davvero la IA player da quella admin, con route dedicate e copy English coerente con i documenti.

Done quando:
- la home non appare piu' come console tecnica
- esiste un entry point chiaro al gioco da card/icona
- admin non compare piu' nel percorso primario del player
- il layout regge desktop e mobile

### P0-B Mines Surface Completa

Obiettivo:
Rendere Mines un gioco credibile e leggibile lato player.

Sottoattivita':
1. Costruire il game launch flow completo: apertura da lobby, configurazione partita, start e CTA di resume active game.
2. Ridisegnare board e HUD: bet, wallet sorgente, progress, multiplier, payout ladder, rischio residuo, payout potenziale, cashout state, feedback win/loss.
3. Rifinire gli stati sessione: loading, active, won, lost, recover, error, recap finale e fairness summary minima visibile.

Done quando:
- l'apertura del gioco parte dalla lobby
- la schermata gioco ha gerarchia visiva chiara
- esiste un resume flow credibile anche oltre il solo localStorage
- il player capisce sempre stato, rischio e prossima azione

### P0-C Account Player

Obiettivo:
Dare al giocatore un account vero, non solo form e wallet grezzi.

Sottoattivita':
1. Creare dashboard account con saldi wallet, stato sessione corrente e scorciatoie principali.
2. Aggiungere storico partite Mines con lista sessioni, esito, bet, payout, data e drill-down.
3. Rifinire i flussi auth/account: login, registrazione, reset password, messaggi, recovery e stato autenticato.

Done quando:
- il player ha una home account leggibile
- puo' vedere il proprio storico partite
- auth e sessione non sembrano piu' componenti di debug

## Stream P1

### P1-A Backoffice Admin

Obiettivo:
Separare e maturare il backoffice admin.

Sottoattivita':
1. Creare layout admin dedicato con login, navigazione e pannelli separati dal frontend player.
2. Costruire il dettaglio utente admin con wallet, azioni manuali, bonus grant, adjustment e stato account.
3. Rifinire strumenti operativi con conferme, feedback chiari, ultimi risultati e audit visibile.

Done quando:
- admin e player hanno esperienze distinte
- un admin puo' operare su utenti senza usare una console mista
- i flussi bonus/adjustment sono leggibili e affidabili

### P1-B Reporting Finanziario E Di Gioco

Obiettivo:
Portare reporting fuori dalla sola logica MVP di admin.

Sottoattivita':
1. Stabilizzare le viste ledger: report contabile, ultime transazioni, riconciliazione wallet/ledger e drill-down.
2. Aggiungere reporting di gioco: sessioni, esiti, bet aggregate, payout e attivita' recente.
3. Preparare il perimetro del modulo `reporting` come dominio separato dal solo `admin.service`.

Done quando:
- admin vede report leggibili e navigabili
- esiste una vista gioco oltre al solo report ledger
- il reporting ha un confine tecnico piu' chiaro

### P1-C Hardening Finale Mines

Obiettivo:
Chiudere il core del gioco prima della fase successiva.

Sottoattivita':
1. Consolidare policy residue su lifecycle, terminal states, board reveal finale e recover state senza violare i documenti.
2. Rafforzare test di concorrenza, idempotenza, ownership e regressione su flussi sensibili.
3. Chiudere audit/fairness admin e coerenza tra sessione, payout runtime e dati verificabili.

Done quando:
- i path sensibili hanno copertura robusta
- Mines e' stabile anche sotto race e retry
- fairness e audit restano coerenti con i vincoli correnti

## Stream P2

### P2-A Confini Di Dominio

Obiettivo:
Preparare la crescita del progetto senza refactor prematuri.

Sottoattivita':
1. Ripulire i confini tra shell piattaforma, modulo Mines e backoffice.
2. Decidere cosa resta nel monolite MVP e cosa verra' estratto in seguito.
3. Ridurre il peso della singola console monolitica lato frontend.

Done quando:
- il frontend non e' piu' tutto concentrato in un solo file
- i confini appaiono intenzionali
- la crescita futura non richiede riscrittura

### P2-B Documentazione Operativa E Release Readiness

Obiettivo:
Rendere il progetto eseguibile e verificabile con meno attrito.

Sottoattivita':
1. Documentare il flusso locale player/admin aggiornato con credenziali, startup e smoke checks.
2. Aggiungere checklist di regressione per player flow, admin flow e Mines flow.
3. Tenere allineati smoke test frontend e verifiche container/build.

Done quando:
- il runbook locale e' chiaro
- i flussi principali hanno checklist ripetibili
- la regressione base e' veloce da eseguire

## Ordine Consigliato

1. P0-A Shell Player E Revisione Grafica
2. P0-B Mines Surface Completa
3. P0-C Account Player
4. P1-A Backoffice Admin
5. P1-B Reporting Finanziario E Di Gioco
6. P1-C Hardening Finale Mines
7. P2-A Confini Di Dominio
8. P2-B Documentazione Operativa E Release Readiness

## Esecuzione Parallela Consigliata

Processo 1:
- P0-A Shell Player E Revisione Grafica

Processo 2:
- P0-B Mines Surface Completa

Processo 3:
- P0-C Account Player

Processo 4:
- P1-A Backoffice Admin
- P1-B Reporting Finanziario E Di Gioco

Processo 5:
- P1-C Hardening Finale Mines
- P2-B Documentazione Operativa E Release Readiness

## Prima Wave Di Delivery

Wave 1:
- visual system
- lobby player
- game card Mines
- layout gioco Mines

Wave 2:
- account player
- storico partite
- backoffice admin separato

Wave 3:
- reporting finanziario e di gioco
- hardening finale Mines
- cleanup confini frontend

## Riassunto

Il progetto non e' fermo, ma e' ancora al livello "MVP tecnico forte". Questo backlog serve a chiudere il salto verso il prodotto reale. La priorita' non e' aggiungere feature casuali: e' completare in sequenza e in parallelo i blocchi che rendono CasinoKing percepibile come piattaforma gambling seria, senza rompere i vincoli forti su ledger, ownership, idempotenza e server-authoritative Mines.
