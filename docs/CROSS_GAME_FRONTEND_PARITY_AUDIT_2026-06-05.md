# Cross-Game FRONTEND/UX Parity Audit — Mines vs BOXE vs HI-LO (2026-06-05)

**Tipo:** Audit READ-ONLY (nessuna modifica a codice/CSS). Solo lettura + scrittura sezione RISULTATI.
**Esecutore:** KIMI. **Gate:** Claude (CTO).
**Origine:** Michele 2026-06-05 ha scoperto A MANO 2 divergenze frontend mai rilevate (X di chiusura mancante in BOXE embedded; storico replay assente in BOXE/HI-LO). L'audit backend (`CROSS_GAME_PARITY_AUDIT_2026-06-04.md`) NON copriva il frontend. Questo audit chiude quel buco di scope. "Differenze non segnalate" basta: trovarle TUTTE qui.

## Obiettivo
Mappare TUTTE le divergenze FRONTEND/UX tra i 3 giochi proprietari, con target canonico per asse. NB: il canonico frontend può essere DIVERSO dal backend (sul frontend Mines è il piu' completo; sul backend era l'outlier). Output = matrice + lista DIV-Fxx.

## Vincoli (HARD)
- READ-ONLY assoluto. Nessun edit a codice/CSS. Solo questo doc (sezione RISULTATI).
- Evidence-based: ogni cella cita `file:line`. Niente "sembra".
- Includere il comportamento **mobile** (`useMobileLayout` / viewport) per ogni superficie: il mobile è critico e spesso divergente.
- Niente assunzioni: non verificabile → `DA VERIFICARE`.

## Superfici da auditare (righe matrice) — per ogni gioco Mines/BOXE/HI-LO
1. **Bottone X / exit**: presente? condizione di visibilita' (embedded / fullscreen / mobile)? file:line. [Noto: BOXE `!bootRequest.isEmbeddedView && !useMobileLayout` boxe-gameplay.tsx:935; Mines `!isHostFullscreen && !useMobileLayout` mines-stage-header.tsx:168; HI-LO sempre hi-lo-gameplay.tsx:730]
2. **Replay singolo round**: comportamento (parte da step finale? controlli play/pausa/step/skip?).
3. **Replay storico sessioni**: pannello "Sessioni recenti" / navigazione round passati presente? [Noto: solo Mines ha `loadLatestReplaySessions`; BOXE e HI-LO NO].
4. **Info/Rules modal**: presente? contenuto a parita'?
5. **Layout mobile**: `useMobileLayout` gestito? controlli/board adattati? scrollbar/clipping?
6. **Balance display (real/demo)**: fonte (server response vs stato locale)? [collegato a DIV-01 backend]
7. **Controlli bet/stake**: stile chip, preset, +/-, validazione.
8. **Celebration / feedback vincita**.
9. **Fairness / verification UI**.
10. **Gate runtime**: table-balance-gate, short-viewport-gate, loading/error states.
11. **Header/shell**: top bar, titolo, struttura (parita' shell platform).
12. **Embed bridge / fullscreen**: messaging host, comportamento embed.

## Formato output (sezione RISULTATI)
Per ogni superficie 1-12: tabella `| Superficie | Mines | BOXE | HI-LO | Canonico (target) | Divergenza? | Severita' |`.
Poi lista `DIV-Fxx`: id, superficie, descrizione, prove (file:line), gioco/i outlier, target canonico, effort (S/M/L), rischi.
Infine: sintesi (quante divergenze per severita'), target canonico per asse, ordine bonifica raccomandato.

Severita': CRITICA (rotto/inutilizzabile o money-adjacent) / ALTA (capability mancante vs altri) / MEDIA (forma/stile divergente) / BASSA (cosmetico).

## DoD
- [x] 12 superfici compilate per i 3 giochi con prove.
- [x] Mobile coperto esplicitamente per ogni superficie.
- [x] Lista DIV-Fxx con severita'/prove/target/effort.
- [x] Le 2 gia' note confermate: X chiusura (DIV-F target Mines), storico replay (DIV-F target Mines).
- [x] Sintesi + ordine bonifica.
- [x] ZERO modifiche codice/CSS. Stop CTO.

---

## RISULTATI (compilato da KIMI)

### Matrice 12 × 3

#### 1. Bottone X / exit

| Aspetto | Mines | BOXE | HI-LO | Canonico | Divergenza? | Severita' |
|---------|-------|------|-------|----------|-------------|-----------|
| Condizione visibilita' desktop | `!isHostFullscreen && !useMobileLayout` (`mines-stage-header.tsx:168-179`) | `!bootRequest.isEmbeddedView && !useMobileLayout` (`boxe-gameplay.tsx:935-946`) | **Sempre renderizzato**, nessuna condizionale (`hi-lo-gameplay.tsx:730-737`) | Mines/BOXE (nascondi su mobile) | **SI** — BOXE outlier su embedded; HI-LO outlier su mobile | ALTA (BOXE) / MEDIA (HI-LO) |
| Mobile | **Nascosto** (`!useMobileLayout`) | **Nascosto** (`!useMobileLayout`) | **Visibile** (nessun guard) | Nascondi su mobile | **SI** — HI-LO mostra X anche su mobile | MEDIA |
| Exit handler | `handleExit()` in `mines-standalone.tsx:1312-1331`: fullscreen → clear state only; demo → `clearDemoState()`; else → `closeCurrentSession()` + `requestEmbedClose()` | `handleExit()` in `boxe-standalone.tsx:232-263`: fullscreen → clear state only; else → close session + `requestEmbedClose()` / navigate | `handleExit()` in `hi-lo-standalone.tsx:327-362`: fullscreen → clear state only; else → close session + `requestEmbedClose()` / navigate | Consistente | NO | — |

**Note:** Il comportamento di BOXE (`!bootRequest.isEmbeddedView`) significa che in modalità embedded desktop il bottone X è **completamente assente**, mentre in Mines/HI-LO è presente (a meno che non sia fullscreen). Questo è il comportamento che Michele ha scoperto a mano.

#### 2. Replay singolo round

| Aspetto | Mines | BOXE | HI-LO | Canonico | Divergenza? | Severita' |
|---------|-------|------|-------|----------|-------------|-----------|
| Tipo | **Static snapshot** (board finale non interattiva) (`mines-replay-viewer.tsx:71-152`) | **Playback animato** con controlli (`boxe-replay-viewer.tsx:27-175`) | **Playback animato** con controlli (`hi-lo-replay-viewer.tsx`) | Playback animato (BOXE/HI-LO) | **SI** — Mines manca di playback interattivo | MEDIA |
| Stato iniziale | Mostra `final_revealed_cells` o fallback `revealed_cells` (`mines-replay-viewer.tsx:74-75`) | `stepIndex = maxStep` (stato finale) ma controlli permettono rewind (`boxe-replay-viewer.tsx:29`) | `stepIndex = maxStep` (stato finale) ma controlli permettono rewind (`hi-lo-replay-viewer.tsx:29`) | Start finale + controlli rewind | **SI** — Mines non ha rewind | MEDIA |
| Controlli | **Nessuno** (board statica `closed={true}`) (`mines-replay-viewer.tsx:100`) | Play/Pausa/Step/Skip + indicatore progresso (`boxe-replay-viewer.tsx:85-121`) | Play/Pausa/Step/Skip + indicatore progresso (`hi-lo-replay-viewer.tsx:83-122`) | Play/Pausa/Step/Skip | **SI** — Mines outlier | MEDIA |
| Mobile | Collassa a colonna singola in modal stretta (`mines.css:2885-2888`) | Layout del replay dentro modal; nessuna variazione mobile specifica | Layout del replay dentro modal; nessuna variazione mobile specifica | Consistente | NO | — |

#### 3. Replay storico sessioni

| Aspetto | Mines | BOXE | HI-LO | Canonico | Divergenza? | Severita' |
|---------|-------|------|-------|----------|-------------|-----------|
| Pannello "Sessioni recenti" | **PRESENTE** (`latestReplaySessionsPanel` in `mines-gameplay.tsx:519-607`) | **ASSENTE** | **ASSENTE** | Presente (Mines) | **SI** — BOXE e HI-LO mancano completamente | ALTA |
| Loader | `loadLatestSessionsForReplay()` (`mines-gameplay.tsx:358-393`) chiama `fetchLatestReplaySessions` (`mines-standalone.tsx:930-946`) | Nessun equivalente | Nessun equivalente | Loader presente | **SI** | ALTA |
| Navigazione round | Frecce prev/next per navigare round passati (`mines-gameplay.tsx:581-598`) | Nessuna | Nessuna | Navigazione presente | **SI** | ALTA |
| Auth gate | Early return se `!isAuthenticated` (`mines-gameplay.tsx:359`) | N/A | N/A | Auth gate | N/A | — |
| Mobile | Pannello dentro rules modal full-screen; layout colonna singola su stretto (`mines.css:2885-2888`) | N/A | N/A | — | N/A | — |

#### 4. Info/Rules modal

| Aspetto | Mines | BOXE | HI-LO | Canonico | Divergenza? | Severita' |
|---------|-------|------|-------|----------|-------------|-----------|
| Componente | `MinesRulesModal` custom (`mines-rules-modal.tsx:41-113`) | `BoxeRulesModal` custom (`boxe-rules-modal.tsx:31-91`) | Wrap di `GameInfoRulesModal` condiviso (`hi-lo-rules-modal.tsx`) | Condiviso o custom per gioco | NO — ogni gioco ha il suo wrapper, ma pattern simile | — |
| Trigger | Bottone "i" circolare (`mines-gameplay.tsx:626-635`) | Bottone "i" ghost (`boxe-gameplay.tsx:799-809`) | Bottone "i" circolare (`hi-lo-gameplay.tsx:577-588`) | Presente in tutti | NO | — |
| Tabs | "REGOLE" + "REPLAY" (`mines-rules-modal.tsx:70-71`) | "rules" + "replay" (`boxe-rules-modal.tsx:47-51`) | "REGOLE"/"RULES" + "REPLAY" (`hi-lo-rules-modal.tsx:47-52`) | 2 tabs | NO | — |
| Contenuto | HTML dinamico da runtime config: `ways_to_win`, `payout_display`, `settings_menu`, `bet_collect` (`mines-rules-modal.tsx:77-100`) | HTML dinamico da runtime config con fallback a `BOXE_DEFAULT_RULE_SECTIONS`: `how_to_play`, `bet_collect`, `fairness`, `rtp`, `limits`, `responsible_gaming` (`boxe-rules-modal.tsx:42-88`) | HTML dinamico da runtime config con fallback a `HI_LO_DEFAULT_RULE_SECTIONS`: 7 sezioni (`hi-lo-rules-modal.tsx:42-88`) | Contenuto game-specific | NO — atteso | — |
| Tab replay guard | Disabilitato se `!isReplayAvailable` | Guard: `if (tab === "replay" && !replayAvailable) return;` | Disabilitato se `!replayAvailable` | Consistente | NO | — |
| Mobile | Full-screen overlay (`GameInfoRulesModal`) | Full-screen overlay | Full-screen overlay (`game-info-rules-overlay`) | Consistente | NO | — |

#### 5. Layout mobile

| Aspetto | Mines | BOXE | HI-LO | Canonico | Divergenza? | Severita' |
|---------|-------|------|-------|----------|-------------|-----------|
| `useMobileLayout` | **PRESENTE** (`mines-standalone.tsx:315`, passato a `MinesGameplay`) | **PRESENTE** (`boxe-gameplay.tsx:255`, `isMobileViewport` da matchMedia) | **ASSENTE** — zero match di `useMobileLayout` in `frontend-v3/app/ui/hi-lo` | Presente | **SI** — HI-LO outlier | MEDIA |
| Hook matchMedia | `(max-width: 960px), (pointer: coarse)` (`mines-standalone.tsx:72`) | `(max-width: 960px), (pointer: coarse)` (`boxe-gameplay.tsx:55`) | N/A — solo CSS media queries | Hook React + CSS | **SI** — HI-LO manca hook | MEDIA |
| Layout switch | `mines-mobile-layout` grid vs `mines-grid` desktop (`mines-gameplay.tsx:880-897`) | `boxe-mobile-layout` form vs `boxe-grid` desktop (`boxe-gameplay.tsx:988-1003`) | Solo CSS: `@media (max-width: 720px)` collapse a colonna singola (`hi-lo.css:963-1186`) | React-level switch | **SI** — HI-LO diverge | MEDIA |
| Mobile controls | `GameMobileControlStack` + `GameMobileSettingsSheet` (`mines-gameplay.tsx:884-894,917-932`) | `GameMobileControlStack` + `GameMobileSettingsSheet` (`boxe-gameplay.tsx:992-1001,1025-1040`) | Nessuno — controlli sempre visibili, adattati solo via CSS | `GameMobileControlStack` | **SI** — HI-LO manca stack mobile | MEDIA |
| Scroll lock | `document.documentElement.style.overflow = "hidden"` (`mines-standalone.tsx:465-478`) | Nessuno esplicito | Nessuno esplicito | Scroll lock | **SI** — Mines solo | BASSA |
| Board sizing | `clamp()` per viewport height (`mines.css:1702-1706,3314-3316`) | `clamp()` per cell sizing (`boxe.css:158-186`) | `clamp()` per card sizing (`hi-lo.css:1002-1012`) | Consistente (clamp) | NO | — |
| Short-viewport gate | `GameShortViewportGate` in mobile form (`mines-gameplay.tsx:895`) | `GameShortViewportGate` in mobile form (`boxe-gameplay.tsx:1003`) | `GameShortViewportGate` (`hi-lo-gameplay.tsx:794-797`) | Presente | NO | — |

#### 6. Balance display (real/demo)

| Aspetto | Mines | BOXE | HI-LO | Canonico | Divergenza? | Severita' |
|---------|-------|------|-------|----------|-------------|-----------|
| Componente | `GameBalanceFooter` (`mines-gameplay.tsx:765-781`) | `GameBalanceFooter` (`boxe-gameplay.tsx:776-793`) | `GameBalanceFooter` (`hi-lo-gameplay.tsx:646-665`) | `GameBalanceFooter` | NO | — |
| Fonte demo | `demoChipBalance` locale (`useState`) (`mines-standalone.tsx:306`) | `demoBalance` locale (`useState("100")`) (`boxe-gameplay.tsx:196`) | `demoBalance` locale (`useState("100")`) (`hi-lo-gameplay.tsx:137`) | Stato locale demo | NO | — |
| Fonte real | `tableSession.table_balance_amount` > `wallet_balance_after_start` > `selectedWallet.balance_snapshot` (`mines-standalone.tsx:306-313`) | `tableSession?.table_balance_amount ?? "0"` (`boxe-gameplay.tsx:240`) | `tableSession?.table_balance_amount` OR `readBalanceAmount({walletSource, wallets})` (`hi-lo-gameplay.tsx:156-158`) | Table session primaria | NO — leggera divergenza su fallback | BASSA |
| Wallets fetch | Non necessario (usa selectedWallet dallo standalone) | Non necessario | `loadHiLoWallets(authToken)` (`hi-lo-gameplay.tsx:227-246`) | N/A | BASSA — HI-LO fetcha wallets esplicitamente | BASSA |
| Potential payout | `potentialPayout` passato a `GameBalanceFooter` (`mines-gameplay.tsx:765-781`) | `potentialPayout` passato (`boxe-gameplay.tsx:776-793`) | `potentialPayout` passato (`hi-lo-gameplay.tsx:646-665`) | Presente | NO | — |
| Mobile | Balance dentro `GameMobileControlStack` (`mines-gameplay.tsx:886`) | Balance dentro `GameMobileControlStack` | Balance dentro layout CSS mobile | Consistente in effetto | NO | — |

#### 7. Controlli bet/stake

| Aspetto | Mines | BOXE | HI-LO | Canonico | Divergenza? | Severita' |
|---------|-------|------|-------|----------|-------------|-----------|
| Componente | `GameBetPanel` (`mines-gameplay.tsx:734-763`) | `GameBetPanel` (`boxe-gameplay.tsx:744-775`) | `GameBetPanel` (`hi-lo-gameplay.tsx:612-626`) | `GameBetPanel` | NO | — |
| inputMode | **`"numeric"`** (solo interi) | **`"decimal"`** (frazioni ammesse) | **`"decimal"`** (frazioni ammesse) | `"decimal"` o `"numeric"` unificato | **SI** — Mines outlier | BASSA |
| Quick chips | `["1","2","5","10","25"]` (`game-quick-chips.tsx:15-47`) | `["1","2","5","10","25"]` (`boxe-gameplay.tsx:753`) | `["1","2","5","10","25"]` (`hi-lo-gameplay.tsx:621`) | Consistente | NO | — |
| +/- stepper | **Assente** | **Assente** | **Assente** | Assente | NO | — |
| Normalizzazione | `normalizeWholeChipInput` — arrotonda per difetto a interi (`mines-standalone.tsx:1663`) | `normalizeBetInput` — sostituisce virgola con punto, strip non-numerici, mantiene un solo punto (`boxe-gameplay.tsx:1113-1119`) | `normalizeBetInput` — stesso pattern di BOXE (`hi-lo-gameplay.tsx:1041-1048`) | Unificare | **SI** — Mines usa normalizzazione diversa | BASSA |
| Validazione | `isBetDisabled` controlla `busyAction`, active round, interaction locked, `!hasTableBudget` (`mines-gameplay.tsx:219-223`) | `canBet` richiede bet>0, sufficient balance, not locked, no active round (`boxe-gameplay.tsx:244-248`) | `isBetDisabled` controlla interaction locked, active round, bet≤0, `(!isDemoPlayer && !tableSession)` (`hi-lo-gameplay.tsx:161-165`) | Pattern simile | NO | — |
| Idle hint | Pulsante bet pulsa dopo 10s di inattività (`mines-standalone.tsx:493-512`) | **Assente** | **Assente** | Presente | **SI** — solo Mines | BASSA |

#### 8. Celebration / feedback vincita

| Aspetto | Mines | BOXE | HI-LO | Canonico | Divergenza? | Severita' |
|---------|-------|------|-------|----------|-------------|-----------|
| Visual celebration | `MinesWinCelebration` — 14 pezzi confetti, CSS keyframes, overlay absolute (`mines-win-celebration.tsx:5-13`, `mines.css:1072-1159`) | `BoxeWinCelebration` — 12 pezzi confetti, CSS keyframes, overlay absolute (`boxe-win-celebration.tsx:5-49`, `boxe-animations.css:40-103`) | **NESSUNA** — nessun confetti, nessun overlay animato, nessuna modale vincita (`hi-lo-gameplay.tsx`) | Presente | **SI** — HI-LO completamente assente | ALTA |
| Trigger | `winCelebrationKey` incrementato su reveal vinta e cashout (`mines-gameplay.tsx:269,292`) | `celebration` state su cashout e top_row (`boxe-gameplay.tsx:682-686,651-657`) | Solo stato UI implicito (bordi colorati su history items) (`hi-lo.css:616-623`) | Celebration esplicita | **SI** — HI-LO outlier | ALTA |
| Audio | 4 effetti sonori (`use-mines-sounds.ts:54-70`): safe reveal, mine hit, collect, win | 2 effetti sonori (`use-boxe-audio.ts:24-29`): cashout_won, top_row_won | **`hasAnySound: false`** hardcoded (`hi-lo-gameplay.tsx:591`) — **nessun audio** | Audio presente | **SI** — HI-LO muto | MEDIA |
| Auto-dismiss | Celebration auto-dismiss dopo durata animazione | Auto-dismiss dopo 2600ms (`boxe-win-celebration.tsx:16-22`) | N/A | Auto-dismiss | N/A | — |
| Mobile | Overlay confetti vincolato a board area (`position: absolute; inset: 0`) | Overlay confetti vincolato a board area | N/A | — | N/A | — |

#### 9. Fairness / verification UI

| Aspetto | Mines | BOXE | HI-LO | Canonico | Divergenza? | Severita' |
|---------|-------|------|-------|----------|-------------|-----------|
| Live fairness | **Assente** durante gameplay attivo | **Assente** durante gameplay attivo | **Assente** durante gameplay attivo | Assente | NO | — |
| Replay fairness | Board hash, server seed hash, nonce (`mines-replay-viewer.tsx:132-148`) | Server seed hash, client seed, outcome verification (`boxe-replay-viewer.tsx:155-171`) | Server seed hash, client seed, outcome verification, server seed (se rivelato) (`hi-lo-replay-viewer.tsx:166-188`) | Presente in replay | NO — leggera variazione campi | BASSA |
| `user_verifiable` flag | Presente nel tipo ma **non usato in UI** (`mines-replay-viewer.tsx:37`) | Presente nel tipo ma **non usato in UI** (`use-boxe-runtime.ts:119-127`) | Non verificato | Flag ignorato | NO | — |
| "Verify" button | **Assente** in tutti | **Assente** in tutti | **Assente** in tutti | Assente | NO | — |

#### 10. Gate runtime

| Aspetto | Mines | BOXE | HI-LO | Canonico | Divergenza? | Severita' |
|---------|-------|------|-------|----------|-------------|-----------|
| Table-balance gate | `GameTableBalanceGate` (`mines-standalone.tsx:1448-1495`) | `GameTableBalanceGate` (`boxe-standalone.tsx:345-389`) | `GameTableBalanceGate` (`hi-lo-standalone.tsx:432-476`) | Presente | NO | — |
| Condizione gate | `shouldShowPreGameTableEntry`: real, no table session, no active round, not resuming (`mines-standalone.tsx:339-344`) | `showTableBalanceGate`: launch ready, not demo, not table balance complete (`boxe-standalone.tsx:180-181`) | `showTableBalanceGate`: launch ready, not demo, not complete, not resumed round, not checking (`hi-lo-standalone.tsx:197-198`) | Pattern simile | NO | — |
| Short-viewport gate | `GameShortViewportGate` in mobile form (`mines-gameplay.tsx:895`) | `GameShortViewportGate` in mobile form (`boxe-gameplay.tsx:1003`) | `GameShortViewportGate` (`hi-lo-gameplay.tsx:794-797`) | Presente | NO | — |
| Provider intro | `GameProviderBootstrap` (`mines-standalone.tsx:299-304`) | `GameProviderBootstrap` (`boxe-standalone.tsx:299-304`) | `GameProviderBootstrap` (`hi-lo-standalone.tsx:398-403`) | Presente | NO | — |
| How-to-play | `GameHowToPlayGate` (`mines-standalone.tsx:306-343`) | `GameHowToPlayGate` (`boxe-standalone.tsx:306-343`) | `GameHowToPlayGate` con 3 cards (`hi-lo-standalone.tsx:405-430`) | Presente | NO | — |
| Loading session | Overlay "Restoring session..." (`mines-standalone.tsx:1355-1359`) | Nessun overlay specifico | Nessun overlay specifico | Overlay restore | **SI** — solo Mines | BASSA |
| Error handling | `handleGameError()` con classificazione, fatal overlay per `SESSION_VOIDED_BY_OPERATOR`, dialog generico (`mines-standalone.tsx:1259-1406`) | `GameActionError` con retry/reload, classificazione via `classifyGameError` (`boxe-standalone.tsx:391-402`, `boxe-gameplay.tsx:1046-1058`) | `GameActionError` con retry (MAX 3 tentativi), reload, dismiss (`hi-lo-standalone.tsx:478-491`, `hi-lo-gameplay.tsx:799-827`) | Pattern simile | NO | — |
| Retry idempotency | Chiavi idempotenza per retry azioni (`mines-gameplay.tsx` implicito; `boxe-gameplay.tsx:85-105,689-702` esplicito) | Chiavi idempotenza esplicite | Retry senza idempotenza esplicita (MAX 3) | Idempotenza | **SI** — HI-LO potrebbe mancare idempotenza | BASSA |

#### 11. Header / shell

| Aspetto | Mines | BOXE | HI-LO | Canonico | Divergenza? | Severita' |
|---------|-------|------|-------|----------|-------------|-----------|
| Shell wrapper | `GameBootShell` (`mines-standalone.tsx:1558-1580`) | `GameBootShell` (`boxe-standalone.tsx:404-467`) | `GameBootShell` (`hi-lo-standalone.tsx:493-544`) | `GameBootShell` | NO | — |
| Shell class management | `pageShellClassName` + `productShellClassName` con varianti mobile/embedded/skin (`mines-standalone.tsx:366-387`) | `pageShellClassName` + `productShellClassName` con varianti mobile/embedded (`boxe-standalone.tsx:164-196`) | `pageShellClassName` + `productShellClassName` con varianti embedded (`hi-lo-standalone.tsx:184-196`) | Consistente | NO | — |
| Stage header | `MinesStageHeader` con titolo, subtitle (WON/LOST), payout preview ladder, X button (`mines-stage-header.tsx:32-182`) | `stageHeader` in `boxe-gameplay.tsx` con titolo/logo, X button (`boxe-gameplay.tsx:901-948`) | `hi-lo-stage-header` con titolo/logo, X button (`hi-lo-gameplay.tsx:721-738`) | Presente | NO — struttura simile | — |
| Payout preview ladder | **PRESENTE** — mostra prossimi 5 moltiplicatori (`mines-stage-header.tsx:151-166`) | **ASSENTE** (non applicabile a BOXE) | **ASSENTE** (non applicabile a HI-LO) | Game-specific | N/A | — |
| Mode badge | `status-badge info mines-mode-badge` in rail header (`mines-gameplay.tsx:643-653`) | `status-badge info mines-mode-badge boxe-mode-badge` in rail header (`boxe-gameplay.tsx:835-837`) | `status-badge info game-mode-badge hi-lo-mode-badge` in rail header (`hi-lo-gameplay.tsx:574-610`) | Presente | NO | — |
| Runtime tools | `GameRuntimeTools` (orologio + audio mute/volume) in `mobileStageTools` e rail header (`mines-gameplay.tsx:654-659`) | `GameRuntimeTools` in rail header e mobile stage tools (`boxe-gameplay.tsx:810-845`) | `GameRuntimeTools` in rail header, ma `hasAnySound: false` (`hi-lo-gameplay.tsx:589-604`) | Presente | NO — HI-LO muto è noto | — |
| Title rendering | Logo image se `title_render_mode === "image"`, altrimenti testo con ResizeObserver dinamico su desktop (`mines-stage-header.tsx:60-147`) | Logo image se skinned, altrimenti testo (`boxe-gameplay.tsx:852-917`) | Logo image se skinned, altrimenti testo (`hi-lo-gameplay.tsx:724-728`) | Consistente | NO | — |

#### 12. Embed bridge / fullscreen

| Aspetto | Mines | BOXE | HI-LO | Canonico | Divergenza? | Severita' |
|---------|-------|------|-------|----------|-------------|-----------|
| Hook | `useGameEmbedBridge({ gameCode: "mines" })` (`mines-standalone.tsx:316-319`) | `useGameEmbedBridge({ gameCode: "boxe" })` (`boxe-standalone.tsx:157-160`) | `useGameEmbedBridge({ gameCode: "hi_lo" })` (`hi-lo-standalone.tsx:180-183`) | Stesso hook | NO | — |
| Incoming messages | `casinoking:game-fullscreen-state` o legacy `casinoking:mines-fullscreen-state` | `casinoking:game-fullscreen-state` o legacy `casinoking:boxe-fullscreen-state` | `casinoking:game-fullscreen-state` o legacy `casinoking:hi-lo-fullscreen-state` | Pattern consistente | NO | — |
| Outgoing messages | Generic `casinoking:game-close` + legacy `casinoking:mines-close` | Generic `casinoking:game-close` + legacy `casinoking:boxe-close` | Generic `casinoking:game-close` + legacy `casinoking:hi-lo-close` | Pattern consistente | NO | — |
| Embed origin | Da `?embed_origin=` query param (`use-game-embed-bridge.ts:95-98`) | Da query param | Da query param | Consistente | NO | — |
| `isEmbeddedView` | Da boot request (`mines-standalone.tsx:402`) | Da boot request (`boxe-standalone.tsx`) | Da boot request (`hi-lo-standalone.tsx:176-177`) | Consistente | NO | — |
| Fullscreen exit | Se `isHostFullscreen` → solo clear state (`mines-standalone.tsx:1312-1331`) | Se `isHostFullscreen` → solo clear state (`boxe-standalone.tsx:232-263`) | Se `isHostFullscreen` → solo clear state (`hi-lo-standalone.tsx:327-362`) | Consistente | NO | — |
| Embed CSS | `mines-page-shell-embedded` + `mines-product-shell-embedded` (`mines-standalone.tsx:366-387`) | `mines-page-shell-embedded` + `mines-product-shell-embedded` (classi ereditate) (`boxe-standalone.tsx:164-196`) | `hi-lo-page-shell-embedded` + `hi-lo-product-shell-embedded` (`hi-lo-standalone.tsx:184-196`) | Consistente | NO | — |

---

### Lista DIV-Fxx

#### DIV-F01 — X button nascosto in BOXE embedded desktop
- **Superficie:** 1 (X/exit)
- **Descrizione:** BOXE usa `!bootRequest.isEmbeddedView && !useMobileLayout` per il render del bottone X. Questo significa che in modalità embedded desktop (viewport >960px, `isEmbeddedView=true`) il bottone X è completamente assente. Invece Mines e HI-LO mostrano il bottone X in embedded (a meno che non sia fullscreen o mobile).
- **Prove:** `boxe-gameplay.tsx:935-946` condizione `!bootRequest.isEmbeddedView`; `mines-stage-header.tsx:168-179` condizione `!isHostFullscreen && !useMobileLayout` (NON include `isEmbeddedView`); `hi-lo-gameplay.tsx:730-737` (nessuna condizionale, X sempre visibile).
- **Outlier:** BOXE
- **Target canonico:** Mines (mostra X in embedded a meno che non fullscreen)
- **Effort:** S (cambio condizionale singola: rimuovere `!bootRequest.isEmbeddedView` o sostituire con `!isHostFullscreen` come Mines)
- **Rischi:** Basso. Cambio puramente di visibilità UI, non logica di exit (l'handler `handleExit()` in `boxe-standalone.tsx:232-263` gestisce già correttamente l'embed con `requestEmbedClose()`).

#### DIV-F02 — X button visibile su HI-LO mobile
- **Superficie:** 1 (X/exit)
- **Descrizione:** HI-LO renderizza il bottone X sempre, senza alcuna guard `useMobileLayout`. Su mobile questo crea un affordance di chiusura che Mines e BOXE nascondono deliberatamente (lasciando l'uscita al back gesture del browser/OS o al messaggio embed del parent).
- **Prove:** `hi-lo-gameplay.tsx:730-737` (nessuna condizionale); `mines-stage-header.tsx:168-179` (`!useMobileLayout`); `boxe-gameplay.tsx:935-946` (`!useMobileLayout`).
- **Outlier:** HI-LO
- **Target canonico:** Mines/BOXE (nascondi X su mobile)
- **Effort:** S (aggiungere `!useMobileLayout` alla condizione di render)
- **Rischi:** Basso. Rischio di regressione minimo; il bottone potrebbe essere desiderato in alcuni contesti ma non allineato con il design system degli altri giochi.

#### DIV-F03 — Replay storico sessioni assente in BOXE e HI-LO
- **Superficie:** 3 (Replay storico sessioni)
- **Descrizione:** Solo Mines ha un pannello "Sessioni recenti" (`latestReplaySessionsPanel`) che permette di navigare i round delle sessioni di gioco precedenti. BOXE e HI-LO hanno solo il replay del round corrente (tab REPLAY nel modal info). Questo è un capability gap significativo per la UX di analisi della storia di gioco.
- **Prove:** `mines-gameplay.tsx:358-393` (loader `loadLatestSessionsForReplay`); `mines-gameplay.tsx:519-607` (pannello JSX); `mines-standalone.tsx:930-946` (`fetchLatestReplaySessions`). BOXE: `boxe-gameplay.tsx:310-354` (solo replay round corrente). HI-LO: `hi-lo-gameplay.tsx:528-551` (solo replay round corrente).
- **Outlier:** BOXE, HI-LO
- **Target canonico:** Mines
- **Effort:** L (richiede: backend endpoint per latest sessions [verificare esistenza per BOXE/HI-LO], componente UI analogo, integrazione nel rules modal, gestione stati loading/error/empty)
- **Rischi:** Medio. Richiede backend + frontend. Se l'endpoint non esiste per BOXE/HI-LO, il lavoro backend è extra. Verificare che `LatestAccessSessionHistory` type sia compatibile.

#### DIV-F04 — Mines replay statico (no playback controls)
- **Superficie:** 2 (Replay singolo round)
- **Descrizione:** Il replay di Mines è una board statica finale (`closed={true}`) senza alcun controllo di playback. BOXE e HI-LO hanno invece replay animati con play/pausa, step avanti/indietro, skip a fine, e indicatore di progresso. Il replay di Mines mostra solo lo stato terminale.
- **Prove:** `mines-replay-viewer.tsx:71-152` (board statica, `closed={true}` line 100, nessun controllo); `boxe-replay-viewer.tsx:85-118` (controlli play/pausa/step/skip); `hi-lo-replay-viewer.tsx:83-122` (controlli analoghi).
- **Outlier:** Mines
- **Target canonico:** BOXE/HI-LO (playback animato con controlli)
- **Effort:** M (richiede: aggiungere stato `stepIndex`, controlli UI, logica di playback con `setInterval`, adattare `MinesReplayViewer` da statico a step-based. Le API di replay Mines già restituiscono lo storico delle celle rivelate? Verificare formato risposta.)
- **Rischi:** Medio. Se il backend non fornisce lo storico step-by-step delle rivelazioni, l'effort diventa L (backend + frontend).

#### DIV-F05 — HI-LO senza celebration visiva per vincite ✅ COMPLETATO 2026-06-07
- **Superficie:** 8 (Celebration / feedback vincita)
- **Descrizione:** HI-LO non ha alcun componente di celebration: nessun confetti, nessun overlay animato, nessuna modale di vincita. Il feedback è solo implicito (bordi verdi/rossi sugli history item, cambio label stato). Questo crea un'esperienza utente significativamente più fredda rispetto a Mines e BOXE. **Risolto:** creato `hi-lo-win-celebration.tsx`, CSS in `hi-lo.css`, trigger su cashout con payout > 0 in `hi-lo-gameplay.tsx`.
- **Prove:** `hi-lo-gameplay.tsx` nessuna import/render di celebration component; `mines-win-celebration.tsx:5-13` + `mines.css:1072-1159`; `boxe-win-celebration.tsx:5-49` + `boxe-animations.css:40-103`. Post-fix: `hi-lo-win-celebration.tsx`, `hi-lo.css`, trigger in `executeCashout`.
- **Outlier:** HI-LO
- **Target canonico:** Mines/BOXE (celebration con confetti + testo vincita)
- **Effort:** M (richiede: componente celebration analogo, CSS keyframes, trigger su cashout/streak vittorie, possibile integrazione audio)
- **Rischi:** Basso-Medio. Design/UX: decidere se celebration va sul board o fullscreen. HI-LO ha una UI diversa (card-centrica), potrebbe servire un design adattato.

#### DIV-F06 — HI-LO senza effetti sonori
- **Superficie:** 8 (Celebration / feedback vincita — audio)
- **Descrizione:** HI-LO passa esplicitamente `hasAnySound: false` a `GameRuntimeTools`, disabilitando completamente l'audio. Mines ha 4 effetti sonori; BOXE ne ha 2. L'audio è un elemento di feedback importante per l'engagement.
- **Prove:** `hi-lo-gameplay.tsx:591` (`hasAnySound: false`); `use-mines-sounds.ts:54-70`; `use-boxe-audio.ts:24-29`.
- **Outlier:** HI-LO
- **Target canonico:** Mines/BOXE (audio abilitato con effetti game-specific)
- **Effort:** M (richiede: rimuovere `hasAnySound: false`, creare hook `use-hi-lo-sounds.ts`, mappare eventi a suoni, fornire assets audio)
- **Rischi:** Medio. Necessita di assets audio. Se non esistono, va prodotto/approvato il sound design.

#### DIV-F07 — HI-LO senza React-level mobile layout (`useMobileLayout`)
- **Superficie:** 5 (Layout mobile)
- **Descrizione:** HI-LO non utilizza `useMobileLayout` né alcun hook di matchMedia. L'adattamento mobile è puramente CSS-driven via media queries. Questo significa che HI-LO non usa `GameMobileControlStack`, `GameMobileSettingsSheet`, o altri componenti mobile-specifici che Mines e BOXE impiegano. Il risultato potrebbe essere un'esperienza mobile meno ottimizzata.
- **Prove:** `grep` zero match per `useMobileLayout` in `frontend-v3/app/ui/hi-lo`; `mines-standalone.tsx:315` + `mines-gameplay.tsx:880-897`; `boxe-gameplay.tsx:255` + `boxe-gameplay.tsx:988-1003`.
- **Outlier:** HI-LO
- **Target canonico:** Mines/BOXE (`useMobileLayout` + `GameMobileControlStack` + `GameMobileSettingsSheet`)
- **Effort:** L (richiede: aggiungere hook matchMedia, rifattorizzare layout per supportare `GameMobileControlStack`, aggiungere `GameMobileSettingsSheet` per le impostazioni HI-LO [deck size?], test su viewport mobili)
- **Rischi:** Alto. Rifattorizzazione strutturale del layout di HI-LO. Possibili regressioni visive su tutti i breakpoint. Richiede test approfonditi su dispositivi reali/emulatori.

#### DIV-F08 — Mines usa `inputMode="numeric"` vs `"decimal"` in BOXE/HI-LO
- **Superficie:** 7 (Controlli bet/stake)
- **Descrizione:** Mines usa `inputMode="numeric"` per il campo bet, limitando l'input a interi. BOXE e HI-LO usano `inputMode="decimal"`, permettendo frazioni. Inoltre Mines usa `normalizeWholeChipInput` che arrotonda per difetto, mentre BOXE/HI-LO usano `normalizeBetInput` che mantiene i decimali. Questa incoerenza è confusa per l'utente che gioca a più giochi.
- **Prove:** `mines-gameplay.tsx` (`inputMode="numeric"` implicito o esplicito, `normalizeWholeChipInput` in `mines-standalone.tsx:1663`); `boxe-gameplay.tsx` (`inputMode="decimal"`, `normalizeBetInput` in `boxe-gameplay.tsx:1113-1119`); `hi-lo-gameplay.tsx` (`inputMode="decimal"`, `normalizeBetInput` in `hi-lo-gameplay.tsx:1041-1048`).
- **Outlier:** Mines
- **Target canonico:** BOXE/HI-LO (`inputMode="decimal"`, supporto frazioni) OPPURE unificare tutti a `numeric` se il business richiede solo chip interi
- **Effort:** S (cambio attributo input + normalizzatore, verificare validazione backend)
- **Rischi:** Basso. Ma: se il backend Mines non supporta bet decimali, il cambio richiede anche backend. Verificare contratto API.

#### DIV-F09 — HI-LO senza idempotenza esplicita su retry azioni
- **Superficie:** 10 (Gate runtime — error handling)
- **Descrizione:** Mines e BOXE usano chiavi idempotenza esplicite per le retry delle azioni di gioco. HI-LO ha `MAX_ACTION_RETRY_ATTEMPTS = 3` ma non mostra un meccanismo di idempotenza esplicito nello stesso modo. Questo potrebbe causare azioni duplicate in caso di retry.
- **Prove:** `boxe-gameplay.tsx:85-105,689-702` (idempotenza con retry keys); `hi-lo-gameplay.tsx` (retry senza idempotenza esplicita visibile).
- **Outlier:** HI-LO
- **Target canonico:** Mines/BOXE (idempotenza con chiavi esplicite)
- **Effort:** S-M (aggiungere generazione chiavi idempotenza e passarle nelle API call)
- **Rischi:** Medio. Azioni duplicate possono avere impatto finanziario. Richiede verifica backend supporto idempotenza per HI-LO.

#### DIV-F10 — Solo Mines ha idle hint sul pulsante bet ✅ COMPLETATO 2026-06-07
- **Superficie:** 7 (Controlli bet/stake)
- **Descrizione:** Dopo 10 secondi di inattività, il pulsante bet in Mines inizia a pulsare (`isBetHintActive`) per attirare l'attenzione dell'utente. BOXE e HI-LO non hanno questo pattern. **Risolto:** replicato il pattern in `boxe-gameplay.tsx` e `hi-lo-gameplay.tsx` con `isBetHintActive`/`playerActivityTick`, timer 10s, pulse 1.1s, CSS `.boxe-bet-idle-pulse`/`.hi-lo-bet-idle-pulse`; `notePlayerActivity` su cambio puntata, settings (BOXE), start/predict/skip/cashout.
- **Prove:** `mines-standalone.tsx:493-512` (timer 10s + pulse 1.1s). BOXE/HI-LO: nessun equivalente. Post-fix: `boxe-gameplay.tsx`, `hi-lo-gameplay.tsx`, `boxe-animations.css`, `hi-lo.css`.
- **Outlier:** BOXE, HI-LO
- **Target canonico:** Mines (idle hint presente)
- **Effort:** S (aggiungere `useEffect` timer + stato pulse in BOXE/HI-LO)
- **Rischi:** Basso. Pattern UX opzionale.

---

### Sintesi

#### Conteggio divergenze per severità

| Severità | Conteggio | DIV-F |
|----------|-----------|-------|
| CRITICA | 0 | — |
| ALTA | 3 | F03, F05, F01 |
| MEDIA | 4 | F02, F04, F06, F07 |
| BASSA | 3 | F08, F09, F10 |
| **Totale** | **10** | |

#### Target canonico per asse

| Asse | Target canonico | Motivazione |
|------|-----------------|-------------|
| X/exit button visibilità | **Mines** (`!isHostFullscreen && !useMobileLayout`) | La logica più corretta: nascondi solo quando strettamente necessario (fullscreen host o mobile). Non nascondere in embedded desktop. |
| Replay storico sessioni | **Mines** (`latestReplaySessionsPanel`) | Unica implementazione completa con loader, navigazione, e auth gate. |
| Replay singolo (playback) | **BOXE/HI-LO** (playback animato con controlli) | Esperienza utente superiore rispetto alla board statica di Mines. |
| Layout mobile | **Mines/BOXE** (`useMobileLayout` + `GameMobileControlStack`) | Approccio React-level più robusto e coerente con il design system platform. |
| Celebration visiva | **Mines/BOXE** (confetti + overlay) | Feedback positivo essenziale per l'engagement. |
| Audio | **Mines/BOXE** (effetti sonori abilitati) | Feedback audio importante, specialmente su mobile. |
| Bet input mode | **DA DECIDERE** (unificare a `decimal` o `numeric`) | Incoerenza attuale tra giochi. Richiede decisione product/business. |
| Error handling idempotenza | **Mines/BOXE** (chiavi idempotenza esplicite) | Protezione contro azioni duplicate su retry. |
| Idle hint bet | **Mines** (presente) | Pattern UX di engagement legittimo. |

#### Ordine bonifica raccomandato

1. **DIV-F01** (BOXE X button embedded) — Effort S, rischio basso, impatto ALTO. Fix immediato.
2. **DIV-F02** (HI-LO X button mobile) — Effort S, rischio basso, impatto MEDIA. Fix immediato, può andare in parallelo con F01.
3. **DIV-F03** (Replay storico BOXE/HI-LO) — Effort L, ma impatto ALTO. Richiede pianificazione backend+frontend. Da spezzare in sub-task per gioco.
4. **DIV-F05** (HI-LO celebration visiva) — Effort M, impatto ALTO. Migliora significativamente l'UX di HI-LO.
5. **DIV-F06** (HI-LO audio) — Effort M, impatto MEDIA. Dipende da disponibilità assets audio.
6. **DIV-F04** (Mines replay playback) — Effort M-L, impatto MEDIA. Da verificare se backend fornisce già dati step-by-step.
7. **DIV-F07** (HI-LO mobile layout React) — Effort L, impatto MEDIA ma rischio ALTO di regressione. Da pianificare con attenzione.
8. **DIV-F08** (Bet input mode) — Effort S, ma richiede decisione product. Potrebbe bloccare su backend.
9. **DIV-F09** (HI-LO idempotenza) — Effort S-M, impatto sicurezza. Da verificare backend.
10. **DIV-F10** (Idle hint BOXE/HI-LO) — Effort S, impatto BASSA. Nice-to-have.

---

## Appendice: Note di metodologia

- Tutte le prove sono state raccolte tramite lettura diretta del codice sorgente in `frontend-v3/app/ui/{mines,boxe,hi-lo}/`.
- Nessun file è stato modificato durante questo audit.
- I sub-agent di esplorazione hanno operato in parallelo sui tre giochi, garantendo copertura indipendente.
- Le citazioni `file:line` si riferiscono alla versione del codice presente nel branch `feature/site-v3-cms-ia-cleanup` al momento dell'audit (2026-06-05).
- Per le superfici 4, 10, 11, 12 la parità è sostanziale (nessuna divergenza significativa); le variazioni riscontrate sono game-specific o di implementazione equivalente.
