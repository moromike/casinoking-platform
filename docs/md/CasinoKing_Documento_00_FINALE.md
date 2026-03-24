# CasinoKing – Documento 00 (Versione Finale)

Visione, Strategia, Architettura e Direzione Operativa

## 1. Executive Summary

CasinoKing è progettato come una piattaforma di casino online completa e un ecosistema di giochi proprietari. La strategia adottata privilegia solidità architetturale, scalabilità e controllo totale del prodotto. Non è un prototipo: è una base ingegneristica costruita per evolvere senza refactor distruttivi.

## 2. Natura del progetto (distinzione chiave)

- Piattaforma casino → utenti, wallet, promo, admin, API
- Giochi → moduli indipendenti (es. Mines)

Questa separazione è intenzionale: i giochi devono poter vivere anche fuori dalla piattaforma.

## 3. Principi guida

- Scalabilità fin dall’inizio
- Controllo totale del sistema
- Modularità reale (non teorica)
- Approccio incrementale ma solido
- Open source quando possibile

## 4. Cosa faremo

- Costruire un ledger robusto (cuore del sistema)
- Sviluppare Mines come primo gioco completo
- Creare una piattaforma pronta a crescere
- Preparare il terreno per crypto e real money

## 5. Cosa NON faremo

- Non useremo scorciatoie su wallet/ledger
- Non costruiremo un monolite rigido
- Non introdurremo complessità inutile all’inizio
- Non legheremo i giochi alla piattaforma in modo stretto

## 6. Architettura scelta

- Backend: FastAPI
- Frontend: Next.js
- Database: PostgreSQL
- Cache: Redis
- Container: Docker
- Ledger: double-entry

## 7. Mappa documentale

- Fondazioni → 01–05
- Gioco → 06–09
- Fairness → 10
- API → 11
- Database → 12–13
- Infra → 14
- Execution → 15

## 8. Roadmap operativa

1. Setup ambiente
2. Auth + utenti
3. Wallet + ledger
4. Game session
5. Mines
6. Frontend
7. Admin + bonus
8. Hardening

## 9. Rischi e approccio

- Ledger → test e vincoli
- Concorrenza → transazioni DB
- Gioco → validazione matematica
- Scalabilità → modularità

## 10. Posizione finale

Il progetto è stato progettato in modo coerente e completo. La direzione è definita. Le scelte sono intenzionali. Da questo punto in avanti si entra in esecuzione.
