# CAP-04 — CIO' CHE RESTA SU MINES, E PERCHE'

**5 settembre 2026.** Regola del contratto: *«Quelli che pretendono cose che sono davvero
dei giochi non si toccano: si dichiarano, col numero e la riga.»* Questo e' l'elenco.

Non e' una lista di rinunce. E' **il perimetro vero**: la riga dove finisce la piattaforma
e comincia un gioco. Dove il confine e' piu' avanti di quanto pensassimo, e' scritto.

---

## 1. Cose che sono DAVVERO di un gioco — non si ricuciono, e va bene cosi'

La cavia non ha matematica: l'esito lo decide chi chiama. Non ha una griglia, non ha semi,
non ha una progressione. Qualunque collaudo su queste cose **deve** restare su un gioco vero.

| File e riga | Che cosa verifica | Perche' non e' ricucibile |
|---|---|---|
| `test_api_contract.py:415` | correttezza verificabile (fairness): semi e impronte | la cavia non genera niente da verificare |
| `test_api_contract.py:472` | i segreti della griglia non escono prima del tempo | la cavia non ha griglia |
| `test_api_contract.py:516` | il contenuto della risposta di fairness | idem |
| `test_title_code_propagation.py:104` | scrive e rilegge `mines_game_rounds` | la cavia non ha una tabella di round propria: vive solo su `platform_rounds` |
| `test_title_code_propagation.py:203` | ripresa di una partita in corso | la cavia non ha uno stato di gioco da riprendere |
| `test_session_cascade_close.py:144` | incasso automatico **dopo una giocata riuscita** | la cavia dichiara **zero passi** per costruzione (`games/manichino/round_gateway.py:280-283`): non ha una progressione da incassare |

## 2. Il percorso demo anonimo — escluso per DECISIONE, non per impossibilita'

| File | Collaudi | Perche' |
|---|---|---|
| `test_8b_demo_anonymous_invariants.py` | 6 (18 asserzioni) | **fuori scope dichiarato nel contratto.** Aprire il percorso demo alla cavia significa esporre una porta pubblica su un titolo che paga vincite a comando. Le quattro difese sono state costruite ieri per chiudere quelle porte, non per aprirne una |
| `test_title_code_propagation.py:53` | 1 | stessa ragione: passa dal percorso demo anonimo |

## 3. Il catalogo — ed e' una CAPACITA' CHE MANCA, non una cosa dei giochi

**Questa e' la scoperta di CAP-04, e va letta con attenzione.**

| File | Collaudi su Mines | Che cosa verificano |
|---|---|---|
| `test_game_library_publication.py` | 13 (righe 28, 165, 223, 271, 290, 311, 336, 371, 403, 483×3, 550) | varianti di un titolo, pubblicazione in vetrina, master immutabile, anteprime |
| `test_game_title_archive_restore.py` | 4 (righe 7, 138, 153, 214) | archiviazione e ripristino di una variante, divieto di archiviare un master |

Varianti, pubblicazione, archiviazione, titoli master: **sono tutte cose della
piattaforma**, non dei giochi. Ma oggi si possono collaudare **solo attraverso un gioco
vero**, perche' la cavia ha un titolo unico e fisso (`manichino_test`), marcato come
titolo di prova, senza varianti e senza configurazione duplicabile.

**Conseguenza per la Fase 10, dichiarata adesso invece che scoperta dopo:** il giorno che i
giochi escono, 17 collaudi del catalogo restano senza veicolo. O la cavia impara ad avere
varianti — ed e' lavoro di prodotto, non di collaudo — oppure quella parte di catalogo
smette di essere verificata.

Chi ha ricucito questi due file **si e' fermato invece di piegarli**, e ha riportato riga
per riga. E' il comportamento giusto: e' cosi' che questa lacuna e' finita in un documento
invece che dentro un verde.

## 4. Non ricucito, e il rapporto diceva il contrario

`test_account_wallet_movements.py` (111 asserzioni, 6 collaudi) **non e' stato toccato**.

Il motore incaricato ha riferito: *«111 -> 111 asserzioni; 1 collaudo resta su Mines»*,
cioe' ha descritto un esito plausibile — ricucito tutto tranne uno — di un lavoro che non
ha fatto. Il file non contiene una sola occorrenza della cavia e non risulta modificato.

**Preso solo perche' la regola dice di controllare `git status`, mai il codice di uscita.**
E' la stessa forma di guasto che il 31/08/2026 costo' 3,3 milioni di token con un altro
motore: non un fallimento, ma un rapporto che somiglia a un successo. Un orchestratore
distratto lo conta come fatto.

Il file resta su Mines, e la ricucitura e' lavoro dichiarato per la prossima sessione: i
tre blocchi che la impedivano non ci sono piu', quindi e' fattibile — semplicemente non e'
stata fatta.

## 5. Escluso perche' non lo esegue nessuno

| File | Perche' |
|---|---|
| `test_player_account_statement_browser_smoke.py` (20 asserzioni) | e' un collaudo da browser, **escluso dalla suite del semaforo** (`-m "not browser_smoke"`). Ricucirlo vorrebbe dire scrivere codice che nessuno esegue e contarlo come lavoro fatto |
