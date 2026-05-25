Status: ACTIVE
Last meaningful update: 2026-05-25

# Game Finance / Replay / Reporting Contract

Scope: contratto strutturale per ogni gioco CasinoKing, da usare prima di
aggiungere il prossimo gioco proprietario.

Questo documento chiude il gap emerso dopo HI-LO: player account, admin finance,
replay, ledger detail e copy esplicativo non possono crescere con branch
manuali per ogni gioco.

## 1. Principle

Ogni gioco deve dichiarare un adattatore reporting. Il gioco e' specifico, ma
le superfici sono di piattaforma:

- player account history;
- admin finance sessions/detail;
- replay player;
- replay admin;
- round/session summary;
- fairness/audit fields;
- retention policy.

Un nuovo gioco non deve aggiungere un quarto branch esplicito nei componenti
finance/account. Deve registrarsi in un registry.

## 2. Required Game Descriptor

Ogni gioco deve fornire un descrittore equivalente a:

```text
GameReportingDescriptor
- game_code
- display_name
- route_slug
- round_identity_kind: round | session | access_session
- player_replay_endpoint(round_or_session_id)
- admin_replay_endpoint(round_or_session_id)
- replay_viewer
- finance_summary(row)
- account_history_summary(round/session)
- finance_detail_rows(round/session)
- fairness_summary(replay)
- retention_class
```

Il nome esatto puo' cambiare in implementazione, ma queste responsabilita' non
sono opzionali.

## 3. Backend Contract

Ogni gioco deve garantire:

| Area | Obbligo |
| --- | --- |
| Platform round | Ogni puntata reale deve creare/aggiornare `platform_rounds` con `game_code`, `title_code`, `wallet_type`, status terminale valido e ledger tx. |
| Ledger | Il gioco non scrive wallet/ledger direttamente: passa sempre dal boundary platform. |
| Game state | Il round/session game-specific conserva abbastanza stato per replay deterministico. |
| Player replay endpoint | Endpoint player ownership-safe, senza `server_seed` se non previsto. |
| Admin replay endpoint | Endpoint finance/admin con audit completo, incluso `server_seed` quando serve verificabilita'. |
| Finance enrichment | Serializer game-specific per spiegare il round in una frase leggibile. |
| Close/timeout | Refund/auto-cashout game-specific, visibile in replay/history. |

Esempi di finance enrichment:

- Mines: `5x5, 3 mines, 4 safe reveals, cashed out`
- BOXE: `8 rows, hard, 3 safe picks, loss on row 4`
- HI-LO: `3 correct predictions, 1 skip, cashout 11.50 CHIP`

La frase deve spiegare cosa e' successo a un admin finance, non a uno
sviluppatore.

## 4. Frontend Contract

Ogni gioco deve registrare:

| Surface | Obbligo |
| --- | --- |
| Player account | Label gioco, summary round, bottone replay, viewer corretto. |
| Admin finance | Detail session/round, summary leggibile, replay admin se disponibile. |
| Info modal | Replay tab nel modal info/rules, non CTA permanente sul tavolo salvo eccezione product. |
| Replay viewer | Render deterministico, compatto, leggibile desktop/mobile. |
| Error copy | Replay non disponibile = messaggio user-facing, non errore tecnico grezzo. |

Regola hard: niente fallback implicito a un altro gioco. Se il gioco non e'
registrato, la UI deve mostrare "Replay non disponibile" e non chiamare un
endpoint sbagliato.

## 5. Copy / Explanation Contract

Ogni gioco deve definire copy per:

- titolo round/sessione;
- outcome: win/loss/cashout/refund/expired/quarantined;
- configurazione gioco usata;
- azioni chiave compiute dal player;
- payout/bet/current exposure;
- fairness fields;
- replay unavailable/loading/error;
- admin finance summary.

Queste copy sono parte della feature, non polish. Se il replay esiste ma non si
capisce cosa racconta, Surface replay/reporting e' partial.

## 6. Retention Contract

Separare tre concetti:

| Concetto | Regola |
| --- | --- |
| Ledger finanziario | Non e' "retention replay": e' audit finanziario e non si cancella come payload UI. |
| Replay/audit payload | Conservazione da decidere prima della produzione; in locale/MVP non cancellare automaticamente. |
| Lista UI backoffice | Paginazione, filtri e "ultimi N" sono limiti di visualizzazione, non cancellazione dati. |

Decisione provvisoria per sviluppo locale:

- conservare tutti i replay terminali;
- paginare in UI;
- nessuna cancellazione fisica automatica prima di policy legale/prodotto.

Prima della produzione serve una decisione formale su durata, archiviazione,
eventuale anonimizzazione e accesso admin.

## 7. New Game Checklist

Prima di scrivere il backend del prossimo gioco:

1. definire `round_identity_kind`;
2. definire payload replay player/admin;
3. definire finance enrichment;
4. definire account history summary;
5. definire copy replay/error/fairness;
6. definire retention class;
7. aggiungere test contract che vieti branch non registrati.

Prima di chiamare il gioco green:

1. creare round demo e real;
2. verificare ledger transaction;
3. aprire player account e replay;
4. aprire admin finance detail e replay;
5. verificare copy leggibile;
6. verificare replay info modal;
7. verificare close/timeout in history/replay;
8. Product Owner walkthrough su `localhost:3000`.

## 8. Current Gap To Fix

Situazione 2026-05-24:

- Player account ha gia' fan-out Mines/BOXE/HI-LO.
- Backend espone admin replay per Mines/BOXE/HI-LO.
- Admin finance frontend e' ancora hardcoded BOXE/HI-LO e non registra Mines.
- `admin-finance-panel` usa un fallback implicito a BOXE per giochi non HI-LO.

Fix strutturale:

1. creare registry frontend reporting/replay;
2. registrare Mines, BOXE, HI-LO;
3. rimuovere fallback a BOXE;
4. aggiungere test per impedire il quarto branch;
5. poi usare lo stesso registry nel prossimo gioco.

## 8.1 Registry Implementation Snapshot - 2026-05-25

Narrow Rule 18 prerequisite implemented:

- frontend registry: `frontend/app/ui/game-reporting-registry.tsx`;
- registered descriptors: Mines, BOXE, HI-LO;
- player account history fetch/mapping/replay rendering consumes
  `GAME_ACCOUNT_HISTORY_DESCRIPTORS`;
- admin finance replay availability, endpoint routing and renderer consume the
  same reporting registry;
- backend finance/account/access-session dispatch uses lightweight builder /
  handler registries instead of game-code if-branches.

Hard rule after this snapshot:

- a fourth proprietary game must add one descriptor/handler entry;
- it must not add another `if game === "<new_game>"` in player account, admin
  finance replay, finance enrichment, account statement summary, or access
  session auto-settle dispatch;
- if a game is not registered, replay is unavailable rather than falling back to
  Mines, BOXE or HI-LO.

Broader finance traceability remains a separate platform WP: settlement
taxonomy, forward ledger metadata, retention policy and reconciliation reporting
are not closed by the narrow registry refactor.

## 9. Stop-And-Ask

Fermarsi prima del codice se:

- il gioco non ha un identificatore round/session chiaro;
- il replay non puo' essere ricostruito deterministicamente;
- il payload admin richiede dati sensibili non ancora approvati;
- la retention reale/legale viene confusa con paginazione UI;
- il finance summary non e' comprensibile a un admin non tecnico.
