# CasinoKing - i18n Foundation Deferred Decision

## Stato

Decision record operativo. Non e' un piano da implementare ora.

## Decisione

La fondazione i18n completa e' rinviata finche' non esiste una seconda lingua
reale da supportare.

## Motivazione

La UI deve diventare inglese, ma questo non implica introdurre subito:

- libreria i18n;
- key namespace obbligatorio;
- file di traduzione;
- fallback locale;
- language switcher;
- routing localizzato;
- workflow di traduzione.

La review CTO evidenzia correttamente il rischio: senza una seconda lingua
reale, ogni stringa nuova pagherebbe subito una tassa architetturale senza un
beneficio immediato. Inoltre le viste Games, Site/Lobby e Player lobby sono
ancora in refactor: introdurre i18n prima di stabilizzarle porterebbe a rifare
chiavi e namespace piu' volte.

## Regola fino a nuova decisione

- Nuova UI: copy in inglese.
- UI toccata da refactor: bonifica copy in inglese.
- Nessuna chiave i18n obbligatoria.
- Nessun language switcher.
- Nessun salvataggio contenuti multilingua.

## Trigger per riaprire i18n

Riaprire questo cantiere solo se accade almeno uno di questi eventi:

- arriva un cliente/partner che richiede una seconda lingua;
- esiste un requisito commerciale multi-country concreto;
- si decide di rendere il sito pubblico multi-locale;
- il backoffice deve gestire contenuti editoriali in piu' lingue;
- il volume di copy rende piu' costoso non avere un catalogo centralizzato.

## Quando verra' riaperto

Il piano i18n dovra' decidere:

- libreria o soluzione interna;
- struttura file;
- convenzione chiavi;
- fallback;
- test mancanti;
- gestione contenuti DB;
- migrazione delle stringhe gia' esistenti;
- workflow di traduzione e review.

## Cosa non fare adesso

- Non introdurre `t("key")` ovunque.
- Non convertire ogni stringa in chiave.
- Non aggiungere `en.ts`/`it.ts` senza seconda lingua.
- Non bloccare Games/Site/Lobby sull'i18n.

## Relazione con copy cleanup

Il documento attivo per la lingua prodotto e':

- `docs/PRODUCT_COPY_ENGLISH_CLEANUP_PLAN.md`

Questo decision record serve solo a evitare che la parola "inglese" venga
confusa con "multilingua subito".
