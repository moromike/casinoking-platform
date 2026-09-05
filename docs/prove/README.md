# Le prove — che cosa sono, e perche' sono conservate qui

**Nate il 5 settembre 2026.** Questa cartella non contiene codice. Contiene le **ricevute**
del lavoro che tocca il denaro: la stampa di un controllo che e' stato eseguito, con la
data, l'esito, e il comando che lo ristampa.

## Perche' esistono, in una frase

Il codice e i collaudi sono archiviati, quindi ogni controllo si puo' **rifare** quando si
vuole. Ma *«posso rifare il controllo adesso»* e' una risposta piu' debole di *«ecco la
ricevuta, datata»* — e per una piattaforma che muove denaro di giocatori, la differenza
conta il giorno in cui la domanda arriva da fuori.

## Che cosa entra qui, e che cosa no

**Entra** solo cio' che dimostra qualcosa **sul denaro o sull'onesta' di una promessa**:
- parita' delle scritture contabili fra due percorsi che devono comportarsi uguale;
- prove che una difesa **sa diventare rossa**, non solo verde;
- il referto di un gate, con la data;
- cio' che una prova **non** dimostra, scritto per esteso.

**Non entra** il materiale di lavoro: registri degli agenti, output intermedi, tentativi.
Quella roba vive in `artifacts/`, che resta **fuori dal versionamento** apposta: sono
appunti, non documentazione, e archiviarli tutti trasformerebbe questa cartella in una
discarica di cui nessuno si fida.

## La regola per chi aggiunge

Ogni prova depositata porta scritto, nel `README.md` della sua fase:
1. **che cosa dimostra**, in una riga di italiano;
2. **il comando che la ristampa**, cosi' chiunque puo' verificare che non sia stata
   ritoccata a mano.

Una prova che non si puo' ristampare non e' una prova: e' un'affermazione con una data.
