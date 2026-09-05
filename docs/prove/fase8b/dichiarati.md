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

## 4. Un file che NON aveva bisogno di essere ricucito — e una mia accusa sbagliata

`test_account_wallet_movements.py` (111 asserzioni, 6 collaudi) **non e' stato modificato,
e non doveva esserlo.**

Dei suoi sei collaudi, **cinque non usano nessun gioco**: muovono denaro con i bonus e le
rettifiche dell'amministratore (`:26`, `:174`), che sono rotte di piattaforma. Non avevano
niente da cui essere staccati. Il sesto (`:282`) apre due round di Mines nella **stessa**
sessione di accesso, con rivelazione e incasso.

### La correzione, e vale come metodo

In una prima stesura di questo documento avevo scritto che il motore incaricato **aveva
riferito un lavoro mai fatto**, perche' il suo rapporto diceva *«111 -> 111; 1 collaudo
resta su Mines»* mentre `git status` non mostrava modifiche.

**Era sbagliata, e l'errore era mio.** Il fatto verificato — il file non e' cambiato — era
vero. La conclusione — quindi il rapporto mente — **non seguiva**: quel rapporto e'
esattamente cio' che si scrive dopo aver ESAMINATO un file e aver trovato che non c'e'
niente da cambiare tranne un collaudo che deve restare dov'e'.

E' lo stesso difetto che questa fase ha contestato ad altri per tutto il giorno: un fatto
verificato e una conclusione data per scontata. Sta qui per esteso invece di sparire in
una modifica silenziosa.

### Cio' che resta davvero aperto, ed e' piccolo

Il collaudo `:282` resta su Mines. Il motivo dichiarato era *«gli attrezzi della cavia
aprono una sessione nuova per ogni round»* — che e' un limite **dell'attrezzo**, non una
cosa impossibile: dalla Fase 8B la piattaforma sa gestire piu' round attivi sulla stessa
sessione, e la cavia chiude un round con un esito deciso dal chiamante, senza bisogno di
progressione. **Ricucibile con una sequenza scritta a mano.** Lavoro piccolo e dichiarato,
non un blocco.

## 5. Escluso perche' non lo esegue nessuno

| File | Perche' |
|---|---|
| `test_player_account_statement_browser_smoke.py` (20 asserzioni) | e' un collaudo da browser, **escluso dalla suite del semaforo** (`-m "not browser_smoke"`). Ricucirlo vorrebbe dire scrivere codice che nessuno esegue e contarlo come lavoro fatto |
