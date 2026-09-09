# CENSIMENTO DEL GATE GIA' ESISTENTE

## I 14 scenari dell'autotest

### verde
- **Cosa impedisce** — Che il gate segnali rosso quando repository, collaudi e baseline sono integri. [LETTO] scripts/ck-gate.sh:143
- **Come lo prova** — Crea tre collaudi che passano e una baseline 3/3, poi pretende uscita 0 e la parola `VERDE`. [LETTO] scripts/ck-gate.sh:62-73,143
- **NON copre:** non rompe il prodotto: usa solo `assert True` nel collaudo fittizio. [LETTO] scripts/ck-gate.sh:65-67

### baseline
- **Cosa impedisce** — La cancellazione di un collaudo per far sembrare la suite piu' verde. [LETTO] scripts/ck-gate.sh:89-91
- **Come lo prova** — Elimina `test_tre`, registra il gesto in git e pretende il rosso per conteggio sotto baseline. [LETTO] scripts/ck-gate.sh:89-91,144
- **NON copre:** non prova un difetto del prodotto: cancella una funzione dal collaudo fittizio. [LETTO] scripts/ck-gate.sh:65-67,89-91

### skip
- **Cosa impedisce** — Il silenziamento di un collaudo con uno skip senza giustificazione. [LETTO] scripts/ck-gate.sh:92-94
- **Come lo prova** — Aggiunge `@pytest.mark.skip` senza timbro e pretende il rosso della scansione skip. [LETTO] scripts/ck-gate.sh:92-94,145
- **NON copre:** non prova il prodotto rotto: aggiunge uno skip al collaudo fittizio. [LETTO] scripts/ck-gate.sh:65-67,92-94

### sporco
- **Cosa impedisce** — L'esecuzione del gate su file modificati ma non registrati in git. [LETTO] scripts/ck-gate.sh:95-96
- **Come lo prova** — Modifica il collaudo senza commit e pretende `ALBERO PULITO: ROSSO`. [LETTO] scripts/ck-gate.sh:95-96,146
- **NON copre:** non dice se il prodotto e' corretto: controlla soltanto lo stato dei file. [LETTO] scripts/ck-gate.sh:205-213

### rosso
- **Cosa impedisce** — Che una suite con un collaudo fallito venga dichiarata verde. [LETTO] scripts/ck-gate.sh:97-99
- **Come lo prova** — Aggiunge `assert False` a un collaudo fittizio e pretende `SUITE VERDE: ROSSO`. [LETTO] scripts/ck-gate.sh:97-99,147
- **NON copre:** non rompe codice di prodotto; rompe esplicitamente il collaudo fittizio. [LETTO] scripts/ck-gate.sh:65-67,97-99

### manomessa
- **Cosa impedisce** — L'abbassamento dei minimi insieme alla cancellazione di collaudi. [LETTO] scripts/ck-gate.sh:100-103
- **Come lo prova** — Toglie un collaudo, abbassa i due minimi nello stesso commit e pretende `BASELINE MANOMESSA: ROSSO`. [LETTO] scripts/ck-gate.sh:100-103,148
- **NON copre:** non verifica il prodotto: modifica solo fixture e file baseline. [LETTO] scripts/ck-gate.sh:65-67,100-103

### modulo
- **Cosa impedisce** — Lo spegnimento di un intero file di collaudi con una sola riga. [LETTO] scripts/ck-gate.sh:104-106
- **Come lo prova** — Inserisce `pytestmark = pytest.mark.skip(...)` e pretende il rosso della scansione skip. [LETTO] scripts/ck-gate.sh:104-106,149
- **NON copre:** non prova il prodotto rotto: silenzia il file fittizio dei collaudi. [LETTO] scripts/ck-gate.sh:65-67,104-106

### uscita
- **Cosa impedisce** — Che un comando di test con uscita anomala sia accettato solo perche' stampa “3 passed”. [LETTO] scripts/ck-gate.sh:84,150
- **Come lo prova** — Sostituisce il comando con uno che stampa tre passaggi ma esce 3; pretende il rosso. [LETTO] scripts/ck-gate.sh:84,150,345-350
- **NON copre:** non lancia il prodotto ne' una suite reale; usa un comando artificiale. [LETTO] scripts/ck-gate.sh:84

### ambiente
- **Cosa impedisce** — Che una variabile d'ambiente imponga un comando di test finto. [LETTO] scripts/ck-gate.sh:107-108
- **Come lo prova** — Passa `CK_GATE_TEST_CMD` con “600 passed” e pretende `COMANDO DEI TEST: ROSSO`. [LETTO] scripts/ck-gate.sh:107-108,151,322-325
- **NON copre:** non controlla il contenuto del prodotto; protegge la scelta del comando di test. [LETTO] scripts/ck-gate.sh:315-325

### chiave
- **Cosa impedisce** — Che sparisca la soglia dei collaudi raccolti, spegnendo il controllo anti-cancellazione. [LETTO] scripts/ck-gate.sh:109-111
- **Come lo prova** — Scrive una baseline senza `test_raccolti_minimo` e pretende il rosso. [LETTO] scripts/ck-gate.sh:109-111,152,373-380
- **NON copre:** non prova un difetto del prodotto; controlla la completezza della baseline. [LETTO] scripts/ck-gate.sh:373-380

### alias
- **Cosa impedisce** — Uno skip muto scritto con l'alias `mark` invece di `pytest.mark`. [LETTO] scripts/ck-gate.sh:112-114
- **Come lo prova** — Aggiunge `from pytest import mark` e `@mark.skip`, poi pretende il rosso. [LETTO] scripts/ck-gate.sh:112-114,153
- **NON copre:** non rompe il prodotto: modifica il collaudo fittizio. [LETTO] scripts/ck-gate.sh:65-67,112-114

### timbro
- **Cosa impedisce** — Che uno skip sia giustificato con una sigla inventata. [LETTO] scripts/ck-gate.sh:119-121
- **Come lo prova** — Aggiunge lo skip con `IMPEGNO: FAKE-1` e pretende “impegno non dichiarato”. [LETTO] scripts/ck-gate.sh:119-121,154,282-290
- **NON copre:** non controlla il prodotto; verifica che la giustificazione dello skip sia nella baseline. [LETTO] scripts/ck-gate.sh:242-247,282-290

### timbro_ok
- **Cosa impedisce** — Che venga bloccato anche uno skip dichiarato e autorizzato. [LETTO] scripts/ck-gate.sh:122-125
- **Come lo prova** — Aggiunge uno skip con `IMPEGNO: BON-05`, dichiara la sigla nella baseline e pretende verde. [LETTO] scripts/ck-gate.sh:122-125,155
- **NON copre:** non dimostra il prodotto corretto; convalida solo il percorso amministrativo dello skip. [LETTO] scripts/ck-gate.sh:122-125,242-247

### condizionale
- **Cosa impedisce** — Che condizioni legittime d'ambiente siano scambiate per silenziamenti proibiti. [LETTO] scripts/ck-gate.sh:115-118
- **Come lo prova** — Aggiunge `skipif(False)` e uno skip dentro `if False`, aggiorna la baseline e pretende verde. [LETTO] scripts/ck-gate.sh:115-118,156
- **NON copre:** non prova il prodotto; prova solo che il filtro degli skip non e' troppo largo. [LETTO] scripts/ck-gate.sh:264-270

## Le 4 difese della cavia

### D1 — l'interruttore
- **Cosa impedisce** — Che la cavia sia raggiungibile o emetta gettoni in produzione quando l'interruttore e' spento. [LETTO] scripts/ck-prove-rosse-cavia.sh:89-92; tests/contract/test_cavia_non_in_produzione.py:112-131
- **Come lo prova** — Toglie due controlli dal servizio di lancio, esige che il collaudo diventi rosso, ripristina e pretende di nuovo verde. [LETTO] scripts/ck-prove-rosse-cavia.sh:41-62,89-92
- **NON copre:** non controlla la vetrina ne' i titoli di prova generici: esercita solo la cavia `manichino`. [LETTO] tests/contract/test_cavia_non_in_produzione.py:112-142

### D2 — il marchio di prova in vetrina
- **Cosa impedisce** — Che un titolo marcato di prova compaia nella vetrina in produzione. [LETTO] scripts/ck-prove-rosse-cavia.sh:94-96; tests/contract/test_cavia_non_in_produzione.py:145-163
- **Come lo prova** — Toglie il filtro `is_test = false`, esige il rosso, poi ripristina e verifica il ritorno al verde. [LETTO] scripts/ck-prove-rosse-cavia.sh:41-62,94-96
- **NON copre:** non verifica che lo stesso titolo sia rifiutato al lancio o nella sessione d'accesso. [LETTO] tests/contract/test_cavia_non_in_produzione.py:145-163

### D3 — l'ambiente sul lancio
- **Cosa impedisce** — Che un titolo di prova sia lanciato in produzione. [LETTO] scripts/ck-prove-rosse-cavia.sh:98-101; tests/contract/test_cavia_non_in_produzione.py:166-179
- **Come lo prova** — Toglie il rifiuto dal servizio di lancio, esige il rosso, poi ripristina e verifica il verde. [LETTO] scripts/ck-prove-rosse-cavia.sh:41-62,98-101
- **NON copre:** non verifica il secondo ingresso, cioe' la creazione della sessione d'accesso. [LETTO] tests/contract/test_cavia_non_in_produzione.py:166-179

### D4 — l'ambiente sulla sessione d'accesso
- **Cosa impedisce** — Che un titolo di prova ottenga una sessione d'accesso in produzione. [LETTO] scripts/ck-prove-rosse-cavia.sh:103-106; tests/contract/test_cavia_non_in_produzione.py:182-199
- **Come lo prova** — Toglie il rifiuto dal servizio delle sessioni, esige il rosso, poi ripristina e verifica il verde. [LETTO] scripts/ck-prove-rosse-cavia.sh:41-62,103-106
- **NON copre:** non verifica il lancio ne' la vetrina del titolo di prova. [LETTO] tests/contract/test_cavia_non_in_produzione.py:182-199

## LA MINACCIA SCOPERTA

I 14 scenari difendono dal barare cancellando, silenziando o falsando la misura dei collaudi: i casi alterano il repository fittizio, la baseline, gli skip o il comando di test. [LETTO] scripts/ck-gate.sh:48-125

**Nessuno dei 14** prova che il gate diventi rosso quando e' rotto il codice di prodotto. In particolare, `rosso` rompe un collaudo (`assert False`), non il prodotto; gli altri 13 non modificano neppure codice di prodotto. [LETTO] scripts/ck-gate.sh:62-67,89-125; [GENERATO] `rg -n --glob '*.sh' --glob '*.py' 'test_d[1-4]_|ck-prove-rosse-cavia|difetti-veri|ROSSO ATTESO' . ../CONTRATTO_FASE_GATE.md` -> gli unici quattro rossi da difetto di prodotto trovati sono nella cavia, non nell'autotest.

L'autotest reale ha confermato soltanto questa copertura: `./scripts/ck-gate.sh --autotest` -> uscita 0, `14/14 scenari corretti`. [GENERATO] 2026-09-09, comando precedente.
