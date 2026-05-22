Status: ACTIVE
Last meaningful update: 2026-05-21

# CasinoKing - Pre-Production External Audit - 2026-05-21

## Provenance

External high-level architecture audit ricevuto 2026-05-21 dal product owner
(Michele) da AI esterna specializzata. Memorizzato qui per persistenza in repo
(non solo nella macchina locale Michele) e per uso strategico durante la
transizione demo locale → produzione real-money.

**Relazione con altri doc**:

- `docs/PRODUCTION_READINESS_ROADMAP.md` - vista strategica 9 categorie. Questo
  audit informa le categorie infrastructure/scaling/architecture.
- `docs/PRODUCTION_READINESS_BRIEF.md` - checklist tecnica dettagliata. Le
  azioni proposte qui aggiungono entry alle sezioni infrastructure e
  performance.
- `docs/SECURITY_REVIEW_PRE_PRODUCTION_PLAN.md` - security review separata,
  non sovrapposta.

## Sommario audit

L'audit qualifica l'architettura attuale come **molto pulita e pensata per
gestire soldi veri in modo sicuro fin dal giorno zero**. Identifica 4 colli
di bottiglia che diventeranno critici nel passaggio a produzione real-money
con traffico significativo.

I 4 punti NON sono blocker per il rilascio iniziale beta/soft-launch (lo
stack locale + Docker + sync Postgres regge fino a un certo throughput), ma
sono ostacoli concreti al **vero scaling produzione** e devono essere
pianificati prima di un'apertura di volume.

## Punto 1 — Redis sta dormendo

### Osservazione audit

Redis e' configurato nello stack ma non attivamente usato ("configured, not
actively used"). In una piattaforma da casino, Redis dovrebbe essere il cuore
pulsante. Se ogni giocata, validazione RNG o session control fa andata/ritorno
su PostgreSQL, il DB diventa presto collo di bottiglia.

### Interpretazione CTO

Vero. Lo stack attuale (verificare con `infra/docker/docker-compose.yml`)
include Redis ma la gestione dello stato di sessione gioco e il catalog
result-caching avvengono sincronicamente su Postgres. Funziona in locale dove
il throughput e' un giocatore alla volta, non regge sotto picchi reali.

### Impact pre-produzione

- Catalog endpoint (`/games/library`, asset registry public_url, theme
  tokens): hit Postgres ad ogni request → cache miss costante.
- Session/round state: scritture Postgres per ogni reveal/cashout, lookup
  ledger sync.
- Demo token / access session validation: round-trip DB ad ogni action API.

### Suggested action (pre-produzione)

Aggiungere a `docs/PRODUCTION_READINESS_BRIEF.md` sezione Infrastructure /
Performance:

- WP-REDIS-CATALOG-CACHE: caching catalog response + theme tokens, TTL
  configurabile, invalidation su publish admin
- WP-REDIS-SESSION-STATE: spostare session/round state caching (mantenendo
  Postgres come source of truth ledger) per ridurre carico DB sotto picco
- WP-REDIS-RNG-FAIRNESS-CACHE: cache fairness proof material e seed metadata
  con TTL

## Punto 2 — Comunicazione REST HTTP per i giochi

### Osservazione audit

Flusso UI dei giochi → FastAPI usa HTTP/REST. Mines/Boxe sono async a turni
discreti quindi puo' bastare, ma HTTP ha overhead enorme. Nessuna traccia di
WebSocket o Server-Sent Events (SSE). Per round veloci, chat, drop di rete
o multiplayer, serve un protocollo persistente.

### Interpretazione CTO

Per Mines/BOXE attuali (turn-based discrete), HTTP/REST regge senza problemi
visibili al player. Diventa critico se:

- Si vogliono round veloci (slot a rotazione rapida, mini-game)
- Disconnect/resume con stato real-time
- Live dealer / multiplayer (non in scope CasinoKing v1, ma scope futuro
  catalog provider)
- Chat o notifiche push player
- Risparmio banda mobile

### Impact pre-produzione

- Disconnect/resume oggi richiede polling lato frontend (peggior caso UX:
  inconsistenza stato player vs server fino al prossimo refresh)
- Round time critical (es. blackjack) impossibili da renderizzare con buon
  UX su HTTP request/response

### Suggested action (pre-produzione)

Per CasinoKing v1 (Mines + BOXE turn-based): HTTP/REST sufficiente, nessun
upgrade necessario. Documentare la decisione esplicita.

Per CasinoKing v2/futuro (catalog allargato, provider esterni live):

- Audit del Session Recovery Engine design vs WebSocket alternative
- Valutare SSE per push notifiche player-side (bonus, jackpot, comunicazioni
  promo) come scope intermedio leggero

## Punto 3 — Il peso del DB Postgres

### Osservazione audit

Divisione logica in tabelle (UsersDB, LedgerDB, MinesDB, ecc.) ma fisicamente
convergono tutte sull'unico container PostgreSQL 16. Ledger e Game Rounds
avranno volume IOPS spaventoso rispetto al Catalog (quasi read-only). Servira'
scalare orizzontalmente o separare fisicamente DB di gioco da DB finanziari.

### Interpretazione CTO

Confermato dal `infra/docker/docker-compose.yml` attuale: un solo container
postgres. La separazione e' solo logica (schema separati, modules separati,
NON physical isolation).

### Impact pre-produzione

- Sotto carico: scritture ledger ad alto volume contendono con read catalog,
  con scritture game state, con auth lookup. Picchi → degrado generalizzato.
- Backup/restore: un solo DB significa backup unico, restore costoso (riporti
  giu' tutto il sistema), no isolamento failure.
- Compliance/audit: finance/ledger su DB separato e' best practice per audit
  AAMS/regulatory.

### Suggested action (pre-produzione)

- WP-DB-PHYSICAL-SEPARATION: piano di separazione fisica DB in 3 cluster:
  - `finance_db`: ledger, platform_rounds, wallet_balances
  - `game_db`: game session/round state, fairness, replay
  - `platform_db`: users, auth, catalog, asset registry, theme, sites
- WP-DB-READ-REPLICA-CATALOG: read-replica per catalog endpoint (quasi
  100% read), riduce carico master
- Aggiungere a `PRODUCTION_READINESS_BRIEF.md` sezione Infrastructure entry
  "DB physical separation pre-launch"

## Punto 4 — Dov'e' il Message Broker

### Osservazione audit

Quando MinesBE calcola payout, aggiorna Wallet e scrive Ledger. Sembra flusso
sincrono (modulo → platform → ledger). Sotto picco, scrittura ledger rallenta
→ tutto il gioco si blocca in attesa. Servirebbe RabbitMQ o Kafka per
disaccoppiare aggiornamenti finanziari da logica di gioco.

### Interpretazione CTO

Confermato. Flusso attuale (verificare con
`backend/app/modules/games/mines/round_gateway.py` +
`backend/app/modules/games/mines/platform_client.py` +
`backend/app/modules/platform/rounds/service.py`): sincrono. Game reveal →
platform round update → wallet adjust → ledger write, tutto inline.

### Impact pre-produzione

- Player waits durante scrittura ledger (latenza visibile UI su slow DB)
- No retry async: se ledger transient failure, game action fallisce hard
  invece di queue + retry
- No backpressure handling: spike traffico → wave di timeout
- Settlement async, ledger reconciliation, audit log: tutti pattern naturali
  per message broker, oggi non disaccoppiati

### Suggested action (pre-produzione)

- WP-MESSAGE-BROKER-INTRO: valutare RabbitMQ (transactional, lower learning
  curve) vs Kafka (high throughput, log-based, ecosystem maggiore). Decisione
  product+CTO.
- Pattern outbox pattern per scritture ledger: backend scrive event in tabella
  outbox + Postgres transactional commit; worker async drena outbox e settla
  ledger. Garantisce consistency anche con broker downtime.
- Reconciliation job notturno per audit AAMS-grade.

## Sintesi audit

> "E' un'architettura molto pulita e pensata per gestire soldi veri in modo
> sicuro fin dal giorno zero. La sfida principale per passare dalla 'fase
> locale' alla produzione sara' trasformare alcuni di quei flussi sincroni su
> Postgres in flussi asincroni in memoria (usando quel Redis che per ora
> riposa)."

L'audit non identifica errori critici di sicurezza o architettura. Conferma
che la base e' solida. I 4 punti sono **ottimizzazioni di scaling** che
diventano necessarie dal punto in cui CasinoKing apre a traffico reale di
volume.

## Tradeoff: cosa serve quando

| Stato | Cosa basta | Cosa aggiungere |
|---|---|---|
| Demo locale (oggi) | Stack attuale | Nulla |
| Beta closed (≤100 player simultanei) | Stack attuale + monitoring | Redis cache catalog |
| Soft-launch (~1000 player) | Beta setup | Redis session state, read-replica catalog |
| Produzione open | Soft-launch + tutto | DB physical separation, message broker, async ledger |

## Cosa NON e' coperto dall'audit

L'audit e' un colpo d'occhio architetturale. Non copre:

- Sicurezza applicativa (XSS, CSRF, SQL injection, auth flow). Coperto
  separatamente da `SECURITY_REVIEW_PRE_PRODUCTION_PLAN.md`.
- Compliance AAMS/regulatory specifica (audit log, KYC, AML, RNG cert).
  Backlog product owner.
- Frontend perf (bundle size, lazy load, CDN). Non menzionato.
- Test coverage / e2e suites. Coperto da `E2E_MANUAL_SMOKE_PLAN.md`.

## Prossime azioni (CTO post-audit)

1. Aggiornare `PRODUCTION_READINESS_BRIEF.md` con 4 nuove entry derivate da
   questo audit (Redis cache + Redis session state + DB separation + Message
   broker).
2. Aggiornare `PRODUCTION_READINESS_ROADMAP.md` linking a questo doc come
   reference audit esterno.
3. Quando si pianifica il pre-launch beta closed, prioritizzare WP-REDIS-*
   come primo step (lift performance basso costo).
4. WP-DB-PHYSICAL-SEPARATION e WP-MESSAGE-BROKER come scope soft-launch
   prep, non scope beta.
