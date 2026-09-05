# BON-03 — Inventario: cosa era stato tolto, e cosa se ne e' fatto

**Metodo: misurato, non indovinato.** Invece di far classificare i test a un modello,
sono stati tolti i 130 marcatori iniettati e i 47 file cancellati sono stati
ripristinati; poi la suite e' stata lanciata e si e' guardato cosa succedeva davvero.
Un test che passa non ha bisogno di un parere.

## Il conto

| | Funzioni di test |
|---|---|
| Dentro i 47 file cancellati (`test_*.py`) | 298 |
| Silenziate con `@pytest.mark.skip` sul disco | 65 |
| **Totale da classificare** | **363** |

I "130 skip" contati a occhio erano marcatori doppi: lo script `auto_skip.py` e'
girato due volte sugli stessi test.

## La classificazione, per categoria

| Cat. | Significato | Quanti | Esito |
|---|---|---|---|
| **A** — legittimamente morto | testava codice che qui non esiste piu' | **0** | nessuno |
| **B** — trasloca in m-and-m-games | testa logica di gioco che se ne va | **0** | nessuno, oggi |
| **C** — era un guasto | rosso perche' qualcosa si era rotto | **354** | ripristinati e passanti |
| **D** — guasto preesistente | rotto gia' prima dell'incidente | **9** | dichiarati con impegno |

**A e B sono zero, ed e' il risultato piu' importante di tutta la fase.** Nessuno di
quei 363 test era diventato inutile: erano tutti ancora validi, e sono tornati verdi
appena il codice che collaudavano e' tornato al suo posto.

## Perche' fallivano: la causa vera

Rilanciando la suite senza gli skip, 58 test fallivano. Raggruppando le cause, quasi
tutte erano **404 su rotte di gioco**. Ma quei test non testano i giochi:

> `test_reconciliation_integrity` chiama `/games/mines/start`, `/reveal`, `/cashout`
> per verificare che **il portafoglio quadri dopo una vincita**.

Mines e' l'impalcatura, la contabilita' e' la cosa collaudata. Lo stesso vale per i
test su sessioni, chiusure forzate, registro contabile, catalogo e rotte anonime:
usano un gioco come veicolo per produrre una transazione. Tolto il gioco, e' caduto
il ponteggio, non l'edificio — ma senza ponteggio non si puo' piu' collaudare
l'edificio.

**Conseguenza architetturale, da non nascondere:** la piattaforma non e' mai stata
resa collaudabile *senza* un gioco dentro. L'estrazione dei giochi va rifatta
partendo da li'. E' lavoro dello sviluppo giochi, non della bonifica.

## I 9 di categoria D — dichiarati, poi RIPARATI

Erano stati dichiarati come impegni aperti (BON-08..BON-11). La revisione indipendente
di Codex li ha respinti chiamandoli *"debito eseguibile mascherato"*. Aveva ragione su
tre su quattro, ed e' il motivo per cui nessuno rivede il proprio lavoro.

| Impegno | Cosa dicevo io | Cos'era davvero | Esito |
|---|---|---|---|
| **BON-08** (5) | "serve `ck-punto-zero.sh`, che cancella il database" | il test assumeva che il titolo `mines001b` fosse gia' nel database. La fixture `create_published_mines_variant` esisteva gia' in `conftest.py` | **riparato**, 6 test verdi |
| **BON-11** (2) | "il frontend non e' raggiungibile" | era raggiungibile su `frontend-v3:3001` da sempre: `ck-test.sh` non esportava la variabile | **riparato** |
| **BON-10** (1) | "il test e' avanti al codice" | il comportamento c'e' ed e' completo, ma in `launch-cashier.tsx`: era il TEST a guardare nel file sbagliato dopo un rifacimento. 8 asserzioni su 10 passavano gia' | **riparato** |
| **BON-09** (1) | "l'asset non e' mai stato in git" | vero, ma la forma giusta non e' uno skip incondizionato: e' una guardia condizionale che riparte dove l'arte c'e' | **convertito** |

Su BON-10 avevamo torto **entrambi**: io dicevo che la funzione non esisteva, Codex che
era un bug del frontend. Era una terza cosa.

## Due difetti emersi cercando l'ultimo rosso

1. **Tre blocchi erano flaky una volta su nove.** Con una mina su nove caselle, se la
   casella 0 e' la mina il round FINISCE; il codice continuava a scoprire le caselle di
   una partita chiusa, la risposta non aveva il campo `data` e il test moriva con
   `KeyError`. Passava otto volte su nove: da solo passava, nella suite no, e sembrava
   "interferenza fra test". Dodici esecuzioni di fila dopo la riparazione: dodici verdi.

2. **Un test era definito due volte con lo stesso nome nello stesso file.** In Python la
   seconda definizione sovrascrive la prima: quella copia non e' **mai** stata eseguita,
   pur comparendo nel file e facendo sembrare la copertura piu' ampia di quanto fosse.

## Il risultato

| Stato | Test eseguiti e passati |
|---|---|
| Prima della Fase 3 (`44d900a`) | 572 |
| Dopo la notte del 3-4/09 | 255 |
| Dopo il ripristino | 574 |
| **Dopo la revisione di Codex** | **580** |

Gli skip residui sono **9, tutti condizionali** (Chromium non installato, file d'arte
non versionati): ripartono da soli dove la precondizione c'e'. **Zero skip dichiarati,
zero skip muti.**
