Status: ACTIVE
Last meaningful update: 2026-05-17

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
- Se il comportamento toccato viene testato dall'utente su `localhost` tramite Docker, il task non e' consegnabile finche' il servizio coinvolto non e' stato riallineato con rebuild/restart mirato oppure finche' non viene dichiarato esplicitamente che il riallineamento non e' stato eseguito.
- Usa lettura proporzionata: documenti core sempre, documenti di dominio solo quando il task li coinvolge.
- Distingui sempre tra file effettivamente letti, file solo individuati e file non letti perche' non necessari.
- Non usare `AGENTS.md` come fonte primaria delle regole: le regole condivise
  vivono nei documenti sotto `docs/`.
- Non essere accondiscendente: se una proposta dell'utente e' fragile,
  prematura o rischiosa, correggila esplicitamente e proponi l'alternativa
  minima piu' sicura. Vedi `docs/AI_CRITICAL_JUDGMENT_RULES.md`.
- Every WP that changes admin UI behavior or adds/removes admin capabilities
  MUST update the corresponding section of `docs/BACKOFFICE_MANUAL.md` in the
  same PR. Documentation-only PRs are accepted only for typo/style fixes;
  capability changes must be co-located with the change itself.
- Every file or asset upload UI MUST show the accepted formats, maximum file
  size, and any dimension/shape constraints or recommendations next to the
  upload control. It must also state how the asset is rendered when relevant:
  cover/crop, contain, no stretch, or not rendered yet. Keep this guidance
  synchronized with backend validation and runtime CSS.

## Recovery, migration e refactor cross-cutting

Quando un task recupera lavoro da un checkpoint, migra una feature o refactora
un flusso che attraversa piu' layer, il diff per file/hunk non basta.

Prima di dichiarare chiuso il task, preparare una matrice capability end-to-end
per ogni funzionalita' coinvolta:

```text
Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Stato | Note
```

Regole:

- classificare per capability, non solo per file o hunk;
- verificare la catena completa dal DB al comportamento visibile;
- separare piccoli pezzi atomici da macro-feature skippate;
- non usare "era dentro una macro-feature sospesa" come scusa per lasciare
  rotta una capability gia' usata;
- marcare ogni capability come completa, intenzionalmente skippata,
  regressione parziale, sostituita o da decisione CTO;
- se emerge una regressione parziale, aprire un WP dedicato invece di
  infilare fix non autorizzati nel task corrente.

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
8. Se ho modificato codice servito da container Docker e l'utente deve testarlo su `localhost`, ho eseguito rebuild/restart mirato e verificato l'artefatto runtime, oppure ho dichiarato perche' non e' stato fatto.
9. Se ho trovato una violazione della checklist, l'ho corretta prima della consegna.

## Regola di rifiuto

Se anche uno solo dei punti sopra non e' rispettato, il task e' da considerare rifiutato e deve essere ricontrollato e corretto prima della consegna.
