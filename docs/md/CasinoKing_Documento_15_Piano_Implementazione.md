# CasinoKing – Documento 15

Piano di implementazione reale: milestone, ordine sviluppo, rischi e task

## 1. Obiettivo

- Passare da teoria a implementazione reale
- Definire ordine sviluppo chiaro
- Ridurre rischi e blocchi

## 2. Strategia generale

- Costruire prima backbone (auth + wallet + db)
- Poi primo gioco (Mines)
- Poi admin e bonus
- Poi miglioramenti (fairness avanzata, UX)

## 3. Milestone principali

1. M1 – Setup ambiente + repo + Docker
2. M2 – Auth + User + Login
3. M3 – Wallet + Ledger funzionante
4. M4 – Game session base
5. M5 – Mines funzionante (MVP)
6. M6 – Admin base + bonus
7. M7 – Hardening + fairness evolution

## 4. Ordine sviluppo tecnico

- Database + migrations
- Backend base (FastAPI)
- Auth system
- Wallet + ledger
- Game engine Mines
- Frontend base
- Admin panel base

## 5. Task concreti iniziali

1. Creare repo GitHub
2. Setup Docker locale
3. Implementare schema DB
4. Endpoint auth base
5. Creare wallet utente
6. Accredito chip iniziale

## 6. Rischi principali

- Errore su ledger (critico)
- Gestione concorrenza
- Bug logica gioco
- Architettura troppo complessa troppo presto

## 7. Strategie anti-rischio

- Test su ledger prima di tutto
- Transazioni DB sempre atomiche
- Logging chiaro
- Versioning API

## 8. Definizione MVP reale

- Login funzionante
- Wallet con chip
- Mines giocabile
- UI semplice
- No crypto, no complessità extra

## 9. Timeline realistica (indicativa)

- Settimana 1: setup + auth
- Settimana 2: wallet + ledger
- Settimana 3: Mines backend
- Settimana 4: frontend + integrazione

## 10. Decisione importante

- Procedere in modo incrementale, non perfetto
- Meglio funzionante che teoricamente perfetto

## 11. Fine fase metodologica

- Questo è l’ultimo documento metodologico
- Da ora si entra in IMPLEMENTAZIONE reale
