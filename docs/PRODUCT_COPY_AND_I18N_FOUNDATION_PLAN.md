# CasinoKing - Product Copy and i18n Foundation Plan

## Stato

Piano operativo da validare prima di implementare.

Questo documento nasce da una decisione di prodotto: Michele puo' continuare a
lavorare e ragionare in italiano, ma l'interfaccia finale del prodotto deve
parlare inglese in modo coerente.

Il rischio principale e' tradurre stringhe a mano in modo disperso, lasciando
pezzi italiani nel codice o creando testi non riusabili. Per questo la proposta
non e' "traduciamo tutto subito", ma "introduciamo un layer copy English-first,
poi migriamo le aree una alla volta".

## Decisione prodotto

La lingua canonica della UI CasinoKing e' l'inglese.

Devono essere in inglese:

- label;
- bottoni;
- menu;
- messaggi di errore;
- messaggi di conferma;
- empty state;
- helper copy;
- titoli delle schermate;
- tab e sezioni;
- copy player-facing;
- copy backoffice-facing;
- copy default di Mines configurabile da backoffice.

La documentazione interna puo' restare in italiano quando serve a Michele e al
team. La regola riguarda il prodotto visibile in UI.

## Obiettivo

Creare una base di copy centralizzata, tipizzata e pronta per multilingua futura,
senza introdurre subito un sistema i18n completo.

La prima versione deve:

- rendere l'inglese la fonte unica del copy UI;
- ridurre stringhe hardcoded nei componenti;
- permettere una migrazione progressiva senza bloccare il resto della roadmap;
- distinguere errori tecnici/API da messaggi leggibili per l'utente;
- lasciare aperta la strada a `it`, `es` o altre lingue in futuro.

## Non obiettivo immediato

Non implementare subito:

- language switcher utente;
- routing locale tipo `/en`, `/it`;
- traduzione completa dei contenuti storici nel database;
- CMS multilingua;
- localizzazione avanzata di date, numeri e valute;
- traduzione runtime backend completa;
- traduzione documentazione progetto.

Spiegazione: queste parti sono reali, ma aprirle subito trasformerebbe una
bonifica copy in un cantiere platform piu' ampio. La fondazione deve prepararle,
non anticiparle tutte.

## Principio guida

Usare chiavi semantiche, non tag visibili.

Corretto:

```text
mines.errors.insufficientBalance
```

Non corretto:

```text
[ERROR_BALANCE]
```

Spiegazione: una chiave semantica e' stabile, testabile e non compare mai al
player. Un tag visibile rischia di finire in UI, nel database o nei log come
testo sporco.

## Architettura proposta

### Layer copy frontend

Prima versione concettuale:

```text
frontend/app/lib/copy/
  en.ts
  keys.ts
  index.ts
```

Responsabilita':

- `en.ts`: valori inglesi canonici;
- `keys.ts`: eventuale tipo o mappa delle chiavi;
- `index.ts`: funzione minima per leggere il copy.

Spiegazione: per ora basta un layer piccolo. Non serve introdurre una libreria
i18n completa se non abbiamo ancora selezione lingua, routing locale o plural
rules complesse.

### Funzione copy minima

Forma concettuale:

```ts
t("mines.errors.insufficientBalance")
t("games.actions.openVariant")
t("common.actions.save")
```

Con parametri futuri:

```ts
t("mines.round.winNotice", { amount: "25 CHIP" })
```

Spiegazione: i parametri servono per evitare concatenazioni manuali, che sono
difficili da tradurre in futuro.

### English-only oggi, multi-locale domani

Stato target della prima fase:

```text
copy/en
  unica lingua caricata
```

Possibile evoluzione:

```text
copy/en
copy/it
copy/es
locale resolver
fallback chain
```

Spiegazione: si evita di pagare subito il costo di un sistema multilingua
completo, ma si evita anche di rendere impossibile aggiungerlo.

## Tassonomia chiavi

Proposta iniziale:

```text
common.actions.*
common.status.*
common.errors.*

auth.login.*
auth.register.*

player.nav.*
player.lobby.*
player.account.*

mines.controls.*
mines.errors.*
mines.rules.*
mines.session.*
mines.result.*

admin.shell.*
admin.finance.*
admin.players.*
admin.games.*
admin.site.*

games.overview.*
games.category.*
games.variant.*

site.lobby.*
notifications.*
```

Spiegazione: la tassonomia separa prodotto, gioco e backoffice. Questo evita di
riusare una stringa con significato simile ma contesto diverso, per esempio
`Publish` config live e `Publish` lobby.

## Confine frontend/backend

### Backend

Il backend deve continuare a esporre:

- codici errore stabili;
- messaggi tecnici utili al debug;
- dati strutturati.

### Frontend

Il frontend deve trasformare codici e contesto in messaggi utente.

Esempio:

```text
Backend code: INSUFFICIENT_BALANCE
Frontend copy: Insufficient balance. Top up to keep playing.
```

Spiegazione: il backend non deve diventare responsabile del tono prodotto.
Questo mantiene separati API, logica dominio e UX.

## Confine contenuto DB / UI copy

Nel progetto esistono testi configurabili da backoffice, per esempio:

- Rules HTML Mines;
- Demo/Real labels Mines;
- lobby display name;
- lobby description.

Questi non sono identici al copy UI hardcoded.

Regola proposta:

- UI chrome: copy layer frontend;
- contenuto editoriale configurabile: resta nel DB, ma default e seed devono
  essere in inglese;
- futuro multilingua contenuti DB: cantiere dedicato, non parte della prima
  fondazione.

Spiegazione: tradurre il codice e tradurre contenuti gestiti da operatori sono
due problemi diversi. Mischiarli ora renderebbe fragile sia il backoffice sia la
lobby.

## Inventario stringhe

Prima di migrare bisogna fare un inventario, non una caccia manuale.

Query consigliate:

```powershell
rg -n "\"[^\"]*[A-Za-z][^\"]*\"" frontend/app
rg -n "Impossibile|Errore|Salva|Pubblica|Bozza|Sito|Giochi|Saldo|Ricarica" frontend/app
rg -n "Ã|à|è|é|ì|ò|ù" frontend/app backend/app
```

Da classificare:

- UI player;
- UI admin;
- Mines game;
- errori frontend;
- default config;
- contenuti DB/seed;
- test snapshot/expected copy.

Spiegazione: l'inventario riduce il rischio di lasciare residui italiani e
permette al CTO di vedere lo scope reale prima della migrazione.

## Sequenza implementativa

### Slice 0 - Validazione piano

Fare approvare questo documento e il piano UX coordinato.

Accettazione:

- lingua prodotto confermata: English;
- niente multilingua completo nella prima slice;
- confine frontend/backend accettato;
- confine UI copy/contenuto DB accettato.

### Slice 1 - Copy foundation minima

Creare struttura copy frontend e helper di lettura.

Azioni:

- introdurre `frontend/app/lib/copy`;
- definire `en` come unica lingua;
- aggiungere helper `t`;
- aggiungere prime chiavi comuni;
- documentare regola "no new hardcoded product copy" per le aree migrate.

Accettazione:

- `tsc --noEmit` passa;
- nessun cambio visuale obbligatorio;
- una piccola area usa il copy layer;
- non viene introdotto language switcher.

### Slice 2 - Mines player copy

Migrare la UI player Mines, inclusi errori e dialog.

Perche' prima:

- e' la parte piu' visibile al player;
- ha gia' ricevuto il nuovo dialog errori;
- ha copy misto italiano/inglese;
- e' un dominio circoscritto.

Accettazione:

- tutte le label player Mines sono inglesi;
- errore saldo insufficiente usa copy inglese da chiave;
- dialog/error system non contiene stringhe italiane;
- nessuna modifica a payout, RNG, fairness o wallet.

### Slice 3 - Games overview/backoffice games copy

Migrare le label del backoffice giochi mentre si fa il refactor UX.

Perche':

- l'area Games e' il prossimo cantiere di UX;
- conviene evitare di rifare due volte gli stessi componenti;
- nomi azioni e stati devono diventare chiari per operatori.

Accettazione:

- elenco master/varianti in inglese;
- azioni principali in inglese;
- stati e badge in inglese;
- title configurabili restano dati, non copy hardcoded.

### Slice 4 - Notification/error standard

Standardizzare popup, toast/dialog, conferme e messaggi di errore.

Perche':

- dopo Mines serve un pattern comune;
- gli errori sono copy critico;
- il tono deve essere coerente su player e backoffice.

Accettazione:

- componente o pattern unico per errori user-facing;
- copy chiave-based;
- mapping codici API -> messaggi prodotto;
- nessun cambiamento ai contratti backend salvo decisione separata.

### Slice 5 - Player lobby and public site copy

Migrare lobby pubblica, card giochi, CTA demo/real e stati.

Perche':

- e' una superficie commerciale visibile;
- influenza poi la pagina Site/Lobby backoffice;
- deve chiarire demo/real in modo professionale.

Accettazione:

- lobby player tutta inglese;
- card giochi e CTA coerenti;
- empty/loading/error in inglese;
- contenuti editoriali da DB restano gestiti come dati.

### Slice 6 - Admin shell and remaining backoffice copy

Migrare shell admin, menu, Finance, Player admin, My Space, Admin management.

Perche':

- e' piu' ampia e meno urgente del flusso giochi/player;
- alcune aree vanno riviste in futuri cantieri;
- conviene migrare dopo aver stabilizzato pattern e tassonomia.

Accettazione:

- menu e shell admin in inglese;
- principali azioni admin in inglese;
- nessuna regressione auth/admin;
- nessuna modifica wallet/ledger.

### Slice 7 - Default DB content audit

Rivedere default/seed/config pubblicate che contengono copy italiano.

Perche':

- alcuni testi non vivono nel codice ma nel DB;
- Mines rules e labels possono essere configurate da backoffice;
- la UI puo' essere inglese ma il contenuto pubblicato restare italiano se non
  viene controllato.

Accettazione:

- default Mines rules/labels in inglese;
- lobby default display/description in inglese;
- nessuna migrazione distruttiva di contenuto custom senza decisione esplicita;
- eventuali script one-shot documentati prima di eseguirli.

## Criteri di qualita'

- Copy breve, operativo, professionale.
- Inglese coerente, non traduzione letterale dall'italiano.
- Stesso concetto = stessa famiglia di chiavi.
- Concetti diversi = chiavi diverse anche se testo simile.
- Nessuna stringa italiana nuova nelle aree migrate.
- Nessuna concatenazione manuale con variabili quando serve frase completa.
- Errori tecnici non esposti direttamente al player.

## Rischi e mitigazioni

### Rischio: lasciare stringhe italiane sparse

Mitigazione:

- inventario con `rg`;
- migrazione per area;
- checklist per ogni slice;
- eventuale test/lint custom in futuro.

### Rischio: fare i18n troppo grande subito

Mitigazione:

- English-only nella prima fase;
- niente language switcher;
- niente routing locale;
- struttura pronta ma non sovradimensionata.

### Rischio: confondere UI copy e contenuti DB

Mitigazione:

- regola esplicita UI chrome vs contenuto editoriale;
- default DB in inglese solo quando si apre slice dedicata;
- nessuna migrazione dati senza piano.

### Rischio: perdere tono prodotto

Mitigazione:

- definire glossario;
- centralizzare copy;
- review CTO/product sui testi principali.

## Glossario iniziale

| Concetto | Copy consigliato |
| --- | --- |
| Saldo insufficiente | Insufficient balance. Top up to keep playing. |
| Bozza | Draft |
| Pubblica live config | Publish config |
| Pubblica in lobby | Show in lobby / Hide from lobby |
| Variante | Variant |
| Master bloccato | Locked master |
| Gioco | Game |
| Sito | Site |
| Ricarica pagina | Reload page |
| Modalita' demo | Demo mode |
| Modalita' real | Real mode |

## Cosa sara' possibile dopo questa fondazione

- Migrare UI in inglese senza perdere pezzi.
- Aggiungere nuove schermate gia' English-first.
- Introdurre in futuro una seconda lingua con meno refactor.
- Uniformare errori e notifiche.
- Far validare copy e UX separatamente dalla logica gioco.

## Cosa non sara' ancora possibile

- Cambiare lingua da UI.
- Gestire contenuti editoriali multilingua da backoffice.
- Tradurre automaticamente contenuti gia' salvati nel DB.
- Garantire localizzazione completa date/numeri/valute.
- Dichiarare il prodotto pronto per mercati multipaese.

## Checklist CTO

- Confermare English-first come regola prodotto.
- Confermare che i18n completo e' futuro, non Slice 1.
- Confermare chiavi semantiche invece di tag visibili.
- Confermare mapping frontend dei messaggi API user-facing.
- Confermare separazione UI copy / contenuto DB.
- Confermare ordine di migrazione per aree.
