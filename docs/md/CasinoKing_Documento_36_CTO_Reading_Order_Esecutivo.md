# CasinoKing - Documento 36

CTO reading order esecutivo

Stato del documento

- Documento operativo nuovo.
- Pensato come porta di ingresso rapida per revisione CTO.
- Non sostituisce i documenti di analisi: li ordina.

## 1. Scopo

Permettere a un revisore tecnico di capire il progetto in modo rapido e corretto, senza partire da file sparsi o da un ordine casuale.

Questo documento dice:

- da dove iniziare
- cosa leggere dopo
- cosa aspettarsi dal codice attuale
- quali sono le decisioni gia' prese
- quali sono i prossimi step concordati

## 2. Lettura consigliata

## 2.1 Primo documento da leggere

- [docs/SOURCE_OF_TRUTH.md](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/SOURCE_OF_TRUTH.md)

Perche':

- definisce le fonti canoniche
- chiarisce la gerarchia tra documenti Word, allegati runtime e documenti operativi interni

## 2.2 Documento base per capire il punto del progetto

- [Documento 33](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_33_Stato_Progetto_Analisi_CTO_Guida_Migrazione.md)

Perche':

- e' la vera guida di stato del progetto
- spiega cosa esiste gia'
- spiega dove il progetto ha mostrato coupling e deviazioni
- spiega le decisioni nuove prese

Questo e' il documento base da cui partire.

## 2.3 Documenti architetturali da leggere subito dopo

1. [Documento 30](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_30_Separazione_Prodotti_Piattaforma_Gioco_Aggregatore.md)
2. [Documento 31](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_31_Contratto_Tra_Platform_Backend_E_Mines_Backend.md)
3. [Documento 34](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_34_Contratto_API_Operativo_Platform_Mines_v1.md)
4. [Documento 35](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_35_Mappatura_Codebase_Attuale_E_Split_Target.md)
5. [Documento 32](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_32_Piano_Migrazione_Da_Monolite_Frontend_A_Prodotti_Separati.md)

Perche':

- `30` definisce la target architecture
- `31` definisce il modello concettuale seamless wallet
- `34` traduce il modello in API concrete
- `35` collega il modello ai file reali del codebase
- `32` ordina l'esecuzione della migrazione

## 2.4 Documenti di vincolo da tenere presenti

1. [Documento 21](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_21_Vincoli_Priorita_Gioco_Mines.md)
2. [Documento 22](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_22_Vincoli_Priorita_Sito_Web_Player.md)
3. [Documento 23](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_23_Vincoli_Priorita_Backend_Piattaforma.md)

Perche':

- fissano i vincoli di priorita' che durante l'implementazione erano stati troppo impliciti

## 3. Come leggere il codebase dopo i documenti

## 3.1 Backend piattaforma

Leggere prima:

- [backend/app/modules/auth/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/auth/service.py)
- [backend/app/modules/wallet/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/wallet/service.py)
- [backend/app/modules/ledger/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/ledger/service.py)
- [backend/app/modules/admin/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/admin/service.py)

Interpretazione:

- questi moduli rappresentano il dominio piattaforma gia' piu' maturo

## 3.2 Backend Mines

Leggere:

- [backend/app/modules/games/mines/fairness.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/fairness.py)
- [backend/app/modules/games/mines/runtime.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/runtime.py)
- [backend/app/modules/games/mines/randomness.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/randomness.py)
- [backend/app/modules/games/mines/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/service.py)

Interpretazione:

- `fairness`, `runtime` e `randomness` sono vicini al dominio gioco corretto
- `service.py` e' il file critico dove oggi convivono gioco e settlement finanziario

## 3.3 Frontend

Leggere:

- [frontend/app/ui/casinoking-console.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/ui/casinoking-console.tsx)
- [frontend/app/ui/mines-standalone.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/ui/mines-standalone.tsx)

Interpretazione:

- `casinoking-console.tsx` e' il contenitore legacy misto
- `mines-standalone.tsx` e' il primo estratto corretto del prodotto gioco

## 4. Punto del progetto in una frase

Le fondamenta piattaforma e il motore Mines esistono gia', ma il progetto ha bisogno ora di una migrazione di confini: da frontend/backend misti verso prodotti separati con integrazione API esplicita.

## 5. Decisioni nuove gia' prese

1. Mines non deve piu' essere trattato come vista del sito.
2. Il backend gioco non deve piu' fare settlement finanziario diretto.
3. La target architecture ufficiale e':
   - `platform-backend`
   - `mines-backend`
   - `web/aggregator`
4. Il modello corretto e' seamless wallet.
5. Serve un `game_launch_token` dedicato.

## 6. Prossimo step concordato

Il prossimo step non e' cosmetico.

E' questo:

1. introdurre il boundary `platform_round_gateway` lato Mines
2. introdurre il service piattaforma per `open_round` e `settle_round`
3. togliere progressivamente da Mines la scrittura diretta su:
   - wallet
   - ledger
   - settlement round

## 7. Uso corretto di questo documento

Questo documento non sostituisce il Documento 33.

Serve a dire al CTO:

- da dove partire
- in che ordine leggere
- dove guardare nel codice
- quale decisione architetturale e' ormai ufficiale
