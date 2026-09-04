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

## I 9 di categoria D — dichiarati, non spenti

| Impegno | Quanti | Perche' e' rosso |
|---|---|---|
| **BON-08** | 5 | richiedono un titolo Mines **pubblicato**. Lo stato di partenza lo crea `ck-punto-zero.sh`, che pero' **cancella il database**: non si lancia senza decisione di Michele |
| **BON-09** | 1 | pretende `assets/Games/boxe/boxe_icon001_512px.webp`, un file **mai stato in git**: poteva passare solo su una macchina dove qualcuno l'aveva messo a mano |
| **BON-10** | 1 | pretende `setReturnTo(window.location.href)` in un componente del frontend, che non esiste. E' il test a essere avanti al codice |
| **BON-11** | 2 | richiedono il frontend Site V3 raggiungibile dal container dei test |

Nessuno dei 9 e' stato causato dall'incidente: fallivano tutti anche prima.

## Un bug vero, riparato (BON-05)

`test_mines_network_header_verification.py` cablava `http://localhost:8000`, che
dentro il container dei test non e' il backend. Sei test fallivano **da sempre** per
questo, e nessuno se n'era accorto perche' erano annegati nel rumore. Ora usano la
stessa variabile del resto della suite. Due passano subito; gli altri quattro sono
BON-08.

## Il risultato

| Stato | Test eseguiti e passati |
|---|---|
| Prima della Fase 3 (`44d900a`) | 572 |
| Dopo la notte del 3-4/09 | 255 |
| **Adesso** | **574** |
