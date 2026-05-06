# CasinoKing - Product UX Execution Sequence Plan

## Stato

Piano operativo aggiornato dopo review CTO.

Questo documento coordina i prossimi cantieri UX/prodotto. Non sostituisce i
piani specifici gia' esistenti; li ordina, registra dipendenze e segnala i
gating pre-produzione.

## Verdetto sulla review CTO

La review e' integrata quasi integralmente.

Decisioni recepite:

- Games overview prima.
- Site/Lobby backoffice seconda, perche' ha gia' piano e va in coppia logica
  con Games.
- Audit leggero alzato di priorita': in un prodotto casino non e' polish.
- Player lobby dopo Site/Lobby backoffice.
- Error system come pattern progressivo, non refactor globale.
- Copy cleanup e i18n foundation separati.
- i18n foundation rinviata finche' non esiste una seconda lingua reale.
- F7-C esplicitato come prerequisito tecnico dentro Games overview.
- Production readiness e Security review registrati come gating pre-produzione.

Unica precisazione:

- F6-D/F6-E risultano gia' chiuse documentalmente in `DEMO_MODE_PLAN.md` e
  `TITLE_EDITOR_SHELL_PLAN.md`; questo documento le registra come checkpoint
  verificato, non come nuovo task.

## Ordine operativo aggiornato

```text
1. Games overview UX
5. Site / Lobby backoffice
3. Game admin change log / audit leggero
4. Player lobby / game cards
2. Error and notification pattern
0a. English copy cleanup
0b. i18n foundation deferred
```

Nota: la numerazione conserva i riferimenti della discussione precedente. Il
vero ordine operativo e' quello mostrato sopra.

## Checkpoint pre-sequenza

### F6-D/F6-E closure

Stato:

- F6-D completata in `docs/DEMO_MODE_PLAN.md`.
- F6-E completata in `docs/DEMO_MODE_PLAN.md`.
- `docs/TITLE_EDITOR_SHELL_PLAN.md` descrive F6 come cantiere chiuso.

Decisione:

- nessun nuovo task F6 da aprire;
- non riaprire F6 salvo bug reale;
- se una futura AI trova una fonte obsoleta che marca F6-D/F6-E come aperte,
  deve riallinearla ai documenti sopra.

### F7-C prerequisite

Stato:

`mines-backoffice-editor.tsx` resta un monolite grande. Sono state fatte
compattazioni e prime estrazioni, ma il refactor profondo non e' completo.

Decisione:

F7-C non e' un cantiere isolato: e' prerequisito tecnico per le Slice 2-3 di
Games overview, quando serviranno category view e variant detail piu' puliti.

Implica:

- estrarre componenti engine-specific;
- mantenere shell/detail separati;
- non spostare config/theme/assets nella overview;
- non cambiare payout/RTP/RNG/fairness;
- non cambiare contratti backend salvo piano esplicito.

## 1 - Games overview UX

Documento guida:

- `docs/BACKOFFICE_GAMES_UX_REORGANIZATION_PLAN.md`

Perche' ora:

- il piano e' gia' validato;
- l'area e' gia' stata parzialmente separata;
- e' il punto in cui l'operatore crea, legge e apre varianti;
- se resta confusa, Site/Lobby e audit erediteranno confusione.

Obiettivo:

- overview chiara di engine, master e varianti;
- duplicazione dal livello elenco/categoria;
- dettaglio variante separato;
- master bloccato e previewable;
- azioni principali comprensibili.

Stato aggiornato:

- Slice 1 implementata: overview/lista e detail separati;
- Slice 2A implementata: category view Mines con master distinto e varianti in
  lista compatta;
- resta aperto il refactor profondo del detail/monolite per Slice 3+.

Dipendenza F7-C:

- Slice 1 puo' proseguire con componenti attuali;
- Slice 2-3 devono spezzare il monolite Mines editor prima di aggiungere altra
  complessita';
- il refactor deve essere funzionale, non estetico.

Accettazione:

- smoke admin: Games -> Mines -> crea variante -> variante appare;
- smoke admin: apri variante -> detail separato -> torna elenco;
- master non modificabile;
- Site/Lobby non viene gestito nel detail;
- nessun endpoint nuovo senza decisione esplicita.

## 5 - Site / Lobby backoffice

Documento guida:

- `docs/SITE_LOBBY_PUBLICATION_PLAN.md`

Perche' subito dopo Games:

- anche questo piano e' gia' validato;
- e' il secondo lato del modello: Games crea/configura, Site pubblica;
- va reso professionale prima di rifare la lobby player, cosi' non si
  hardcodano decisioni editoriali nel frontend pubblico.

Obiettivo:

- gestione compatta di cosa appare sul sito;
- visibilita' hidden/visible;
- demo/real;
- posizione;
- display name/description;
- preview coerente con `GET /games/library`;
- nessuna configurazione gioco dentro Site.

Accettazione:

- Site/Lobby non crea varianti;
- Site/Lobby non modifica config Mines;
- salvataggi persistono;
- preview/lobby leggono la stessa fonte;
- layout compatto e leggibile.

## 3 - Game admin change log / audit leggero

Documento guida:

- `docs/GAME_ADMIN_CHANGE_LOG_PLAN.md`

Stato:

- Slice 1 implementata: schema `admin_audit_log`, service transazionale e
  primo evento `title_config_publish`.
- Slice 2 implementata: `theme_publish`, `lobby_publication_change`,
  `title_asset_upload`, `title_asset_delete`.
- Slice 3 ancora aperta: UI LOG minima.

Perche' prima della lobby player:

- casino + backoffice richiede audit operativo;
- modifiche a config e pubblicazione devono essere tracciabili presto;
- non e' event sourcing e non e' ledger, ma e' compliance hygiene.

Direzione schema:

- non riusare `admin_actions` per audit operativo non finanziario;
- `admin_actions` resta finanziaria, idempotente e ledger-linked;
- creare `admin_audit_log` come tabella separata per modifiche Title, Theme,
  Asset e Lobby;
- non introdurre event sourcing generico.

Action kind iniziali:

- `title_config_publish`;
- `theme_publish`;
- `lobby_publication_change`;
- `title_asset_upload`;
- `title_asset_delete`.

Accettazione:

- actor, timestamp, action kind, resource e payload leggibili;
- nessun payload sensibile non necessario;
- nessun impatto wallet/ledger/platform rounds;
- nessun logging gameplay round-by-round;
- schema `admin_audit_log` confermato prima di toccare Player lobby.

## 4 - Player lobby / game cards

Documento guida da creare:

- `docs/PLAYER_LOBBY_UX_PLAN.md`

Perche' dopo Site/Lobby e audit:

- la lobby player deve riflettere regole editoriali gia' decise;
- le modifiche di pubblicazione dovrebbero essere gia' tracciabili;
- e' ad alto impatto percepito, ma non deve anticipare decisioni backoffice.

Obiettivo:

- card giochi professionali;
- CTA demo/real chiare;
- stati disponibili/non disponibili;
- varianti visibili come prodotti, non record tecnici;
- master escluso dagli item ordinari;
- layout responsive.

Accettazione:

- lobby legge `GET /games/library`;
- demo/real lanciano title corretto;
- copy nuovo in inglese;
- nessun CMS completo;
- nessun hardcoding di pubblicazione.

## 2 - Error and notification pattern

Documento eventuale:

- `docs/ERROR_NOTIFICATION_PATTERN.md`

Decisione:

Non fare refactor globale.

Perche':

- i sistemi cross-cutting tendono al big bang;
- Mines ha gia' un primo dialog, ma non va riscritto tutto ora;
- il pattern deve nascere nel nuovo codice e propagarsi quando tocchiamo aree
  esistenti.

Regola:

- definire pattern toast/banner/dialog/inline per nuovo codice;
- applicare a Games/Site/Audit/Player lobby quando si implementano;
- migrare vecchio codice solo quando viene toccato per altri motivi.

Accettazione:

- nuovi errori non espongono messaggi tecnici grezzi;
- pattern coerente nel nuovo codice;
- nessun refactor globale di `mines-standalone.tsx`;
- nessun cambio contratti backend senza piano.

## 0a - English copy cleanup

Documento guida:

- `docs/PRODUCT_COPY_ENGLISH_CLEANUP_PLAN.md`

Decisione:

Il prodotto deve essere in inglese, ma la bonifica e' progressiva e collegata
ai cantieri UI.

Regola:

- nuovo codice UI in inglese;
- area toccata da refactor bonificata in inglese;
- niente copy layer obbligatorio ora;
- niente big bang di traduzione.

## 0b - i18n foundation deferred

Documento guida:

- `docs/I18N_FOUNDATION_DEFERRED_DECISION.md`

Decisione:

Rinviare finche' non esiste una seconda lingua reale.

Trigger:

- cliente/partner richiede lingua diversa;
- requisito commerciale multi-country;
- CMS editoriale multilingua;
- costi del copy hardcoded diventano superiori al costo della fondazione i18n.

## Gating pre-produzione

Questi non sono nello stream UX, ma sono obbligatori prima di parlare di
produzione vera:

- `docs/PRODUCTION_READINESS_BRIEF.md`;
- `docs/SECURITY_REVIEW_PRE_PRODUCTION_PLAN.md`.

Non bloccano Games/Site/Audit adesso, ma bloccano qualsiasi "go production".

## Cosa potrai fare dopo i prossimi tre step

Dopo Games, Site/Lobby e audit:

- creare e gestire varianti dal posto giusto;
- decidere cosa appare sul sito;
- vedere un tracciamento operativo delle modifiche backoffice principali.

## Cosa non potrai ancora fare

- creare engine non-Mines da UI;
- usare un CMS completo;
- fare scheduling editoriale;
- avere multilingua;
- dichiarare produzione pronta;
- sostituire audit finanziario/ledger con il LOG operativo.

## Checklist CTO

- Confermare ordine: 1 -> 5 -> 3 -> 4 -> 2 -> 0a -> 0b.
- Confermare F7-C come prerequisito tecnico dentro Games.
- Confermare F6-D/F6-E come gia' chiuse documentalmente.
- Confermare audit leggero su `admin_audit_log`, lasciando `admin_actions`
  solo al dominio finanziario.
- Confermare error system come pattern progressivo, non refactor.
- Confermare production/security come gating pre-produzione.
