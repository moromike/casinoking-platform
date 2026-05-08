# CasinoKing - Platform i18n Foundation Deferred Decision

## Stato

Decision record operativo per la platform generale.

Aggiornamento 2026-05-07:

- la i18n foundation globale della platform resta rinviata;
- la i18n foundation del runtime Mines e' stata riaperta come cantiere attivo;
- Mines mantiene una foundation i18n dedicata, ma il runtime pubblica una sola
  lingua per gioco/config;
- la review CTO ha approvato il pivot per Mines;
- per Mines valgono i documenti:
  - `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`
  - `docs/MINES_I18N_STRING_INVENTORY.md`

## Decisione

La fondazione i18n completa della platform generale resta rinviata finche' non
esiste un requisito multi-locale esteso a lobby, backoffice, account,
auth/reporting e contenuti site-wide.

Eccezione esplicita:

```text
Mines runtime i18n e' ora un cantiere attivo.
```

Motivo dell'eccezione:

- il gioco deve eliminare label player-facing hardcoded;
- il backoffice deve poter governare copy e traduzioni del Title;
- il player runtime deve risolvere copy da un bundle controllato;
- il CTO deve poter validare copertura, produzione contenuti, static scan e
  publish gating;
- il supporto editoriale `it`/`en`/`de`/`es` resta confinato al cantiere Mines;
  il player non seleziona lingua in runtime.
- runtime e config pubblicata Mines restano single-locale.

## Motivazione

La UI platform deve diventare inglese, ma questo non implica introdurre subito
per tutta la platform:

- libreria i18n;
- key namespace obbligatorio;
- file di traduzione;
- fallback locale;
- language switcher;
- routing localizzato;
- workflow di traduzione.

La review CTO evidenzia correttamente il rischio: applicare subito i18n a tutta
la platform mentre Games, Site/Lobby e Player lobby sono ancora in refactor
porterebbe a rifare chiavi e namespace piu' volte.

Mines e' diverso perche' e' un runtime di gioco separato, con superficie copy
piu' circoscritta e con il requisito esplicito di non lasciare label
player-facing hardcoded.

## Regola fino a nuova decisione

- Fuori dall'epic Mines i18n, nuova UI platform/backoffice segue il cantiere
  copy cleanup inglese quando la slice UI lo prevede.
- UI platform toccata da refactor: bonifica copy in inglese secondo
  `docs/PRODUCT_COPY_ENGLISH_CLEANUP_PLAN.md`.
- Nessuna chiave i18n obbligatoria fuori dal runtime Mines.
- Nessun language switcher globale.
- Nessun salvataggio contenuti multilingua platform-wide.
- Mines segue invece il piano i18n dedicato.
- Nel solo epic Mines i18n, la UI backoffice resta IT-only; il tab traduzioni
  gestisce contenuto player-facing e lingua pubblicata, non traduce il
  backoffice stesso.
- Nel solo epic Mines i18n, i body rules localizzati vivono in
  `title_locale_maps.locales_json[locale].rules_sections.*.body_html`;
  `rules_sections_json` resta solo projection legacy della lingua pubblicata.

## Trigger per riaprire i18n

Riaprire la i18n globale platform solo se accade almeno uno di questi eventi:

- arriva un cliente/partner che richiede una seconda lingua;
- esiste un requisito commerciale multi-country concreto;
- si decide di rendere il sito pubblico multi-locale;
- il backoffice deve gestire contenuti editoriali in piu' lingue;
- il volume di copy rende piu' costoso non avere un catalogo centralizzato.

## Quando verra' riaperto

Il piano i18n globale dovra' decidere:

- libreria o soluzione interna;
- struttura file;
- convenzione chiavi;
- fallback;
- test mancanti;
- gestione contenuti DB;
- migrazione delle stringhe gia' esistenti;
- workflow di traduzione e review.

## Cosa non fare adesso

- Non introdurre `t("key")` ovunque nella platform.
- Non convertire ogni stringa platform in chiave.
- Non bloccare Games/Site/Lobby globali sull'i18n.
- Non confondere il cantiere Mines con una i18n globale gia' attiva.

Per Mines, invece, non aggiungere nuove label player-facing hardcoded: usare il
manifest e il resolver previsti nel piano dedicato.

## Relazione con copy cleanup

Il documento attivo per la lingua prodotto e':

- `docs/PRODUCT_COPY_ENGLISH_CLEANUP_PLAN.md`

Questo decision record serve solo a evitare che la parola "inglese" venga
confusa con "multilingua globale subito".

Per il runtime Mines la fonte attiva e':

- `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`
