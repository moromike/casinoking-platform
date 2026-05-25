Status: ACTIVE
Last meaningful update: 2026-05-25

# Prompt Codex - COINS Fase 0+1 SPEC and Architecture Mapping

Workstream: chiusura Fase 0 (SPEC) + Fase 1 (Architecture Mapping) per il
gioco COINS, seguendo il pattern HI-LO/BOXE del playbook.

## Prompt da incollare in Codex

```
You are CTO assistant for CasinoKing platform.

Parte A: validate approach, list documents you plan to produce, identify gaps,
counter-propose if you see issues.
Parte B: execution starts only after CTO approval of Parte A.

=== CONTEXT (you start cold) ===

CasinoKing è una piattaforma di casino games con 3 giochi proprietari già in
produzione: Mines, BOXE, HI-LO. Ora si integra il 4° gioco proprietario:

  COINS - instant-win coin-flip (riferimento Hacksaw Gaming Dare2Win)

Le decisioni product di Fase 0 sono CHIUSE. Devi produrre il contratto
documentale Fase 0 (SPEC) + Fase 1 (Architecture Mapping) seguendo il
metodologia del playbook. Nessun codice production toccato in questo WP.

=== REQUIRED READING (in questo ordine) ===

Metodologia platform:
1. docs/README.md
2. docs/SOURCE_OF_TRUTH.md
3. docs/TASK_EXECUTION_GUARDRAILS.md
4. docs/AI_CRITICAL_JUDGMENT_RULES.md
5. docs/ACTIVE_OPEN_LOOPS.md
6. docs/NEW_GAME_INTEGRATION_PLAYBOOK.md (fasi, regole, anti-pattern,
   12-surface, Rule 18, 19, 20, 22, 24, 25)
7. docs/NEW_GAME_BRIEF_TEMPLATE.md

Replication briefs HI-LO e BOXE:
8. docs/NEXT_GAME_REPLICATION_BRIEF_FROM_HI_LO_2026-05-23.md
9. docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_HI_LO_2026-05-23.md

Pattern reference (HI-LO è il riferimento più recente):
10. docs/games/hi-lo/SPEC.md
11. docs/games/hi-lo/SOURCE_INVENTORY_2026-05-22.md
12. docs/games/hi-lo/HI_LO_PRODUCT_DECISION_MAP_2026-05-22.md
13. docs/games/hi-lo/HI_LO_OPEN_QUESTIONS_2026-05-22.md
14. docs/games/hi-lo/HI_LO_12_SURFACE_STATUS_2026-05-22.md
15. docs/games/hi-lo/ARCHITECTURE_MAPPING.md
16. docs/games/hi-lo/MATH_SPEC.md

Pattern BOXE come secondo riferimento:
17. docs/games/boxe/SPEC.md
18. docs/games/boxe/ARCHITECTURE_MAPPING.md
19. docs/games/boxe/MATH_SPEC.md

Contratti platform trasversali:
20. docs/GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md
21. docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md
22. docs/ARCHITECTURE_ATLAS_MINES.md
23. docs/CAPABILITY_INVENTORY_2026-05-17.md
24. docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md

COINS-specific inputs:
25. games/coins/COINS - analisi gemini funzionale_v01.md
    (analisi funzionale generata da skill Gemini su video+screenshot;
    copre math/UI/animazioni/autoplay/API; NON copre state machine,
    idempotency, mode, lifecycle, replay, asset contract — questi sono
    coperti dal documento sotto)
26. docs/games/coins/COINS_OPEN_QUESTIONS_2026-05-25.md
    (25 Q product + round 2 follow-up CHIUSE con risposte definitive
    Michele; questo è il contratto product da convertire in SPEC tecnico)
27. assets/Games/coins/ (asset sorgente, per riferimento)

=== DECISIONI PRODUCT GIÀ CHIUSE (riepilogo da COINS_OPEN_QUESTIONS) ===

Non riaprire queste decisioni. Sono già state validate da Michele il
2026-05-25. Se le rileggi e qualcosa non torna, Stop-and-Ask.

Identità:
- Game code: "coins"
- Engine name: "coins"
- Route pubblica: /coins (da confermare in Parte A se differente)
- Primo title variant code: proporre tu (es. "coins001" o "coins_classic"),
  allineato al naming Mines/BOXE/HI-LO

Math:
- Formula payout: M(N) = 0.98 * 2^N
- RTP: 98% fisso
- N range Wave 1: 1..10 (N=11,12 abilitabili Wave 2)
- Max win cap: 5.000× bet (configurabile admin via Title Editor)
- Bet range osservato: €0.20-€200, configurabile admin

Modes:
- Demo + Real Cash + Real Bonus, tutti e 3 al lancio (come Mines/BOXE/HI-LO)
- Currency: EUR (multivaluta crypto = M-section, fase 2 produzione)

State machine:
- IDLE → BET_PLACED → SPINNING → RESOLVED
- Round chiude in <2s
- Autoplay = sequenza N round indipendenti, NO stato session-level autoplay

Auto-settlement (Rule 22 playbook):
- BET_PLACED non ancora SPINNING → refund_no_progress
- SPINNING → settle naturale (RNG già lanciato server-side)
- Disconnect durante autoplay tra round → stop autoplay, no new bet
- Game-specific dispatcher tramite platform access-session policy

Idempotency:
- client_idempotency_key UUID generato dal client
- TTL 5 minuti
- Server riconosce duplicato e restituisce stessa risposta

Replay:
- Storage minimo: {coin_matrix, N, bet, multiplier, payout, mode, timestamp,
  idempotency_key_hash}
- Replay viewer rirenderizza animazione deterministica sugli stessi indici
- Entry point player: dentro modal info, tab "Replay" (Rule 20 playbook)
- NO CTA Replay permanente sulla play surface
- Account history + Admin finance: registry/adapter pattern (Rule 18) -
  GIÀ IMPLEMENTATO in workspace (game-reporting-registry.tsx); NON toccare

Title Editor / Operator Settings:
- Bet range (default €0.20-€200)
- N range monete (default 1-10)
- Max win cap (default 5.000× bet)
- Autoplay limits (rounds, loss limit, win limit)
- Copy / Rules HTML (i18n IT+EN+DE+ES)
- Asset (monete H/X, background, sound)
- Theme tokens (palette neon)
- Pattern Title Editor identico a Mines/BOXE/HI-LO

Lingue:
- IT + EN + DE + ES (4 lingue, stesso set di Mines/BOXE/HI-LO)
- ALLOWED_LOCALES = ("it", "en", "de", "es")
- Copy nel manifest i18n, NO hardcoded (Rule 25 playbook)

Shell platform (12-surface check obbligatorio):
- TUTTE le superfici platform riusate via GameRuntimeShell:
  - Lobby card (pattern Mines/BOXE/HI-LO)
  - Launch Cashier modal
  - Provider intro gate
  - How-to-play gate
  - Table balance gate
  - Short viewport gate
  - Mobile rotation gate
  - Embed mode `?embed=1` - GIÀ IMPLEMENTATO via useGameEmbedBridge in
    workspace; NON toccare
- Game-specific (game-owned, non platform):
  - Board adapter (coin grid layout)
  - Payout adapter (multiplier badge corrente + max win)
  - Control rail content (toggle Manual/Auto + griglia 1-N + bet)

Control rail (Rule 16):
- GameControlRail condiviso + schema adapter game-specific
- Layout custom COINS (toggle Manual/Auto + griglia selettore N) via
  registry pattern, NO if-game-branch

Theme:
- Variant del platform theme tramite advanced skin (sistema Mines già lo
  supporta)
- Palette default COINS: blu-notte (sfondo), verde neon #4ade80 (selection),
  ciano neon #00f0ff (heads), viola desaturato (idle/tails)
- Configurabile admin in Title Editor (palette tokens)
- Theme advanced editing pieno = Wave 2, NON Wave 1

Mobile:
- Cella adattiva (Rule 14 playbook): no scrollbar, no clipping, board sempre
  visibile per ogni N
- Mobile portrait: griglia 4×3 si adatta per N=12 (riferimento mockup), per
  N più piccoli centratura proporzionale
- Landscape-short gate riusato (pattern Mines/BOXE/HI-LO)
- Michele non testa mobile in prima persona: responsabilità Codex/CTO

Embed mode:
- ?embed=1 supportato (Mines/BOXE/HI-LO già lo fanno)
- postMessage handshake close + fullscreen-state via useGameEmbedBridge
- GIÀ IMPLEMENTATO in workspace per Mines/BOXE/HI-LO; NON toccare

Assets:
- Moneta (4 stati: idle, spin, H, X):
  - opzione A: immagini PNG 256×256, max 100KB per file, caricabili da admin
  - opzione B: caratteri editabili (testo H/X, font/colore via theme)
  - SCELTA Michele (L5): ENTRAMBE - admin sceglie se carica immagine o
    edita testo. Default: caratteri (no asset richiesto al lancio).
- Background gameplay: PNG 1920×1080, max 500KB, oppure gestito via theme
- Sound: 3 eventi (spin, win, lose) MP3 max 200KB ciascuno
- Lobby card + icona engine: format Mines (PNG ottimizzati)
- Upload guidance esplicita nel Title Editor (Rule playbook Phase 4B)

Animazione:
- Reduced-motion (prefers-reduced-motion) → spin diventa fade in/out (no
  rotazione 3D + motion blur)
- Animazione base solida in Wave 1 (Phase 3C playbook)
- Polish (rotazione 3D + motion blur tipo Hacksaw) = mini-progetto post
  Wave 1 (M6), tema annotato non dimenticato

Failure UX (Rule 25):
- Errori standard mappati a copy i18n manifest:
  - insufficient_balance, table_expired, network_error, config_missing,
    malfunctioning, bet_out_of_range
- No stringa hardcoded nel runtime
- Lista platform errors + game-specific COINS errors definita in SPEC

Autoplay edge cases:
- balance<bet → auto-stop + dialog "Saldo insufficiente"
- loss_limit raggiunto → auto-stop + dialog
- single_win_limit raggiunto → auto-stop + dialog
- disconnect → stop alla prossima resa, no new round

Fairness/RNG:
- Server-side RNG sempre
- Seed deterministico archiviato per ogni round (per audit/cert)
- Provably fair con client seed = futuro probabile non certo (M4)

Wave 1 scope (cosa entra al primo merge):
- Demo + Real Cash + Real Bonus end-to-end
- Autoplay base (rounds + loss limit + win limit + custom)
- Title Editor con config + copy + rules + asset upload + theme base
- Lobby card + launch flow
- Finance + replay funzionanti
- IT + EN + DE + ES

Wave 2 differito (annotato M-section, non Wave 1):
- RTP variants 97% / 99%
- N=11/12 abilitabili
- Provably fair client-seed
- Theme advanced editing pieno
- Polish animazione 3D (mini-progetto)
- Multivaluta crypto (fase 2 produzione)

=== PREREQUISITI PLATFORM (già chiusi in workspace, non riaprire) ===

1. Rule 18 - frontend game-reporting-registry: registry account history +
   admin finance + replay routing. File: frontend/app/ui/game-reporting-registry.tsx
   Mines/BOXE/HI-LO già registrati, no fallback BOXE/Mines.

2. Embed mode parity (useGameEmbedBridge): Mines/BOXE/HI-LO consumano lo
   stesso bridge con postMessage handshake. Audit:
   docs/games/coins/EMBED_MODE_PARITY_AUDIT_2026-05-25.md

Quando Wave 1 COINS partirà, COINS si registrerà al game-reporting-registry
e consumerà useGameEmbedBridge come gli altri 3 giochi - NO if-branch.

=== WP NON BLOCCANTI PER FASE 0+1 COINS (ma noti) ===

- WP-FINANCE-REPLAY-REGISTRY-RETENTION ampio (settlement taxonomy + forward
  metadata + Mines admin replay parity + BOXE wallet bug + retention doc +
  reconciliation report) - CTO review in
  docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md
  Procede in parallelo. SPEC COINS può citare "settlement_kind via forward
  metadata, TBD finalize after WP-FINANCE merge".

- 3 WP platform foundation (Error/Logging/Settings) - CTO review pronte.
  Anche questi paralleli a COINS Fase 0+1.

=== Parte A - OUTPUT ATTESO ===

Produci UN documento di plan in
docs/games/coins/COINS_PHASE_0_1_PLAN_2026-05-25.md che contenga:

1. Lista documenti che intendi produrre, in quale ordine, con breve
   descrizione del contenuto previsto. Default proposto CTO (validare/
   correggere):

   a. docs/games/coins/SOURCE_INVENTORY_2026-05-25.md
      Inventario sorgenti: analisi Gemini, screenshot, riferimenti
      Hacksaw, gap rispetto a fonti reali.

   b. docs/games/coins/COINS_PRODUCT_DECISION_MAP_2026-05-25.md
      Estrazione strutturata delle decisioni da COINS_OPEN_QUESTIONS,
      classificate (game-specific / platform-default / wave-1-vs-2 /
      future-annotation).

   c. docs/games/coins/COINS_12_SURFACE_STATUS_2026-05-25.md
      Per ognuna delle 12 superfici (Playbook 6.3): pattern atteso,
      capability platform consumata, gap potenziali, evidenza pre-WP1.

   d. docs/games/coins/SPEC.md
      Contratto Fase 0, modellato su HI-LO SPEC: Scope/Sources/Decisions,
      Game Identity, Core Rules, State Machine, Idempotency, Replay
      contract, Visual Layout, Operator Settings, Failure UX, Test gates,
      Stop-Before-Code items.

   e. docs/games/coins/MATH_SPEC.md
      Math, RNG, fairness contract: formule, payout matrix, RTP target,
      max-win cap, seed/fairness model, simulator harness atteso.

   f. docs/games/coins/ARCHITECTURE_MAPPING.md
      Fase 1 contract: matrice common vs game-specific vs platform-
      extension, WP list per Fasi 2-7, protected file/area list, contract
      tests, smoke baseline, admin manual update plan, capability matrix
      skeleton per ogni WP.

2. Per ognuno dei 6 documenti, una descrizione di cosa NON va dentro
   (es. policy: math non in SPEC ma in MATH_SPEC; etc.).

3. Lista dei [STOP-AND-ASK] - decisioni che ti sembrano ambigue dopo aver
   letto COINS_OPEN_QUESTIONS. Esempi tipici:
   - route /coins vs /coin-flip vs altro?
   - title variant code primo?
   - settlement taxonomy per COINS: usa quale subset dei 7 valori?
   - max-win cap UI behavior: avviso pre-bet o cap silenzioso?

4. Lista delle aree dove identifichi sorgenti/info mancanti:
   - mockup Wave 1 final visivi mancanti?
   - asset reali (PNG monete, background, sound) attesi quando?
   - Hacksaw legal review per assomiglianza?

5. Capability matrix preliminare per i WP che produrrai in Fase 2+:
   - WP-COINS-2A-MATH-RNG (math/fairness)
   - WP-COINS-2B-SCHEMA-STATE (state machine + repository + migrations)
   - WP-COINS-2C-API (endpoints start/bet/replay/idempotency)
   - WP-COINS-2D-ADAPTER-FINANCE-REPLAY (platform adapter)
   - WP-COINS-3A-STANDALONE-BOOT (frontend standalone wrapper)
   - WP-COINS-3B-GAMEPLAY (board, control rail content, payout)
   - WP-COINS-3C-ANIMATIONS (animation polish base)
   - WP-COINS-4A-CONFIG-COPY-RULES (Title Editor config/copy/rules)
   - WP-COINS-4B-ASSETS-SOUNDS-THEME (asset upload, theme tokens, lobby)
   - WP-COINS-5-SITE-LOBBY (engine/title seeding, lobby integration)
   - WP-COINS-6-DOCS-ATLAS (atlas COINS)
   - WP-COINS-7-E2E-VALIDATION

   Per ogni WP: 1 riga capability matrix preliminare con stime DB/Backend/
   API/Admin/Player/CSS/Test/Docs (NEW/UPDATE/n-a).

6. Stop-and-Ask trigger di Parte A:
   - decisione product nuova emerge non in COINS_OPEN_QUESTIONS;
   - capability platform che non è ancora pronta;
   - mismatch tra analisi Gemini e decisioni Michele;
   - sorgente necessario al lavoro che non trovi nel repo.

NON eseguire codice in Parte A. Solo plan + audit + Stop-and-Ask.

=== Parte B - SOLO DOPO APPROVAZIONE CTO ===

Produzione dei 6 documenti elencati in Parte A, rispettando:

- Pattern docs HI-LO/BOXE come reference visivo della struttura sezioni.
- Status header su ogni file: "Status: ACTIVE" + "Last meaningful update: 2026-05-25".
- File-citation per ogni claim che riferisce a codice esistente o doc esistente
  (formato `backend/path/file.py:line` o `docs/file.md`).
- Nessun codice production toccato. Documenti-only WP.
- Aggiornare nello stesso PR:
  - docs/README.md tabella documenti attivi (6 nuove righe in `docs/games/coins/`);
  - docs/ACTIVE_OPEN_LOOPS.md riga COINS riflettendo "Fase 0+1 chiuse, pronti
    per Fase 2A math";
  - docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md (mappa) può essere
    aggiornata o annotata come "no map change since Fase 0+1 è docs-only;
    update richiesto al primo WP che tocca codice".

Convenzioni di Sezioning (modellate su HI-LO):

- SPEC.md sezioni: 0.Scope/Sources/Decisions, 1.Identity, 2.Core Rules,
  3.State Machine, 4.Idempotency, 5.Replay, 6.Visual Layout, 7.Operator
  Settings, 8.Failure UX, 9.Test Gates, 10.Stop-Before-Code Items.

- MATH_SPEC.md sezioni: 1.Formule, 2.Payout Matrix Full, 3.RTP target,
  4.Max-Win Cap, 5.RNG model, 6.Fairness/Seed, 7.Simulator Harness, 8.Test
  cases.

- ARCHITECTURE_MAPPING.md sezioni: 1.Common vs Game-specific vs Platform-
  Extension matrix, 2.WP list Fasi 2-7, 3.Protected files, 4.Contract tests,
  5.Visual baselines, 6.Admin manual update plan, 7.Capability matrix
  skeleton.

=== VINCOLI HARD ===

- I 2 prerequisiti workspace (Rule 18 registry + embed parity) sono già
  chiusi. NON modificarli. Quando SPEC li cita, riferiscili come "platform
  capability esistente, COINS la consuma".
- WP-FINANCE-REPLAY-REGISTRY-RETENTION ampio: NON bloccante per Fase 0+1
  COINS. SPEC può citare "settlement_kind = TBD when WP-FINANCE-RETENTION
  finalizes forward metadata contract", ma non aspettare quel WP per
  produrre SPEC.
- Nessuna modifica a Mines/BOXE/HI-LO. Se serve cambio, Stop-and-Ask.
- Nessuna decisione product nuova. Tutte le decisioni stanno già in
  COINS_OPEN_QUESTIONS. Stop-and-Ask se emerge novità.
- 4 lingue IT+EN+DE+ES = vincolo hard. Non aggiungere/togliere.
- Allineamento Rule 18, 19, 20, 22, 24, 25 del playbook: verifica esplicita
  per ogni regola in SPEC.

=== INIZIA CON Parte A ===

Produci il piano in COINS_PHASE_0_1_PLAN_2026-05-25.md e fermati.
Aspetti CTO approval prima di scrivere i 6 documenti finali.

Stima effort Parte B post-approvazione: 6-10 prompts (un doc per ronda con
review CTO veloce per ognuno).
```

---

## Note d'uso per Michele

- Codex parte cold con questo prompt. Tutta la decisional context COINS sta
  nel prompt + nei file linkati in REQUIRED READING.
- Stima effort totale: Parte A = 2-3 prompts (plan + Stop-and-Ask),
  Parte B = 6-10 prompts (6 documenti, magari iterati).
- L'output Parte A è un singolo documento `COINS_PHASE_0_1_PLAN_2026-05-25.md`
  che tu mi giri per approvazione/correzioni prima di lasciare partire la
  Parte B.
- Quando i 6 documenti escono, hai il **contratto completo Fase 0+1 COINS**.
  Da lì si parte con Fase 2A (math/RNG) seguendo il playbook.

## Riferimenti

- `docs/games/coins/COINS_OPEN_QUESTIONS_2026-05-25.md` - decisioni product
- `games/coins/COINS - analisi gemini funzionale_v01.md` - analisi Gemini
- `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` - playbook
- `docs/games/hi-lo/SPEC.md` - template SPEC reference
- `docs/games/hi-lo/ARCHITECTURE_MAPPING.md` - template Architecture Mapping
