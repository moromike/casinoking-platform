Status: ACTIVE
Last meaningful update: 2026-05-24

# Platform Financial Audit Traceability Plan

CTO approval required before implementation.

CTO review: `docs/PLATFORM_FINANCIAL_AUDIT_TRACEABILITY_CTO_REVIEW_2026-05-24.md`.

Current-state CTO review:
`docs/PLATFORM_FINANCIAL_AUDIT_TRACEABILITY_CURRENT_STATE_CTO_REVIEW_2026-05-24.md`.

CTO status: concept approved, implementation must be split. No automatic
financial correction, no ledger rewrite, and no broad migration before the
current-state matrix is complete.

## 1. Problematica

Il tema "log finanziari" non deve essere trattato come logging tecnico. Quando
si parla di soldi, CasinoKing deve poter ricostruire con precisione:

- da quale wallet e' uscito l'importo;
- quale round o sessione lo ha generato;
- quale azione del player o del sistema lo ha causato;
- quale idempotency key ha protetto la scrittura;
- quale replay/fairness payload spiega l'esito;
- se l'evento deriva da cashout manuale, auto-cashout, refund, void o admin
  action;
- quale admin ha fatto un'eventuale azione finanziaria.

Oggi esistono ledger, `admin_actions`, `platform_rounds`, replay e report
finance, ma la tracciabilita' cross-game e' ancora parziale e in alcuni punti
hardcoded. Questo e' stato gia' segnalato nel contratto finance/replay.

## 2. Principio di architettura

Il ledger e' la fonte contabile primaria. Non si corregge mai un gap finanziario
aggiungendo "un log" separato che racconta una cosa diversa dal ledger.

La regola e':

```text
Se impatta saldo -> ledger.
Se spiega perche' il ledger e' cambiato -> financial audit/replay reference.
Se e' mutazione admin finanziaria -> admin_actions + ledger.
Se e' debug tecnico -> application log.
```

## 3. Direzione alto livello

Costruire una tracciabilita' finanziaria uniforme per tutti i giochi:

1. registry game finance/replay adapter;
2. payload ledger metadata minimo e stabile;
3. collegamento obbligatorio tra ledger transaction e round/sessione;
4. replay deterministico per spiegare outcome;
5. admin finance view game-agnostic;
6. retention policy separata per ledger, replay payload e application logs;
7. reconciliation job per anomalie.

## 3.1 Current-State Matrix Obbligatoria

Prima di implementare codice, produrre una matrice reale:

| Area | Mines | BOXE | HI-LO | Gap |
| --- | --- | --- | --- | --- |
| Player account summary | TBD | TBD | TBD | TBD |
| Player replay route/viewer | TBD | TBD | TBD | TBD |
| Admin finance detail | TBD | TBD | TBD | TBD |
| Admin replay viewer | TBD | TBD | TBD | TBD |
| Ledger metadata `game_code` | TBD | TBD | TBD | TBD |
| Ledger metadata `title_code` | TBD | TBD | TBD | TBD |
| Ledger metadata `platform_round_id` | TBD | TBD | TBD | TBD |
| Access/table session link | TBD | TBD | TBD | TBD |
| Auto-settlement trace | TBD | TBD | TBD | TBD |
| Retention policy | TBD | TBD | TBD | TBD |

Senza questa matrice, il rischio e' ripetere il falso green gia' visto su BOXE
backoffice e HI-LO finance/replay.

## 4. Modello concettuale

Ogni evento economico di gioco dovrebbe essere spiegabile tramite una catena:

```text
Player / Admin
  -> Access session / Table session
  -> Game round
  -> Platform round
  -> Ledger transaction
  -> Ledger entries
  -> Replay / fairness payload
  -> Account/admin finance explanation
```

Questa catena deve essere navigabile sia dal player account sia dall'admin
finance, con livelli di dettaglio diversi.

## 5. Eventi finanziari da classificare

Categorie minime:

| Categoria | Esempi | Fonte |
| --- | --- | --- |
| Bet | start round, puntata table game | Ledger bet |
| Win/Cashout | cashout manuale, top-row auto-win | Ledger win |
| Loss | round perso senza payout | Round state + eventuale no settlement |
| Refund | start senza progress significativo | Ledger void/refund |
| Void | annullamento admin/sessione | Ledger void + admin_actions |
| Bonus/Admin | grant, adjustment | admin_actions + ledger |
| Auto settlement | timeout cashout/refund | access session + ledger |
| Quarantine | settlement incerto | dedicated status/audit, non inventare saldo |

Settlement taxonomy approvata:

| `settlement_kind` | Significato | Ledger |
| --- | --- | --- |
| `manual_cashout` | Player incassa volontariamente | win |
| `auto_cashout` | Sistema incassa per timeout/close dopo progress significativo | win |
| `refund_no_progress` | Round partito ma senza progress significativo | void/refund |
| `loss` | Round perso senza payout | no win, round terminal |
| `admin_void` | Admin annulla/forza chiusura | void + admin_actions |
| `expired_no_settlement` | Stato tecnico scaduto senza saldo da muovere | audit/reconciliation |
| `quarantined` | Stato finanziario incerto | quarantine/report, no auto-fix |

Ogni gioco deve definire cosa significa "progress significativo". Esempi:

- Mines: almeno una cella safe rivelata;
- BOXE: almeno una pick safe;
- HI-LO: almeno una previsione corretta.

## 6. Payload finanziario minimo

Ogni transazione ledger legata a gioco dovrebbe avere metadata coerente:

| Campo | Descrizione |
| --- | --- |
| `game_code` | engine/game |
| `title_code` | titolo giocato |
| `site_code` | sito/lobby di ingresso, se disponibile |
| `wallet_type` | cash/bonus/demo se applicabile |
| `platform_round_id` | id round platform |
| `game_round_id` | id round engine-specific |
| `access_session_id` | sessione real-money/table session |
| `settlement_kind` | manual_cashout/auto_cashout/refund/loss/void |
| `idempotency_key` | chiave namespaced |
| `replay_ref` | id o endpoint logico del replay |

Il metadata non deve duplicare l'intero replay. Deve contenere abbastanza
informazioni per raggiungerlo.

Demo vs real:

- real-money usa sempre platform ledger e access/table session dove applicabile;
- demo puo' usare demo wallet/event storage, ma deve offrire spiegazione
  coerente in UI;
- non mescolare demo storage e real ledger in report finanziari;
- i descriptor finance/replay devono dichiarare se un campo e' real-only,
  demo-only o comune.

Migration strategy:

- non riscrivere ledger storici senza piano dedicato;
- i nuovi metadata sono forward-only;
- vecchi round possono essere esposti con `metadata_completeness = legacy`;
- eventuali backfill sono read-only/analitycal finche' non approvati.

## 7. Replay come spiegazione finanziaria

Replay non e' solo UX. E' parte della spiegazione economica.

Per ogni gioco:

- player replay mostra esito in linguaggio comprensibile;
- admin replay mostra riferimenti audit/fairness piu' tecnici;
- entrambi ricostruiscono lo stesso round deterministico;
- account history e admin finance usano lo stesso registry di replay;
- nessun gioco deve cadere su fallback di un altro gioco.

## 8. Reconciliation

Serve un job di riconciliazione separato dai log:

- round aperti senza ledger start;
- ledger bet senza round;
- round terminali senza settlement atteso;
- access session scadute non chiuse;
- replay mancante per round settlement;
- idempotency conflict ripetuti;
- wallet balance non coerente con ledger entries.

Output:

- report admin;
- application log `critical` se impatta saldo;
- eventuale quarantine, mai correzione silenziosa.

Severity:

| Severity | Esempio | Azione |
| --- | --- | --- |
| `info` | replay mancante per demo legacy | report |
| `warning` | metadata legacy incompleto | report + follow-up |
| `financial_risk` | ledger bet senza round | alert + investigation |
| `quarantine_required` | settlement incerto real-money | blocco/triage manuale |

Il reconciliation MVP e' read-only/reporting. Non corregge saldi.

## 9. Retention

Retention separata:

| Oggetto | Retention |
| --- | --- |
| Ledger | Lunga / legale / non cancellazione applicativa ordinaria |
| Admin financial actions | Lunga, allineata al ledger |
| Replay payload | Policy esplicita, sufficiente a supporto/audit |
| Application logs | Piu' breve, storage esterno |
| Admin operational audit | Configurabile, non hard cap casuale |

Qualsiasi cancellazione/anonymization deve essere decisione product/legal, non
effetto collaterale di un limite UI.

## 10. Approccio a basso livello

### 10.1 Registry finance/replay

Introdurre un registry:

```text
game_code -> {
  replay_endpoint,
  player_replay_viewer,
  admin_replay_viewer,
  finance_summary_builder,
  account_summary_builder,
  settlement_explainer
}
```

Questo elimina branch hardcoded in account/admin finance e impedisce fallback
pericolosi.

Descriptor minimo:

```text
FinanceReplayDescriptor {
  game_code
  player_replay_endpoint
  admin_replay_endpoint
  player_replay_viewer
  admin_replay_viewer
  account_summary_builder
  admin_finance_summary_builder
  settlement_explainer
  supported_wallet_modes
  metadata_completeness
}
```

### 10.2 Settlement explanation

Ogni gioco deve fornire copy/descriptor per spiegare:

- configurazione iniziale;
- azioni del player;
- moltiplicatore/payout;
- esito;
- eventuale auto-settlement/refund.

### 10.3 Financial audit UI

Admin finance deve mostrare:

- sessione;
- round;
- ledger transaction;
- entries contabili;
- replay;
- settlement reason;
- anomaly flags.

Player account mostra una versione meno tecnica ma coerente.

## 11. Gate implementativi

- Nessun nuovo gioco senza finance/replay descriptor.
- Nessun fallback implicito a BOXE/Mines/HI-LO.
- Account e admin finance puntano allo stesso registry.
- Ogni settlement real-money e' idempotente e visibile.
- Replay ricostruisce round deterministico.
- Reconciliation smoke su casi base.
- CTO approva retention MVP.

MVP approvato:

- current-state matrix;
- registry finance/replay;
- rimozione fallback impliciti;
- Mines/BOXE/HI-LO descriptor;
- admin finance e player account consumano descriptor;
- retention MVP documentata;
- reconciliation report read-only su pochi controlli critici.

Fuori MVP:

- auto-repair;
- rewrite/backfill ledger storico;
- cancellazione fisica replay;
- nuova quarantine table salvo audit bloccante;
- cambio settlement behavior.

## 12. Effort stimato

Parte A dettagliata: 3-5 prompt.

Parte B MVP:

- registry finance/replay: 5-9 prompt;
- admin finance cleanup: 5-8 prompt;
- reconciliation MVP: 4-7 prompt;
- tests: 3-5 prompt.

Totale: 17-29 prompt.

## 13. Stop-and-Ask

Fermarsi se:

- una transazione economica non e' spiegabile dal ledger;
- si vuole correggere saldo fuori dal ledger;
- replay non e' deterministico;
- retention richiede decisione legale;
- un adapter game-specific richiede cambiare contratti platform.
