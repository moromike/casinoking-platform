# CasinoKing - Task Execution Guardrails

Questa checklist e' obbligatoria all'inizio e alla fine di ogni task.

## Obiettivo

Evitare invenzioni, regressioni e modifiche non richieste, soprattutto su UI, Mines e backoffice.

## Regole obbligatorie

- Implementa solo cio' che l'utente ha chiesto.
- Non aggiungere testi, badge, hint, helper copy, label, pulsanti o sezioni non richiesti.
- Se un miglioramento sembra utile ma non e' richiesto, non implementarlo: proponilo soltanto.
- Non mischiare in un singolo fix copy, layout, comportamento e architettura se non e' strettamente necessario.
- Mantieni separati i layer: contenuto, layout, comportamento, publishing, runtime.
- Non dichiarare un task concluso senza verifica reale del comportamento toccato.
- Usa lettura proporzionata: documenti core sempre, documenti di dominio solo quando il task li coinvolge.
- Distingui sempre tra file effettivamente letti, file solo individuati e file non letti perche' non necessari.

## Checklist iniziale

Prima di iniziare:

1. Ho letto `docs/SOURCE_OF_TRUTH.md`.
2. Ho letto questa checklist.
3. Ho letto `docs/DOCUMENTATION_MAINTENANCE.md`.
4. Ho distinto i file effettivamente letti da quelli solo individuati.
5. So esattamente cosa devo cambiare.
6. So esattamente cosa non devo cambiare.
7. Non sto introducendo elementi UI nuovi non richiesti.

## Checklist finale

Prima di consegnare:

1. Ho ricontrollato questa checklist.
2. Ho ricontrollato `docs/DOCUMENTATION_MAINTENANCE.md`.
3. Ho dichiarato quali documenti ho letto davvero e quali ho escluso per lettura proporzionata.
4. Ho verificato se la modifica richiede aggiornamenti documentali e li ho fatti, oppure ho dichiarato perche' non servono.
5. Ho verificato che non ci siano testi o elementi UI aggiunti senza richiesta esplicita.
6. Ho verificato che il bug richiesto sia davvero risolto.
7. Ho verificato che desktop, mobile o admin non abbiano regressioni evidenti nelle aree toccate.
8. Se ho trovato una violazione della checklist, l'ho corretta prima della consegna.

## Regola di rifiuto

Se anche uno solo dei punti sopra non e' rispettato, il task e' da considerare rifiutato e deve essere ricontrollato e corretto prima della consegna.
