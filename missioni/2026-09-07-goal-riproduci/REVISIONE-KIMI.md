# Revisione indipendente — ck-riproduci.sh e PROPOSTA.md

Revisore: Kimi (non ho scritto niente di ciò che revisiono).
Data: 2026-09-08. Oggetto: `scripts/ck-riproduci.sh` e
`missioni/2026-09-07-goal-riproduci/PROPOSTA.md`, contro il mandato
`MANDATO-GOAL-01.md`.

---

## 1. La domanda centrale: MISURE o DICHIARAZIONI?

**DICHIARAZIONI. Il dubbio sollevato da Codex è fondato, e la sua formulazione è
perfino ottimista.**

Il modulo proposto (`PROPOSTA.md` righe 56-91) riceve `importo`, `saldo_prima`,
`saldo_dopo` come **stringhe** e le scrive così come le riceve. Niente dentro
`scrivi_esito` collega il valore stampato al valore che il collaudo ha davvero
osservato: chi scrive la chiamata può passare una costante battuta a mano, e il
modulo non può accorgersene. L'unica difesa prevista è una disciplina
("ogni chiamata dovrà essere accanto all'asserzione", righe 113-115): una
promessa, non un controllo — esattamente il genere di cosa che il gate esiste
per non accettare.

La prova concreta sta nei collaudi veri:

- `tests/integration/test_seamless_parita_contabile.py:76` contiene l'unica
  asserzione economica del file: `assert Decimal(data["balance_after"]) ==
  Decimal("1015.00")`. Il **saldo prima non è osservato da nessuna parte** in
  quel collaudo. Quindi il campo `saldo_prima=`, obbligatorio nel formato, potrà
  solo essere **inventato**: una costante scritta a mano che nessuna asserzione
  presidia. E anche `saldo_dopo`, se chi applica la proposta passa il letterale
  `"1015.00 EUR"` invece della variabile `data["balance_after"]`, diventa una
  copia della costante dell'assert: un collaudo svuotato che continua a chiamare
  `scrivi_esito` con le stesse cifre lascerebbe `ck-riproduci.sh` verde.
- In altri collaudi i valori osservati esistono davvero
  (`tests/integration/test_seamless_ordine_operazioni.py:107,118` e
  `tests/integration/test_seamless_controlli_di_casa.py:84-89` leggono il saldo
  prima e dopo in variabili `before`/`after`). Lì una chiamata onesta è
  possibile — ma resta onesta solo per disciplina, non per costruzione.

Conclusione: così com'è proposto, il blocco ESITO è **un'affermazione con una
data**, non una prova. Per diventare una misura servirebbe un vincolo meccanico:
per esempio un helper che riceve **lo stesso oggetto osservato** (la risposta
HTTP, il saldo letto dal database), lo asserisce E lo registra — in modo che
stampare un valore non osservato sia impossibile, non solo sconsigliato.

---

## 2. ck-riproduci.sh — la lista chiusa delle mascherature

**La lista chiusa esiste, ma non è quella che maschera.**

- `controlla_allowlist` (righe 46-70) controlla l'array `MASCHERATURE`
  (riga 14) e rifiuta correttamente chiunque aggiunga `IMPORTO` all'array.
  Ma la mascheratura vera la fanno tre espressioni `sed` cablate in
  `maschera_esito` (righe 85-89), che **non derivano dall'array**. Chi aggiunge
  una quarta espressione sed che maschera `importo=` lascia l'array intatto e
  passa il controllo verde. Il requisito del mandato ("lo script deve fallire
  lui stesso se qualcuno li aggiunge alla lista", MANDATO-GOAL-01.md riga 35) è
  soddisfatto sulla carta e violato nel meccanismo.
- **Le espressioni mascherano più di quanto la lista dichiara.** Non sono
  ancorate ai confini di etichetta: bastano come sottostringa. Verificato
  empiricamente da me sul sed dello script:
  - `importo_request_id=10.00 EUR` → `importo_request_id=<IDENTIFICATIVO_GENERATO> EUR`
  - `saldo_prima_tx_id=100.00` → `saldo_prima_tx_id=<IDENTIFICATIVO_GENERATO>`
  - `importo_nonce=5.00 EUR` → `importo_nonce=<IDENTIFICATIVO_GENERATO> EUR`

  Quindi sì: **un importo può finire dentro una sostituzione destinata a un
  identificativo**, se il nome del campo contiene una delle dieci parole chiave.
  Inoltre la lista dichiara tre categorie ma i sed coprono dieci etichette
  (`identificativo_generato`, `id_generato`, `request_id`, `tx_id`, `nonce`,
  `timestamp`, `marca_temporale`, `durata`, `durata_ms`, `duration`): il
  perimetro reale della mascheratura è più largo di quello dichiarato e nessun
  controllo li tiene allineati.

## 3. L'impronta SHA-256 è circolare?

**Sì.** `verifica_deposito` (righe 101-115) controlla che l'impronta del file di
collaudo coincida con quella dichiarata nell'artefatto. Ma artefatto e collaudo
vivono nello stesso repository e sono entrambi riscrivibili: **chi indebolisce
il collaudo e rigenera l'artefatto nello stesso commit supera entrambi i
controlli in modo coerente.** Prova B funziona solo perché l'attaccante finto
tocca il collaudo e non l'artefatto.

C'è di peggio: con la proposta applicata, è il collaudo stesso a calcolare la
propria impronta a tempo d'esecuzione (`PROPOSTA.md` riga 75:
`sha256(Path(collaudo).read_bytes())`). L'artefatto rigenerato porta quindi
sempre l'impronta del collaudo corrente, qualunque esso sia: il controllo
sull'artefatto fresco (`ck-riproduci.sh` riga 166) è **tautologico** — confronta
il collaudo con la fotografia che il collaudo stesso si è appena fatto. L'unico
controllo vero resta quello sul deposito pre-rilancio (riga 151), che però
ancora tutto a un file nel working tree che ogni corsa del gate sovrascrive.
Manca un'ancora esterna: un manifesto firmato delle impronte approvate, o almeno
il confronto con il contenuto a HEAD git, come già fa `ck-rosso.sh` righe
450-467 per il ripristino.

## 4. L'autotest: cosa dimostrano davvero le due prove?

Ho rieseguito io stesso `./scripts/ck-riproduci.sh --autotest`: output identico
a quello incollato in ESITO.md, `2/2 prove di fallimento corrette`, uscita 0.
Ho anche lanciato `./scripts/ck-riproduci.sh` senza argomenti: rosso pulito sui
quattordici artefatti mancanti/malformati, prima di toccare Docker, come
dichiarato.

Le prove dimostrano proprietà **reali del parser**: l'estrattore rifiuta blocchi
ambiguil, il confronto nomina l'artefatto divergente, l'impronta disallineata
viene colta. Ma il produttore finto (righe 233-270) è disegnato dallo stesso
autore del parser e scrive esattamente il formato atteso, calcolando l'impronta
a runtime — la stessa circolarità del punto 3. Sul mondo reale non dimostrano
niente: i dieci artefatti verdi non esistono, i due rossi presenti in
`artifacts/fase9/` sono log pytest puri senza marcatori (verificato:
`parita-seamless-mines-rosso.txt` inizia con l'output di pytest), e — punto che
la proposta non dichiara — **quattro dei nove collaudi del gate non esistono
affatto**: `test_seamless_accredito_senza_trattenuta.py`,
`test_seamless_firma_rigiocata.py`, `test_seamless_rollback.py`,
`test_migrazione_0058.py` non sono in `tests/integration/` né altrove nel
repository (verificato per nome).

## 5. Un modo ovvio di passare senza riproducibilità vera

**Sì, e non richiede malizia.** In `riproduci()` il deposito viene copiato
(righe 149-154), poi il gate rilancia i produttori, poi si confronta il file in
sede (righe 159-176). Se un collaudo **esce verde ma smette di scrivere il suo
artefatto** — e con la proposta togliere la chiamata a `scrivi_esito` non fa
fallire nessun test, perché quella funzione non asserisce niente — il file in
sede resta quello della corsa precedente, **identico alla copia del deposito**:
VERDE senza che nulla sia stato riprodotto. Manca un controllo di freschezza:
cancellare gli artefatti prima del rilancio o verificarne la data di modifica.

Conseguenza collegata: i comandi #3, #4, #9 e #10 del gate (righe 128-135)
lanciano `ck-test.sh` sui quattro collaudi inesistenti. Anche applicando la
proposta, `ck-riproduci.sh` **non può diventare verde in questo repository**
finché quei quattro collaudi non vengono scritti da zero. La PROPOSTA (righe
96-107) li elenca come "file protetti da adattare": ma adattare un file che non
esiste vuol dire crearlo — lavoro e perimetro diversi da quelli dichiarati.

## 6. Note minori

- La PROPOSTA ha dichiarato in testa il modello sbagliato del proprio autore
  (righe 2-6, corretto da terzi): la catena di tracciabilità si è persa nel
  primo campo del dossier. La correzione è onesta, l'errore resta un segnale.
- ESITO.md è invece accurato: dichiara l'integrazione non verificata, incolla
  l'output vero delle prove (riprodotto identico da me) e non rivendica più di
  quanto fatto.
- Non ho verificato la conformità alla sezione del contratto
  `../CONTRATTO_FASE_9_QUINTA_STESURA.md`: è fuori dal worktree e il mio incarico
  non la includeva. Va confermata da chi monta la catena.

## 7. Cosa ho controllato per poter giudicare

Ho letto per intero mandato, script, proposta, ESITO.md e ck-rosso.sh; ho letto
o perlustrato i cinque collaudi seamless esistenti; ho rieseguito l'autotest e
la corsa secca dello script; ho provato le espressioni sed su input avversi;
ho verificato per nome l'esistenza di tutti i collaudi e degli artefatti citati.
Nessun file del progetto è stato modificato: l'unico file scritto è questo.

---

VERDETTO: RESPINTA
