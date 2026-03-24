# CasinoKing – Documento 10

Fairness Model, Randomness, Seed Strategy e Audit Verificabile

Versione progettuale robusta, pensata per evoluzione verso modello public-verifiable

Scopo del documento
Definire come il modulo Mines potrà gestire casualità, seed, nonce, commit-reveal, audit interno e futura verifica esterna. L'obiettivo è partire con un impianto semplice ma corretto, senza bloccare la futura evoluzione verso un fairness model più avanzato.

## 1. Obiettivo

- Separare chiaramente matematica del gioco e sorgente di casualità.
- Definire un random model robusto per la fase iniziale.
- Progettare un percorso evolutivo verso un sistema verificabile dall’utente.
- Lasciare tracce dati sufficienti per audit interno, test e analisi anomalie.

## 2. Principi guida

- Il backend resta la fonte di verità.
- La casualità non deve dipendere dal frontend.
- Ogni partita deve essere ricostruibile a posteriori.
- Il fairness layer deve essere versionato.
- Il motore di gioco non deve cambiare radicalmente quando verrà introdotto il modello avanzato.

## 3. Architettura logica del fairness layer

```text
Player / Frontend UI
Mines API + Session Service
Fairness Facade
Random Source / Seed Engine
Board Derivation Logic
Audit Store + Game Session Data
```

## 4. Fasi del modello

| Fase | Descrizione | Uso | Decisione |
| --- | --- | --- | --- |
| Fase A | Secure server RNG | MVP / demo robusta | Scelta iniziale |
| Fase B | Seeded internal fairness | Audit interno forte | Target intermedio |
| Fase C | Provably fair / user-verifiable | Trasparenza esterna | Evoluzione futura |

## 5. Modello iniziale scelto (Fase A)

- Il server genera casualità con sorgente crittograficamente sicura.
- Il board viene derivato e salvato lato backend.
- La partita conserva metadati sufficienti a ricostruzione e audit interno.
- L’utente non verifica ancora autonomamente la random sequence.
- Il sistema prepara già i campi necessari per una transizione ordinata al modello seed-based.

## 6. Modello target evolutivo (Fase B/C)

- Server seed segreto per batch o per sessione.
- Client seed opzionale o impostabile dall’utente.
- Nonce incrementale per ogni round.
- Commit del server seed tramite hash pubblicabile prima del gioco.
- Reveal del seed o del dato necessario a fine partita o rotazione.
- Algoritmo deterministico di derivazione board a partire da seed/nonce/versione.
- Possibilità futura di pagina di verifica indipendente.

## 7. Componenti dati del fairness model

| Campo | Tipo logico | Uso | Fase |
| --- | --- | --- | --- |
| fairness_version | string | Versione algoritmo fairness | A/B/C |
| server_seed | secret string | Origine random controllata | B/C |
| server_seed_hash | string | Commit pubblico/registrato | B/C |
| client_seed | string | Contributo utente o default | C |
| nonce | integer | Contatore round/sessione | B/C |
| rng_material | bytes/string | Materiale usato per derivazione | A/B/C |
| board_hash | string | Fingerprint board | A/B/C |
| revealed_at | timestamp | Traccia audit di eventuale reveal | B/C |

## 8. Lifecycle dei seed

1. Generazione server seed con generatore sicuro.
2. Salvataggio protetto del seed e calcolo del relativo hash.
3. Pubblicazione o registrazione del commit hash prima dell’uso, dove previsto.
4. Associazione del seed a un round, a una sessione o a una finestra temporale.
5. Uso del seed insieme a nonce e parametri della partita per derivare il board.
6. Chiusura della sessione con memorizzazione dei metadati fairness.
7. Eventuale reveal controllato del seed quando la policy lo consente.
8. Verifica a posteriori tramite algoritmo deterministico e confronto con hash/board.

## 9. Derivazione concettuale del board

- Input logici: fairness_version, server_seed, client_seed opzionale, nonce, grid_size, mine_count.
- Il sistema genera una sequenza pseudo-casuale deterministica a partire dagli input.
- La sequenza viene convertita in posizioni uniche di mine.
- La derivazione deve essere riproducibile byte-per-byte nella stessa versione algoritmo.
- Ogni cambiamento futuro dell’algoritmo richiede incremento di fairness_version.

board_input = fairness_version + server_seed + client_seed + nonce + grid_size + mine_count
stream = deterministic_prng(board_input)
mine_positions = pick_unique_positions(stream, total_cells=grid_size, count=mine_count)

## 10. Commit–reveal model

- Commit = il sistema espone o registra l’hash del server seed prima che il round sia verificabile.
- Reveal = il sistema rende disponibile il server seed quando non crea più vantaggio informativo.
- L’utente o un tool esterno può ricalcolare l’hash e verificare che corrisponda al commit iniziale.
- Successivamente può ricalcolare il board e verificare coerenza con la partita registrata.

| Passo | Dato | Scopo |
| --- | --- | --- |
| Pre-game | server_seed_hash | Impegno crittografico del seed |
| During game | nonce + config partita | Contesto deterministico |
| Post-game / rotate | server_seed | Verifica del commit |

## 11. Livelli di audit

| Livello | Chi verifica | Cosa verifica | Quando |
| --- | --- | --- | --- |
| Audit tecnico interno | Backend / Dev team | Board, logica, seed use | Sempre |
| Audit operativo | Admin / support | Anomalie e dispute | Su richiesta |
| Audit utente verificabile | Player / tool esterno | Commit/reveal e board | Fase C |

## 12. Rischi principali e contromisure

| Rischio | Contromisura | Nota |
| --- | --- | --- |
| Seed leak | Segreti protetti e accesso ristretto | Mai loggare il seed in chiaro |
| Re-use non voluto del nonce | Policy rigida di incremento e unique constraints | Evita collisioni |
| Version drift | fairness_version obbligatoria | Auditabilità |
| Reveal troppo presto | Policy temporale/di chiusura | Evita vantaggi informativi |
| Algoritmo non deterministico | Funzioni pure e test cross-env | Riproducibilità |
| Mismatch commit/seed | Verifiche automatiche di integrità | Rilevazione immediata |

## 13. Estensioni al database / game session

- Aggiungere fairness_version a game_sessions o tabella collegata.
- Aggiungere nonce e riferimenti ai seed quando il modello avanzato sarà attivo.
- Conservare server_seed_hash fin da subito, anche se il reveal esterno non è ancora esposto.
- Separare eventuali secret store e dati applicativi quando il sistema maturerà.
- Rendere audit trail immutabile o fortemente controllato per i campi fairness.

## 14. API candidate per fairness e verifica

| Metodo | Endpoint | Uso | Fase |
| --- | --- | --- | --- |
| GET | /games/mines/fairness/current | Config fairness attiva | A/B/C |
| GET | /games/mines/session/{id}/fairness | Dettaglio fairness della sessione | B/C |
| POST | /games/mines/fairness/rotate | Rotazione seed amministrativa/interna | B/C |
| GET | /games/mines/verify | Endpoint o tool di verifica | C |

## 15. Flusso di verifica utente (target futuro)

1. L’utente recupera server_seed_hash, client_seed, nonce, fairness_version e parametri della partita.
2. Quando la policy lo consente, recupera il server_seed.
3. Ricalcola l’hash del server_seed e verifica che coincida con il commit.
4. Ricalcola il board con l’algoritmo documentato.
5. Confronta il board e l’esito con i dati della sessione.
6. Se tutti i passaggi coincidono, la partita risulta verificabile.

## 16. Piano di transizione consigliato

| Step | Obiettivo | Impatto codice | Priorità |
| --- | --- | --- | --- |
| 1 | Salvare fairness_version e board_hash | Basso | Alta |
| 2 | Incapsulare random source in un adapter | Medio | Alta |
| 3 | Introdurre seed e nonce interni | Medio | Media |
| 4 | Aggiungere commit hash in API/session data | Medio | Media |
| 5 | Costruire tool di verifica | Medio/Alto | Successiva |

## 17. Decisioni prese

- La demo parte con random model robusto lato server.
- Il motore viene però progettato fin da subito per poter passare a seed strategy avanzata.
- Il fairness layer avrà versionamento esplicito.
- Audit e ricostruibilità sono requisiti architetturali, non optional.
- La verifica utente esterna è obiettivo futuro, non requisito immediato dell’MVP.

## 18. Punti aperti

- Policy precisa di rotazione seed.
- Uso o meno del client seed nel prodotto iniziale evoluto.
- Momento esatto del reveal: fine sessione, batch, o finestra temporale.
- Formato del tool/pagina di verifica.
- Conservazione e protezione dei segreti in ambienti multipli.

## 19. Prossimo documento consigliato

- Documento 11 – API Contract dettagliato: payload, error codes, auth, idempotency e versioning.
