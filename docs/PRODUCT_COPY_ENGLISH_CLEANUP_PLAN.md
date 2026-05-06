# CasinoKing - Product Copy English Cleanup Plan

## Stato

Piano operativo da validare prima di implementare.

Questo documento sostituisce la parte "copy" del precedente piano unico
copy/i18n. La review CTO ha chiarito un punto corretto: revisione copy e i18n
foundation sono due cantieri diversi.

Questo piano riguarda solo la bonifica progressiva del copy prodotto verso
l'inglese. Non introduce un sistema i18n.

## Decisione prodotto

La UI prodotto CasinoKing deve essere in inglese.

Michele e il team possono continuare a ragionare in italiano, e la
documentazione interna puo' restare in italiano. La regola riguarda cio' che un
player, un operatore o un admin vede nel prodotto.

## Obiettivo

Portare progressivamente in inglese:

- menu;
- label;
- bottoni;
- tab;
- stati;
- empty state;
- helper copy;
- messaggi di errore user-facing;
- messaggi di conferma;
- copy lobby/player;
- copy backoffice;
- default editoriali di Mines e lobby quando si apre il relativo cantiere.

## Cosa non fa questo piano

Non introduce:

- copy layer obbligatorio;
- chiavi i18n;
- language switcher;
- file traduzione per piu' lingue;
- routing locale;
- traduzione automatica dei contenuti DB.

Spiegazione: forzare subito un layer i18n mentre stiamo ancora ridisegnando le
schermate creerebbe una tassa su ogni PR e rischierebbe di rallentare i cantieri
gia' validati. La lingua inglese e' una regola di prodotto; i18n e' una scelta
architetturale futura.

## Strategia

### Non fare big bang

Non aprire un refactor globale "traduci tutto il repo".

Motivo:

- troppe stringhe sparse;
- troppe aree UI ancora da rivedere;
- alto rischio di lasciare residui;
- alto rischio di cambiare copy in schermate che verranno riscritte.

### Migrare quando si tocca una vista

Regola pratica:

- quando si apre un cantiere UI, il nuovo codice deve uscire in inglese;
- quando si modifica una vista esistente, si bonifica il copy della zona toccata;
- quando una vista sara' rifatta a breve, non si spende tempo a tradurla due
  volte.

### Inventario leggero prima di ogni slice

Prima di chiudere una slice UI:

```powershell
rg -n "Impossibile|Errore|Salva|Pubblica|Bozza|Sito|Giochi|Saldo|Ricarica|Variante|Tema" frontend/app
rg -n "accented Italian characters or mojibake" frontend/app backend/app
```

Spiegazione: l'inventario e' un controllo di qualita', non un invito a
riscrivere tutto subito.

## Priorita'

La copy cleanup non blocca i cantieri Games e Site/Lobby.

Ordine consigliato:

1. Games overview: nuovo copy in inglese mentre si rifa' la UX.
2. Site/Lobby backoffice: nuovo copy in inglese durante il polish.
3. Audit LOG: copy in inglese fin dal primo rilascio.
4. Player lobby/cards: copy in inglese per la superficie player.
5. Error pattern: nuovi messaggi in inglese, senza refactor globale.
6. Bonifica residua: passate mirate su aree ancora non toccate.

## Regole di tono

- Breve.
- Operativo.
- Professionale.
- Non tecnico quando parla al player.
- Preciso quando parla all'admin.
- Non tradurre letteralmente dall'italiano se suona innaturale.

Esempi:

| Italiano concettuale | Inglese consigliato |
| --- | --- |
| Saldo insufficiente | Insufficient balance. Top up to keep playing. |
| Bozza | Draft |
| Pubblica live | Publish live |
| Pubblica in lobby | Show in lobby |
| Nascondi dalla lobby | Hide from lobby |
| Variante | Variant |
| Master bloccato | Locked master |
| Ricarica pagina | Reload page |

## Confine UI copy / contenuto DB

Alcuni testi sono configurabili da backoffice:

- Mines rules HTML;
- Mines demo/real labels;
- lobby display name;
- lobby description.

Regola:

- UI chrome hardcoded: bonifica in inglese quando si tocca la vista;
- default/seed DB: bonifica solo con slice dedicata e, se serve, script
  esplicito;
- contenuti custom gia' salvati nel DB: non sovrascrivere senza autorizzazione.

## Accettazione per ogni slice UI

Una slice UI e' accettabile se:

- il nuovo copy introdotto e' inglese;
- non introduce nuove stringhe italiane user-facing;
- i vecchi testi italiani nell'area toccata sono rimossi se ragionevole;
- non apre i18n foundation;
- non cambia contenuti DB custom senza piano.

## Cosa sara' possibile

- Far evolvere UI e copy insieme.
- Evitare nuove stringhe italiane.
- Migrare progressivamente senza bloccare i cantieri principali.

## Cosa non sara' ancora possibile

- Cambiare lingua da UI.
- Avere contenuti multilingua.
- Garantire che ogni stringa storica del prodotto sia gia' inglese.
- Evitare un futuro lavoro i18n se arrivera' una seconda lingua reale.
