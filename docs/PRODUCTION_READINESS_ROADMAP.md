Status: ACTIVE
Last meaningful update: 2026-05-18

# CasinoKing — Production Readiness Roadmap

Mappa di tutto ciò che serve per portare CasinoKing da **demo locale** a
**produzione real-money** con player veri.

Questo documento è strategico, non operativo: elenca le 9 categorie di lavoro
necessarie, lo stato attuale di ognuna, e l'ordine consigliato per affrontarle.
Non sostituisce i brief operativi che verranno scritti per ogni singolo WP.

**Relazione con altri doc**:

- `docs/PRODUCTION_READINESS_BRIEF.md` (2026-05-07) — checklist tecnica
  complementare focalizzata su infrastruttura/security/observability/migration.
  Il ROADMAP è la vista strategica per 9 categorie; il BRIEF è la checklist
  tecnica dettagliata per le categorie 4 (Security), 5 (Infrastructure), 9
  (Operational). I due doc lavorano insieme.
- `docs/SECURITY_REVIEW_PRE_PRODUCTION_PLAN.md` — piano security review
  pre-produzione referenziato dal BRIEF nella sezione Gating.
- `project_deferred_initiatives.md` (memoria automatica CTO) — conferma quali
  iniziative sono esplicitamente rimandate a "produzione futura".

---

## 0. Stato attuale (2026-05-18)

| Stato | Valore |
|---|---|
| Modalità prodotto | Demo locale (Docker, no player veri) |
| Obiettivo strategico Maggio 2026 | Cleanup tecnico + BOXE come prototipo di metodo per giochi 3-20 |
| Produzione real-money | Non avviata; pre-requisiti mai affrontati formalmente |
| Iniziative pronte per produzione | Nessuna |
| Iniziative in design futuro | Math testing (BOXE 2A) parzialmente, Session Recovery Engine designed |

---

## 1. Le 9 categorie

| # | Categoria | Cosa significa | Stato attuale | Priorità ordering |
|---|---|---|---|---|
| 1 | Legal & licensing | Entità legale, licenza gambling per giurisdizione, T&C, privacy policy, KYC requirements legali | Non avviato | **Prima** (blocca tutto il resto operativamente) |
| 2 | Compliance | KYC, AML, age verification, geolocation, responsible gaming tools, GDPR | Non avviato | Dopo licensing |
| 3 | Math & game certification | Certificazione attuariale RTP, fairness audit, ente terzo (eCOGRA/GLI/iTech Labs) | BOXE Fase 2A produce math spec, simulator e stress framework; Mines retroactive pianificato | **In costruzione in parallelo** |
| 4 | Security audit | Penetration test, vuln scan, code review esterno, encryption at-rest/in-transit | Non avviato | Pre-launch |
| 5 | Infrastructure | Production deployment (cloud), monitoring, alerting, SLA, backup, disaster recovery, scaling | Non avviato (Docker locale) | Dopo math + security |
| 6 | Payment integration | KYC verificato, deposit/withdraw, crypto direct (BTC/ETH/Ripple), wallet custody, dispute handling | Designed but deferred (no gateway, blockchain direct) | Dopo compliance |
| 7 | Player support | Helpdesk, dispute resolution, chat/email/ticketing, multi-lingua | Non avviato | Pre-launch |
| 8 | Marketing & acquisition | Affiliate program, SEO, paid ads, brand, content, social | Non avviato | Pre-launch + ongoing |
| 9 | Operational | 24/7 oncall, runbook incidenti, SLA player-facing, financial reconciliation manuale, fraud detection | Non avviato | Pre-launch + ongoing |

---

## 2. Dettaglio per categoria

### 2.1 Legal & licensing

**Cosa serve**:
- Entità legale registrata (SRL/SpA o equivalente)
- Licenza gambling per giurisdizione target (Malta MGA, Curaçao, UK Gambling Commission, AAMS/ADM Italia, ecc.)
- Terms & Conditions player-facing
- Privacy policy GDPR-compliant
- Requirements KYC legali per giurisdizione

**Stato attuale**: nessuna decisione product/business sull'entità o giurisdizione

**Bloccante per**: tutto il resto operativamente (no licenza = no real-money legalmente)

**Cosa possiamo iniziare ora**: nulla tecnicamente; decisione product/business

### 2.2 Compliance

**Cosa serve**:
- **KYC**: verifica identità player (documenti, selfie, address proof). Wizard registrazione esteso oltre i 3 campi attuali
- **AML**: anti-money-laundering checks (PEP, sanction lists, transaction monitoring)
- **Age verification**: hard gate 18+ (o 21+ giurisdizione)
- **Geolocation**: blocco giurisdizioni vietate (GeoIP + verification)
- **Responsible gaming**: self-exclusion, deposit limits, loss limits, time-out, reality check
- **GDPR**: right to be forgotten, data export, consent management

**Stato attuale**:
- Wizard registrazione attuale: 3 campi base (vedi `project_deferred_initiatives.md`)
- KYC/AML/geolocation: zero
- Responsible gaming tools: zero

**Cosa possiamo iniziare ora**: design wizard registrazione esteso (doc only), no implementazione

### 2.3 Math & game certification

**Cosa serve**:
- Math spec formalizzata per ogni gioco
- Test stress estensivi (10M+ round, RTP empirico, distribuzione varianza)
- Simulator esterno indipendente dal backend
- Audit del codice math da ente terzo
- Certificazione attuariale RTP da ente accreditato (eCOGRA / GLI / iTech Labs / BMM)
- Submission test results + certificazione a regolatori

**Stato attuale**:
- BOXE Fase 2A include math spec doc, simulator esterno, stress test framework e anchor reconciliation
- Mines retroactive: WP pianificato (`WP-MINES-MATH-CERTIFICATION-READY`) dopo BOXE 2A
- Audit terzo + certificazione: non avviato (costa €€€, richiede prodotto stabilizzato)

**Cosa stiamo facendo ora**: costruiamo il materiale (spec + simulator + test) ora durante BOXE; certificazione esterna quando andiamo verso produzione

**Materiale che sarà pronto**:
- Mines + BOXE math spec formalizzata
- Simulator esterno per Mines + BOXE
- Stress test framework on-demand riusabile
- Fairness verification verifiable on-chain (pattern Mines già esiste)

### 2.4 Security audit

**Cosa serve**:
- Penetration test (esterno, professional)
- Vulnerability scan automatizzato in CI
- Code review esterno (security-focused)
- Encryption at-rest (DB) + in-transit (HTTPS/TLS)
- Secret management (no hardcoded keys, vault)
- Session security review
- API rate limiting + DoS protection
- Audit log security
- Backup encryption

**Stato attuale**:
- Encryption in-transit: HTTPS in deployment (TBD per produzione)
- Encryption at-rest: TBD per produzione
- Secret management: env vars semplici
- Penetration test: mai eseguito
- Rate limiting: TBD

**Cosa possiamo iniziare ora**: vulnerability scan automatizzato in CI (basso costo); review architetturale security (doc only)

### 2.5 Infrastructure

**Cosa serve**:
- Production deployment cloud (AWS / GCP / Azure / OVH)
- Monitoring (Prometheus / Datadog / NewRelic)
- Alerting (PagerDuty / Opsgenie)
- SLA player-facing dichiarato
- Backup automatizzato + tested restore
- Disaster recovery plan
- Scaling automatico (load balancer, container orchestration)
- CDN per asset statici
- DB replica / failover
- Logging centralizzato

**Stato attuale**: Docker Compose locale, zero produzione

**Cosa possiamo iniziare ora**: design infrastructure target (doc), no implementazione

### 2.6 Payment integration

**Cosa serve**:
- Deposit flow con KYC verifica
- Withdraw flow con manual review (anti-fraud) o automatic per amount sotto soglia
- Crypto direct: BTC, ETH, Ripple wallets (custody decision: custodiale vs non-custodiale)
- Fiat option? (decisione product: solo crypto o anche fiat?)
- Dispute handling (chargeback prevention)
- Transaction monitoring real-time
- Cold/hot wallet strategy

**Stato attuale**:
- Wallet interno player: cash + bonus, funziona in demo
- Deposit/withdraw esterni: zero
- Crypto integration: deferred (vedi `project_deferred_initiatives.md`)
- Custody decision: non presa

**Cosa possiamo iniziare ora**: design crypto integration architecture (doc), no implementazione

### 2.7 Player support

**Cosa serve**:
- Helpdesk (ticketing system)
- Live chat 24/7 o orari estesi
- Email support
- Dispute resolution process (interno + escalation regolatore)
- Multi-lingua (almeno le 4 supportate: it, en, de, es)
- FAQ + knowledge base
- Player communications (email transactional, marketing opt-in)

**Stato attuale**: zero

**Cosa possiamo iniziare ora**: design supporto operativo (doc), no implementazione

### 2.8 Marketing & acquisition

**Cosa serve**:
- Affiliate program (commissioni, tracking)
- SEO (content, backlinks, site speed)
- Paid ads (Google Ads se compliant, social, programmatic)
- Brand identity (logo, voice, messaging)
- Content marketing
- Social media presence
- Influencer partnerships
- Email marketing automation
- Referral program

**Stato attuale**: zero

**Cosa possiamo iniziare ora**: nulla tecnicamente; decisione product/business

### 2.9 Operational

**Cosa serve**:
- 24/7 oncall rotation
- Runbook per incidenti comuni
- SLA player-facing dichiarato
- Financial reconciliation manuale + automatica
- Fraud detection (pattern, ML, manual review queue)
- KPI dashboard interno (retention, conversion, churn, LTV)
- Compliance reporting (audit trail per regolatori)
- Player risk scoring
- Bonus abuse detection
- Bot detection
- Session anomaly detection
- Reporting financial real-time (vs Mines current "demo finance")

**Stato attuale**:
- Reporting financial demo: sezione finance funziona in admin
- Tutto il resto: zero

**Cosa possiamo iniziare ora**: design KPI dashboard (doc), fraud detection design (doc)

---

## 3. Roadmap suggested order

**Fase A — Pre-decision (now, parallel to BOXE)**:
1. Math & game certification material (BOXE 2A + Mines retroactive) — **in costruzione**
2. Design docs per altre categorie (no implementazione, solo mappa di cosa servirà)
3. Decisione product/business su giurisdizione legale + entità

**Fase B — Decision taken (after BOXE closed, before launch)**:
4. Legal & licensing (richiede entità + giurisdizione)
5. Compliance implementation (KYC, AML, geolocation, responsible gaming, GDPR)
6. Security audit (penetration test esterno)
7. Infrastructure production deployment
8. Payment integration (crypto direct)

**Fase C — Pre-launch operational**:
9. Player support setup
10. Marketing & acquisition setup
11. Operational runbook + 24/7 oncall

**Fase D — Launch**:
12. Submission certificazione + licensing approval
13. Soft launch limited geographies
14. Full launch

---

## 4. Cosa stiamo facendo ORA in preparazione

| Item | Stato | Doc |
|---|---|---|
| Math testing framework (BOXE) | Implementato in Fase 2A | `docs/games/boxe/MATH_SPEC.md`, `tests/stress/boxe_math/` |
| Math testing retroactive (Mines) | WP pianificato | Da aprire dopo BOXE 2A merge |
| Math spec doc per gioco | BOXE pronto; pattern per prossimi giochi | `docs/games/boxe/MATH_SPEC.md` |
| Simulator esterno standalone | BOXE pronto; pattern per prossimi giochi | `tools/boxe_math_simulator.py` |
| Stress test framework on-demand | BOXE pronto; pattern per prossimi giochi | `tests/stress/boxe_math/` |
| Session Recovery Engine design | Designed | `docs/SESSION_RECOVERY_ENGINE_DESIGN.md` |
| Capability Inventory aggiornato | Living doc | `docs/CAPABILITY_INVENTORY_2026-05-17.md` |
| Backoffice manual | Living doc | `docs/BACKOFFICE_MANUAL.md` |

---

## 5. Cosa NON stiamo facendo (esplicitamente)

| Item | Quando affrontarlo |
|---|---|
| Licensing gambling | Fase B (post-BOXE) |
| KYC wizard implementation | Fase B |
| Crypto payment implementation | Fase B |
| Production infrastructure | Fase B |
| Penetration test esterno | Fase B |
| Certificazione attuariale esterna | Fase D (pre-launch) |
| Affiliate program | Fase C |
| 24/7 oncall | Fase C |

Vedi `project_deferred_initiatives.md` per la versione "memoria CTO" delle deferred initiatives.

---

## 6. Riferimenti

- Strategic priorities maggio 2026: memoria CTO `project_strategic_priorities.md`
- Deferred initiatives: memoria CTO `project_deferred_initiatives.md`
- BOXE prototipo di metodo: `docs/BOXE_PROJECT_BRIEF.md` (untracked finché Fase 0 non parte)
- Playbook giochi: `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`
- Session recovery: `docs/SESSION_RECOVERY_ENGINE_DESIGN.md`
- Capability inventory: `docs/CAPABILITY_INVENTORY_2026-05-17.md`

---

## 7. Maintenance rule

Questo doc è **strategico**, non operativo. Va aggiornato quando:

- Una categoria cambia stato significativamente (es. Math passa da "in costruzione" a "framework pronto")
- Una nuova categoria emerge (es. multi-tenant, white-label)
- L'ordering cambia (es. licensing risolto per una giurisdizione specifica)
- Stato "deferred" di una categoria viene sbloccato (richiede esplicito sblocco product/business)

Aggiornamento minimo: 1 volta per gioco completato (refresh stato categoria 3 Math) + ad ogni cambio strategico product/business.
