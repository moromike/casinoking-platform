Status: COMPLETED
Last meaningful update: 2026-05-07

# CasinoKing - Master Launch Legacy Removal Plan

## Stato

Documento operativo da sottoporre al CTO prima di implementare.

Questo piano riguarda la rimozione dell'eccezione legacy che permette ancora il
launch pubblico del master `mines_classic`.

Prerequisito operativo: eseguire e chiudere lo smoke manuale descritto in
`docs/E2E_MANUAL_SMOKE_PLAN.md`.

## Contesto

Il modello attuale separa:

- Engine: tecnologia di gioco;
- Title: prodotto commerciale configurabile;
- Site: distribuzione e pubblicazione sul sito.

La player lobby legge `GET /api/v1/games/library` e mostra solo Title
non-master visibili, attivi e con almeno una modalita' abilitata.

Il master `mines_classic` ha oggi questo ruolo:

- sorgente tecnica per duplicare varianti Mines;
- read-only nel backoffice;
- non pubblicabile come item lobby ordinario;
- previewable dal backoffice tramite `preview_token` admin dedicato.

Resta pero' una deroga legacy nel launch pubblico. In
`backend/app/modules/platform/game_launch/service.py`,
`_ensure_title_launch_mode_allowed()` ritorna subito se `is_master` e' true,
saltando i controlli di pubblicazione Site/Lobby.

## Problema

Oggi esistono due regole:

- le varianti rispettano `lobby_visibility`, `demo_enabled` e `real_enabled`;
- il master bypassa quei flag per compatibilita' storica.

Questo significa che `mines_classic` e':

- escluso dalla library player;
- non pubblicabile dal backoffice come item lobby;
- ma ancora lanciabile direttamente dai flussi pubblici real/demo.

La preview admin non dipende piu' da questo bypass, perche' usa un token firmato
dedicato.

## Perche' Risolverlo

Rimuovere l'eccezione riallinea backend, backoffice e lobby player:

- un Title non pubblicabile non deve essere lanciabile pubblicamente;
- il master torna a essere solo sorgente tecnica e oggetto di preview admin;
- i link diretti non possono aggirare le decisioni Site/Lobby;
- i test smettono di dipendere da un comportamento dichiarato temporaneo.

Questa e' una correzione di coerenza architetturale, non un polish visuale.

## Obiettivi

- Eliminare il bypass pubblico per `mines_classic`.
- Mantenere funzionante la preview backoffice con `preview_token`.
- Far rispettare a tutti i public launch le regole Site/Lobby.
- Conservare la propagazione `title_code` e `site_code` su access session, table
  session e round.
- Aggiornare test e documentazione che oggi citano l'eccezione legacy.

## Proposta Tecnica

### Backend Launch

In `backend/app/modules/platform/game_launch/service.py`, rimuovere la deroga:

```python
if title.get("is_master") is True:
    return
```

Il public launch deve rifiutare qualsiasi Title master in modo esplicito. La
regola deve essere generica su `is_master`, non hardcoded su `mines_classic`, in
modo da valere anche per futuri engine con un proprio master.

L'errore deve avere code stabile, ad esempio `LAUNCH_REJECTED_MASTER`, senza
affidare il frontend allo scraping del messaggio. Il frontend deve poter
distinguere:

- master non lanciabile pubblicamente;
- variante nascosta;
- variante non abilitata in demo;
- variante non abilitata in real.

### Preview Admin

Mantenere separato il percorso:

```text
POST /admin/games/titles/{title_code}/preview-launch
POST /demo/launch con preview_token
```

Questo percorso deve continuare a permettere demo preview di master e varianti
hidden senza pubblicarle in lobby.

### Default Senza title_code

Oggi molte chiamate senza `title_code` cadono su `mines_classic`. Dopo la
rimozione dell'eccezione la richiesta deve fallire.

Il default silente verso un Title non pubblicabile e' un footgun. Il backend
deve restituire errore esplicito; il frontend puo' gestire quel caso riportando
il player alla lobby.

Non deve esistere un nuovo magic default verso una variante pubblicata.

## Aree Toccate

- `backend/app/modules/platform/game_launch/service.py`
- `backend/app/api/routes/mines.py`
- `backend/app/api/routes/demo.py`
- `tests/integration/test_title_code_propagation.py`
- `tests/integration/test_game_library_publication.py`
- `tests/conftest.py`, se fixture o helper assumono `mines_classic` come launch
  pubblico valido.
- Eventuali contract/browser smoke che aprono `/mines` senza `title_code`.
- Frontend Mines solo se il CTO decide di gestire esplicitamente `/mines` senza
  `title_code`.

## Test Da Aggiornare O Aggiungere

- Aggiornare i test positivi di launch/start per usare una variante non-master
  pubblicata.
- Introdurre un helper riusabile, ad esempio
  `create_published_mines_variant(client, ...)`, in `tests/conftest.py`.
- Ogni test deve preparare la propria variante pubblicata, evitando una variante
  globale condivisa che crea coupling tra test e righe audit visibili ai vicini.
- Aggiornare `test_launch_token_is_title_and_site_aware...`, che oggi accetta
  launch del master.
- Aggiornare `test_title_and_site_code_are_persisted...` per usare una variante
  pubblicata e verificare comunque propagazione `title_code`/`site_code`.
- Aggiungere test: public real launch di `mines_classic` fallisce.
- Aggiungere test: public demo launch di `mines_classic` fallisce senza
  `preview_token`.
- Mantenere verde il test preview admin master.
- Verificare che le varianti hidden o con mode disabilitata restino respinte.
- Verificare che le varianti visible e abilitate continuino a lanciarsi.

Suite minima consigliata:

```text
tests/integration/test_title_code_propagation.py
tests/integration/test_game_library_publication.py
tests/contract
tests/integration con flussi Mines/financial interessati
```

## Impatto Documentale

Se il CTO approva l'intervento, aggiornare:

- `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`
- `docs/ARCHITECTURE_ATLAS_MINES.md`
- `docs/PRODUCT_UX_EXECUTION_SEQUENCE_PLAN.md`
- `docs/PLAYER_LOBBY_UX_PLAN.md`
- `docs/SITE_LOBBY_PUBLICATION_PLAN.md`
- `docs/README.md`

L'aggiornamento deve rimuovere i riferimenti alla compatibilita' legacy
temporanea e dichiarare che il master e' previewable solo via token admin.

Documentazione, codice e test vanno aggiornati nello stesso task tecnico, cosi'
il cantiere resta atomico e non introduce drift documentale.

## Criteri Di Accettazione

- `mines_classic` non e' lanciabile pubblicamente in real.
- `mines_classic` non e' lanciabile pubblicamente in demo senza
  `preview_token`.
- Il public launch master fallisce con code stabile, ad esempio
  `LAUNCH_REJECTED_MASTER`.
- Una richiesta public launch senza `title_code` fallisce in modo esplicito.
- Preview admin master funziona con `preview_token` valido.
- Varianti visibili e abilitate continuano a lanciarsi correttamente.
- Varianti hidden o con mode disabilitata restano respinte.
- `title_code` e `site_code` continuano a propagarsi su access session, table
  session, platform round e Mines round.
- Nessuna modifica a payout, RTP, RNG, fairness, wallet o ledger.
- Test rilevanti verdi.
- Documentazione aggiornata nello stesso cantiere tecnico.

## Fuori Scope

- Payout, RTP, RNG e fairness.
- Wallet, ledger e accounting.
- Redesign lobby o backoffice.
- CMS, scheduling o nuova logica editoriale.
- Creazione automatica di varianti.
- Production readiness.
- External adapter.
- i18n foundation.

## Rischi

- Ampio impatto sui test storici che usano `mines_classic` come default.
- Link diretti `/mines` senza `title_code` potrebbero diventare non giocabili.
- Una modifica troppo ampia potrebbe rompere la preview admin.
- Una fixture globale mal aggiornata potrebbe nascondere regressioni nei flussi
  Title/Site.

## Rollback Strategy

Se dopo la rimozione emerge una regressione bloccante, il rollback e' il revert
del commit applicativo insieme ai test e agli aggiornamenti documentali
associati.

Non e' previsto feature flag: la regola e' binaria e di dominio, cioe' un master
non deve essere lanciabile pubblicamente.

## Decisioni CTO Recepite

- Public launch master: errore dedicato con code stabile
  `LAUNCH_REJECTED_MASTER`.
- Richieste senza `title_code`: fallimento esplicito lato backend; il frontend
  puo' redirigere alla lobby.
- Test: ogni test prepara la propria variante tramite helper riusabile.
- Documentazione: aggiornata nello stesso task tecnico.
