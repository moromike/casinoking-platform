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

## Project Implementation Log

Per progetti multi-fase con brief/design doc dedicato (es. BOXE, futuri giochi
3-20, future iniziative di metodo riusabile), ogni WP che tocca il progetto deve
aggiungere una entry nella sezione "Implementation Log" del brief, nello stesso
PR del codice/doc.

Formato entry:

```
### [YYYY-MM-DD] - [WP-CODE]
**Discovery / Decision**: 1-2 righe sul fatto.
**Why it matters**: 1-3 righe sul perché un lettore futuro deve saperlo.
**What we did**: 1-3 righe sull'azione presa.
**Affects**: link a file/sezione/altra entry se rilevante.
```

Livello di dettaglio: 5-15 righe per entry. Sufficiente a far capire a un
lettore futuro (o a un agente Codex fresco) il PERCHÉ, non solo il COSA.

Cosa annotare:

- sorprese trovate durante l'implementazione
- decisioni divergenti dal brief originale, con motivazione
- edge case scoperti
- anti-pattern identificati
- naming convention inventate al volo
- dipendenze non previste

Cosa NON annotare:

- cose già visibili dal diff/commit (è quello che fa git)
- status di completamento WP (è nel PR description / capability matrix)
- generiche "test verdi" (è nel delivery report)

Alla chiusura del progetto, le entry del log vanno distillate in:

- aggiornamenti del Game Brief Template (`docs/NEW_GAME_BRIEF_TEMPLATE.md`)
  con nuove domande da fare upfront, nuovi default sensati, nuovi campi
- aggiornamenti del Playbook (`docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`) con
  nuovi step di processo, anti-pattern formalizzati, refinement di checklist

Senza distillazione finale, il progetto non è formalmente chiuso. Obiettivo
sistemico: ogni progetto futuro parte da un Template più ricco e un Playbook
più affilato, riducendo il costo dei progetti successivi.

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
