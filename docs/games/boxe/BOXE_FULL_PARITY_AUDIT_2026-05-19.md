Status: ACTIVE
Last meaningful update: 2026-05-19

# BOXE - Full Parity Audit - 2026-05-19

## 1. Methodology

Questo audit e' stato eseguito sulla branch
`audit/boxe-full-parity-2026-05-19` come WP read-only. Nessun file di codice e'
stato modificato. Le uniche modifiche versionate di questo WP sono questo
documento e l'indice documentale.

Fonti effettivamente aperte o ispezionate:

- Mockup BOXE: `assets/Games/boxe/boxe1 splash.png`,
  `boxe2 stato idle base .png`, `boxe4.png`, `boxe5.png`, `boxe6.png`,
  `boxe7.png`.
- Documento funzionale: `assets/Games/boxe/BOXE - DOCUMENTO DI DESIGN FUNZIONALE.docx`.
- Mines reference: `frontend/app/ui/mines/`, piu' baseline
  `tests/visual/baselines/mines_classic/*`.
- BOXE current: `frontend/app/ui/boxe/`,
  `frontend/app/ui/boxe-backoffice/`, piu' baseline
  `tests/visual/baselines/boxe_3c/*`.
- Shared runtime e shell admin: `frontend/app/ui/game-runtime/`,
  `frontend/app/ui/title-editor/`.
- Baseline pre-game shared: `tests/visual/baselines/boot_2a/*`.
- Memorie CTO in `~/.claude/projects/.../memory/` su visual uniformity,
  post-closure distillation, approach validation pattern e bug visuali BOXE.
- Localhost side-by-side su `http://localhost:3000` con browser Playwright:
  provider intro, how-to, gameplay desktop, gameplay mobile, landscape-short,
  table gate real/bonus, admin Mines/BOXE title editor.

Nota operativa: l'admin Mines master e' locked e non espone l'editor completo.
Per osservare la struttura reale tabs Mines e' stata creata una variante locale
solo per audit, `mines_audit_20260519`, tramite endpoint admin gia' esistente.
Gli screenshot sono in `var/tmp/boxe-full-parity-audit/`, directory ignorata da
git. Non fanno parte del commit.

Limitazioni:

- Screenshot localhost, non production. Tema, catalogo e dati dipendono dal DB
  locale.
- L'audit e' visuale/strutturale, non una run completa di regressione test.
- Alcune superfici, come lobby card Mines, sono valutate anche da componenti e
  contratti perche' nel catalogo locale Mines master e' hidden.
- Non e' stata fatta implementazione correttiva. Dove dico "estrarre" o
  "consumare" e' raccomandazione, non stato fatto.

Classificazione applicata:

- **Aderente**: BOXE rispetta gia' l'aspettativa product rispetto a Mines o ai
  mockup, con rischio basso.
- **Parziale**: base corretta ma manca un pezzo visivo, comportamentale,
  amministrativo o di consumo shared.
- **Divergente**: direzione attuale diversa dall'aspettativa product.
- **Mancante**: superficie non presente in BOXE o non consumata in modo utile.

Tipi di correzione:

- **Estrazione shared**: Mines ha gia' il pattern, ma e' ancora locale o va
  consolidato in `game-runtime`/`title-editor` prima di far consumare BOXE.
- **BOXE consume esistente**: il pezzo shared esiste gia', BOXE deve usarlo
  meglio o collegarlo a dati/assets corretti.
- **BOXE game-specific**: logica o visuale propria del gioco BOXE.
- **Mines local da estrarre per giochi futuri**: tech debt platform che non
  blocca solo BOXE, ma blocchera' HI-LO e giochi successivi.

## 2. Surface-by-surface audit table

| Superficie | Mines reference | BOXE current | Aspettativa product | Verdetto current | Tipo correzione raccomandata |
| --- | --- | --- | --- | --- | --- |
| Lobby card render | Card e launcher passano da catalog/player shell condivisa; Mines locale e' hidden nel DB audit ma il pattern e' shared. | BOXE `boxe001` e' visibile in lobby e usa il flusso catalog/title. | Struttura identica, solo artwork/titolo/descrizione game-specific. | Aderente | Nessuna correzione strutturale; mantenere guard su `PlayerGameCard`/catalog shared. |
| Launch Cashier modal | Modal/picker saldo platform, con route title/game. | BOXE usa lo stesso entry path e i parametri `title_code`/`wallet_source`. | Identico fino all'ingresso gioco. | Aderente | BOXE consume esistente; regression visual side-by-side come gate. |
| Provider intro gate | `GameProviderBootstrap`, moromike lab video, fullscreen panel. | Consuma lo stesso componente shared. | Identico. | Aderente | BOXE consume esistente; nessuna fork locale. |
| How-To-Play gate, layout | `GameHowToPlayGate` shared: overlay, cards, CTA. | Consuma lo stesso layout shared. | Layout identico, contenuto diverso. | Aderente | BOXE consume esistente; layout protetto. |
| How-To-Play gate, contenuti | Mines cards: prepara mano, diamanti, incassa/rischia. | BOXE cards: Bet, Pick, Collect, ma mini-visual ancora griglia 5x5 generica. | Contenuto BOXE-specific e coerente con boxe1 splash/doc. | Parziale | BOXE game-specific: mini-visual deve diventare pyramid/box, non griglia Mines-like. |
| Table Balance gate | Shared `GameTableBalanceGate`; real mode prima di provider/how-to. | Dopo Step 5 ha lo stesso sequencing e componente. Callback BOXE resta placeholder senza table session backend. | Visuale e sequencing identici; lifecycle reale da convergere quando BOXE real e' product-ready. | Parziale | Estrazione shared/BOXE consume: visual ok, table-session lifecycle non ancora simmetrico. |
| Demo mode boot sequencing | Provider -> How-To -> Gameplay. | Provider -> How-To -> Gameplay. | Sequencing identico. | Aderente | Guard di sequencing per ogni nuovo gioco. |
| Real cash/bonus boot sequencing | Table gate -> Provider -> How-To -> Gameplay. | Stesso ordine post Step 5. | Sequencing identico per cash e bonus. | Aderente | Guard di sequencing per ogni nuovo gioco. |
| Gameplay area lato sinistro, settings rail | Mines ha una left rail forte: info/audio, grid/mines, bet input, quick chips, Bet/Collect, balance/win. | BOXE ha settings separati a sinistra e bet panel a destra; nessuna rail Mines-equivalente. | Lato sinistro gameplay uguale o quasi uguale a Mines; solo parametri gioco diversi. | Divergente | Estrazione shared critica: `GameControlRail`/`GameBetPanel` da Mines, BOXE consuma rows/difficulty. |
| Gameplay action/bet/balance | Mines integra bet, quick amounts, collect, saldo e vincita nella rail. | BOXE mette bet/balance/action in panel destro; no collect idle, no quick chips, no saldo rail Mines. | Ergonomia Mines condivisa, action labels e stato game-specific. | Divergente | Estrazione shared critica: action/balance/bet controls platform runtime. |
| Gameplay area lato destro, board | Mines board 5x5 dentro stage con title/payout. | BOXE pyramid 3 colonne funzionale, ma composizione e scala lontane dai mockup. | Board BOXE-specific, aderente a boxe2/4/5/6/7. | Divergente | BOXE game-specific: pyramid mockup parity con assets e stato riga. |
| Payout display / multiplier ladder | Mines ladder sotto title nello stage. | BOXE ladder orizzontale sopra pyramid; non mostra mine icon/count come doc, current pill debole. | BOXE-specific top-center ladder con current multiplier pill e rischio prossima riga. | Parziale | BOXE game-specific: ladder visiva e semantica da mockup/doc. |
| Game info modal / runtime tools | Mines ha info button, `MinesRuntimeTools`, `MinesRulesModal`, tabs rules/replay. | BOXE non ha info modal equivalente nel gameplay. Rules HTML esiste in admin ma non e' esposto come runtime tool completo. | Shell runtime tools condivisa, contenuto rules game-specific. | Mancante | Estrazione shared: runtime tools/rules modal da Mines a `game-runtime`. |
| Replay viewer | Mines ha `MinesReplayViewer` e replay tab nel modal. | BOXE backend/replay capability esiste in area backend, ma player runtime non espone viewer equivalente. | Replay shell condivisa con adapter per eventi game-specific. | Mancante | Estrazione shared: replay viewer shell + BOXE adapter. |
| Mobile portrait variant | Mines mobile usa stage/board/action stack e mantiene ergonomia da gioco. | BOXE mobile e' un layout verticale lungo, generico, con controls sopra board; non rispecchia mockup o left-rail adaptation. | Mobile deve essere una variante coerente, non solo responsive collapse. | Divergente | Estrazione shared + BOXE consume: mobile game shell e control rail adattiva. |
| Rotation gate landscape-short | Mines usa `GameShortViewportGate` con CSS locale. | BOXE usa `GameShortViewportGate` con copy BOXE. | Pattern identico, copy eventualmente game-specific. | Parziale | BOXE consume esistente + estrazione CSS visibility condivisa. |
| Game list / variant management | Platform catalog/title detail condivisi; duplicate Mines supportato. | BOXE registrato in `REGISTERED_ENGINE_EDITORS` e title detail funziona. | Engine/title management condiviso. | Aderente | Nessuna correzione urgente; mantenere registry. |
| Title detail shell/header | Shared route e `TitleEditorShell`; header/back/preview/archive comuni. | BOXE usa lo stesso contenitore e command bar. | Identico shell, editor interno plugin. | Aderente | BOXE consume esistente. |
| Title detail Overview tab | Mines overview e' ricco: lingua pubblicata, runtime summary, fairness diagnostics context. | BOXE overview e' minimale: rows/difficulty draft/live/runtime. | Shared overview frame con metriche game-specific. | Parziale | Estrazione shared admin: overview panel adapterizzato. |
| Copy & i18n tab | Mines ha manifest ampio, locale publish, copy editor piu' maturo. | BOXE ha copy per 4 locale, locale selector, ma schema e UI locali. | Shell copy/i18n condivisa, manifest per gioco. | Parziale | Estrazione shared admin: copy editor generico + game manifest. |
| Rules HTML tab | Mines gestisce sezioni multiple: ways_to_win, payout, settings, bet_collect, ecc. | BOXE gestisce solo `bet_collect`. | Editor shared multi-section; contenuto/sezioni game-specific. | Parziale | Estrazione shared admin: rules section editor con adapter. |
| Game config tab | Mines grid/mines editor locale. | BOXE rows/difficulty editor locale. | Form shell condivisa, campi game-specific dichiarativi. | Parziale | Estrazione shared admin: config form framework, field adapters. |
| Board assets tab | Mines separa game card, safe/mine board assets e li consuma nel board. | BOXE assets include game_card/symbol_safe/symbol_mine, ma gameplay board non consuma davvero diamond/mine assets. | Asset pipeline condivisa, consumo runtime verificato. | Parziale | Estrazione shared + BOXE consume: asset registry runtime hook. |
| Sounds tab | Mines ha sounds editor/runtime audio assets. | BOXE non ha Sounds tab, e BOXE v1 e' dichiarato silent/default. | Decidere se v1 richiede parita tab o defer esplicito. | Mancante | Estrazione shared admin/runtime audio oppure PO defer documentato. |
| Theme tab | Mines theme editor include tokens, advanced skin, skin assets, preview piu' ricca. | BOXE theme editor e' piu' semplice, tokens/presets senza advanced skin/assets. | Theme shell condivisa; differenze solo dove game-specific. | Parziale | Estrazione shared admin: theme editor comune con game-specific capabilities. |
| Lobby card / Assets tab | Mines combina game card e board assets. | BOXE ha `Assets`, ma label/tab e consumo non sono allineati; game card presente, symbol assets non visualizzati in gameplay. | Stessa ergonomia e nomenclatura, assets game-specific. | Parziale | BOXE consume esistente + estrazione asset editor shell. |
| Draft / Publish workflow ergonomics | Mines e BOXE usano `TitleEditorCommandBar`. | BOXE usa lo stesso command bar. | Identico. | Aderente | Guard only; mantenere command bar unico. |
| Validation error display | Mines ha warning/status e validazione piu' estesa. | BOXE mostra `Validation errors` ma meno integrato nei singoli field. | Shared validation display e field-level mapping. | Parziale | Estrazione shared admin: validation summary + field targeting. |
| Theme tokens applicati | Mines runtime consuma `TitleThemeProvider`, skin e asset theme. | BOXE passa da `TitleThemeProvider`, ma gameplay usa molto CSS locale e non mostra asset skin. | Token shared applicati al shell e ai controlli comuni; board puo' avere token game-specific. | Parziale | Estrazione shared + BOXE consume tokens in gameplay. |
| Typography | Mines usa gerarchia forte e coerente tra rail/stage. | BOXE usa heading grandi/generic bold e panel admin-like; meno casino-game, piu' dashboard. | Shell typography condivisa, eccezioni solo per brand title/board. | Divergente | Estrazione shared typography/runtime UI primitives. |
| Spacing system | Mines ha rapporto rail/stage definito. | BOXE e' distribuito su tre colonne con grandi vuoti; mockup e Mines chiedono composizione piu' compatta. | Spacing condiviso nella shell gameplay; board-specific al centro/destra. | Divergente | Estrazione shared layout grid + BOXE mockup layout. |
| Color palette | Mines ha nero/verde/viola stage coerente; mockup BOXE e' nero con accenti cyan/green. | BOXE current e' slate/blue dashboard, lontano da mockup e da shell Mines. | Protected shell non deve cambiare; gameplay puo' avere BOXE palette ma non dashboard generica. | Divergente | Estrazione shared tokens + BOXE palette mockup. |
| Animation patterns | Mines ha board reveal, button pulse, win celebration. | BOXE ha CSS safe/mine/payout/confetti, ma resa mockup non convincente e non asset-based. | Stato animation shared dove possibile; reveal BOXE-specific fedele al doc. | Parziale | BOXE game-specific con primitives condivise. |
| CSS ownership/scope | Mines CSS e' enorme e contiene molte primitive riutilizzabili ma locali. | BOXE CSS e' separato e ricrea pannelli/controls invece di consumare primitive gameplay. | Shared CSS/components per shell e controls; CSS locale solo board/payout speciali. | Parziale | Mines local da estrarre per giochi futuri. |

## 3. Verdetti aggregati

| Verdetto | Count | Esempi |
| --- | ---: | --- |
| Aderente | 9 | Provider intro, how-to layout, demo sequencing, real sequencing, title detail shell, draft/publish command bar. |
| Parziale | 15 | Table gate lifecycle, BOXE how-to content, payout ladder, admin overview/copy/rules/config/assets/theme, token application. |
| Divergente | 7 | Gameplay left rail, bet/balance/action layout, pyramid visual parity, mobile portrait, typography, spacing, palette. |
| Mancante | 3 | BOXE runtime game info modal, replay viewer, Sounds tab. |

Lettura brutale: il pre-game shell e il contenitore admin sono in una forma
buona. Il gameplay player-facing e l'editor admin interno sono ancora troppo
BOXE-locali o troppo generici. La retrospective precedente ha sottostimato
l'ampiezza dell'admin parity: non e' solo "manca gameplay mockup", e' anche
"Mines ha un backoffice prodotto, BOXE ha un editor locale sufficiente".

## 4. Tipi di correzione

Questi count considerano le 25 superfici non aderenti. Le 9 superfici aderenti
richiedono solo guard/regression.

| Tipo | Count | Note |
| --- | ---: | --- |
| Estrazione shared | 18 | E' la massa del lavoro: gameplay control rail, runtime tools/rules/replay, admin tabs, asset/theme/validation shells. |
| BOXE consume esistente | 3 | Soprattutto asset runtime, rotation gate/CSS shared, consumo piu' completo di tokens e componenti gia' disponibili. |
| BOXE game-specific | 3 | Pyramid board mockup parity, payout ladder, BOXE-specific reveal/animation polish. |
| Mines local da estrarre per future giochi | 1 | Il CSS/component set Mines e' ancora il vero "reference implementation", non ancora un prodotto platform consumabile. |

Distribuzione: 18/25 = 72% estrazione shared. Questo e' coerente con la
direttiva product owner "eredita il piu' possibile, copia il meno possibile".
Se nei prossimi WP il lavoro diventasse soprattutto "patch BOXE locale", sarebbe
un segnale di regressione metodologica.

## 5. Pattern strutturali emersi

### Parti Mines ancora troppo locali

- Gameplay control rail: settings, bet input, quick chips, action buttons,
  balance/win footer.
- Runtime tools: info button, audio controls, rules modal, replay tab.
- Replay viewer: oggi e' Mines-oriented, ma il concetto e' platform.
- Admin tabs: copy/i18n, rules, config, assets, sounds, theme hanno pattern
  comuni ma sono implementati dentro Mines.
- Theme/skin assets: Mines e' piu' avanti di BOXE, ma il prodotto e'
  title-level, non Mines-only.
- CSS primitives: rail, stage, buttons, cells, mobile stack e short-viewport
  sono disseminati in `mines.css`.

### Shared robusti che tengono

- `game-runtime` pre-game shell: `GameProviderBootstrap`,
  `GameHowToPlayGate`, `GameTableBalanceGate`, `GameBootShell`.
- Launch context e storage namespacing: abbastanza solidi dopo lo Step 5.
- `TitleEditorShell`, engine registry e `TitleEditorCommandBar`.
- Platform catalog/title routing.
- Title theme API/provider come fondazione.

### Dove "game-specific" e' giustificato

- Math, RNG, state machine, payout path e backend adapter.
- Board geometry e reveal semantics: Mines grid vs BOXE pyramid.
- Payout ladder content/semantics: mine count/next-risk per BOXE.
- Visual assets specifici: diamond, mine, splash, BOXE icon.
- Copy/rules contenuto, non il contenitore editor.

### Dove "game-specific" e' stata scorciatoia

- BOXE bet panel a destra invece di consumare una rail condivisa.
- BOXE settings panel locale invece di adapter sopra controlli runtime comuni.
- BOXE admin tabs locali invece di uno schema title-editor comune.
- BOXE theme editor ridotto invece di capability shared con feature flags.
- BOXE gameplay CSS che ricrea card/panel/button invece di usare primitives
  estratte da Mines.

### Implicazione per giochi 3-20

Il vero prodotto non e' "scrivere un nuovo frontend per ogni gioco". Il prodotto
e' una `GameRuntimeShell` con slot/adapters:

- pre-game gates shared;
- left/control rail shared;
- stage/header/runtime tools shared;
- board adapter game-specific;
- payout adapter game-specific;
- admin editor shared con schema adapter;
- assets/theme/audio/replay shared con capabilities per gioco.

HI-LO non deve partire da "copia Mines e rinomina". Deve partire da "consuma
shell shared, implementa solo board/math/payout/adapters". BOXE deve diventare
il forcing function che estrae questa architettura.

## 6. Lista WP raccomandati prioritizzati

| WP | Tipo | Scope | Backward compat impact | Effort stimato | Priorita | Dipendenze | Stop-and-Ask attesi | Generalization candidate |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- |
| WP-PLAYER-GAMEPLAY-CONTROL-RAIL-SHARED-EXTRACTION | Estrazione shared | Estrarre da Mines left rail, bet input, quick chips, action buttons, balance footer in componenti shared consumati da Mines e BOXE. | Mines visual baseline INVARIATO e' gate hard. | 5-8 prompt | 1 | Nessuna, ma richiede Parte A design. | Se Mines rail dipende da session model non generalizzabile; se BOXE rows/difficulty non si mappano pulitamente. | Si, base per tutti i giochi futuri. |
| WP-BOXE-GAMEPLAY-MOCKUP-PARITY | BOXE game-specific | Rifare composizione pyramid, ladder, board cells, assets diamond/mine, idle/safe/loss states contro boxe2/4/5/6/7. | Mines invariato; BOXE baseline aggiornata. | 6-10 prompt | 1 | Control rail shared o decisione PO se procedere in parallelo. | Se mockup va interpretato come pixel target o solo direzione. | Si, mockup come gate vincolante. |
| WP-RUNTIME-TOOLS-RULES-REPLAY-SHARED | Estrazione shared | Estrarre game info button/modal, rules sections, replay shell da Mines; BOXE adapter per rules/replay. | Mines modal/replay baseline invariato. | 4-7 prompt | 2 | Gameplay shell/control rail preferibile. | Se replay payload BOXE non contiene eventi sufficienti per viewer. | Si, runtime tools obbligatori per giochi nuovi. |
| WP-TITLE-EDITOR-TABS-SHARED-EXTRACTION | Estrazione shared | Generalizzare Overview, Copy i18n, Rules HTML, Config, Assets, Sounds, Theme come tab shell con adapters. | Mines admin screenshot baseline invariato; BOXE tabs possono crescere. | 7-11 prompt | 2 | Nessuna, ma richiede Parte A forte. | Se si scopre che Mines editor e' troppo accoppiato per estrazione singola. | Si, backoffice scalable 10-20 giochi. |
| WP-BOXE-ASSETS-RUNTIME-CONSUME | BOXE consume esistente | Collegare `symbol_safe`, `symbol_mine`, game_card/theme assets al gameplay e preview admin. | Mines invariato; BOXE visual cambia. | 2-4 prompt | 2 | Mockup parity o asset contract deciso. | Se assets attuali non sono finali o dimensioni non compatibili. | Si, asset consumption audit pre-close. |
| WP-BOXE-TABLE-SESSION-LIFECYCLE-PARITY | Estrazione shared | Eliminare placeholder table gate BOXE e collegare table session/access session lifecycle come Mines, con adapter game code/title. | Mines table tests invariati; BOXE real mode behavior cambia. | 4-6 prompt | 3 | Product decision su quando real BOXE diventa obbligatorio. | Se backend shared service richiede refactor piu' ampio. | Si, lifecycle symmetry gate pre-frontend close. |
| WP-BOXE-MOBILE-PORTRAIT-PARITY | Estrazione shared + BOXE consume | Portare mobile a shell coerente: controls ergonomici, board leggibile, no dashboard stack. | Mines mobile baseline invariato. | 3-5 prompt | 3 | Control rail shared. | Se PO accetta mobile v1 defer. | Si, mobile gate per ogni gioco. |
| WP-BOXE-ANIMATION-POLISH | BOXE game-specific | Diamond flip, mine explosion/red pulse, current-row reveal, multiplier pill slide fedeli al doc. | Mines invariato; BOXE baseline aggiornata. | 3-5 prompt | 4 | Mockup parity. | Se animazioni v1 devono essere lightweight o production-polish. | Si, state animation checklist. |
| WP-PLAYBOOK-V2-PARITY-GATES-DISTILLATION | Pure cleanup/process | Formalizzare gate: mockup open, consume audit, sequencing audit, backend lifecycle symmetry, side-by-side screenshots. | Nessun impatto runtime. | 2-3 prompt | 1 | Questo audit approvato. | Se CTO vuole aspettare dopo fix BOXE. | Si, obbligatorio per HI-LO. |

Ordine raccomandato:

1. Distillation minima dei gate nel Playbook v2 prima di altri fix critici.
2. Gameplay control rail shared extraction.
3. BOXE mockup gameplay parity.
4. Runtime tools/rules/replay shared.
5. Title editor tabs shared extraction.
6. Asset runtime consume, mobile, animation e table lifecycle in base alla
   decisione PO su "accettabile" vs "eccellente".

Questo ordine riduce rework: se si rifinisce BOXE local prima di estrarre la
rail/shared admin, si rischia di pagare due volte.

## 7. Open questions per product owner

1. Left rail gameplay: deve essere pixel-perfect Mines, oppure stessa ergonomia
   con micro-variazioni BOXE?
2. Mockup BOXE: sono target pixel/visual gate o reference di composizione da
   adattare al design CasinoKing?
3. Bottom system icon strip visto nei mockup: obbligatorio per livello
   accettabile o solo per livello eccellente?
4. BOXE palette: deve restare vicina a Mines default, oppure e' ammessa una
   variante dark/cyan "tower-style" purche' non sembri dashboard?
5. Sounds tab: BOXE v1 puo' dichiararsi silent e rimandare audio, oppure la
   parita admin richiede il tab subito?
6. Replay viewer: obbligatorio per "accettabile" o puo' stare nel livello
   "production-ready/eccellente"?
7. Table session lifecycle BOXE: il placeholder e' ancora accettabile fino a
   demo/prototipo, o va chiuso prima di dichiarare BOXE product-acceptable?
8. Admin backoffice: il product owner vuole "spacchettare Mines anche nel
   backoffice" subito, oppure prima solo BOXE gameplay?
9. Mobile: e' gate del livello accettabile o puo' essere un WP separato dopo
   desktop?
10. Assets: usare subito `diamond_green_v001.png` e `mine_fucsia_002.png` come
   fonti vincolanti, o aspettare un asset pass finale?

## 8. Verdict tecnico finale

BOXE non e' lontano lato backend. E' lontano lato prodotto visibile.

Il backend BOXE e' la parte piu' sana: math, state machine, API, admin config
base, adapter e settlement sono un buon secondo gioco. Il pre-game shell ora e'
ragionevolmente allineato a Mines dopo lo Step 5. Ma il gameplay attuale non e'
il gioco mostrato nei mockup: e' un engine funzionante con una UI generica,
troppo dashboard, non abbastanza casino-game, non abbastanza BOXE.

La mia retrospective precedente ha sottovalutato due cose:

- admin parity e' piu' ampia del previsto. BOXE non deve solo avere un editor;
  deve spingere l'estrazione di tabs/capabilities dal backoffice Mines;
- la left rail non e' un dettaglio visuale. E' il pattern ergonomico base della
  piattaforma game runtime. Finche' resta Mines-local, ogni nuovo gioco tendera'
  a ricrearla male.

Stima realistica:

- **BOXE accettabile**: 10-14 prompt. Include rail shared minima, gameplay
  desktop fedele ai mockup principali, assets consumati, payout ladder corretta,
  mobile non rotto, pre-game invariato.
- **BOXE eccellente/production-ready**: 24-36 prompt. Include admin tabs shared,
  runtime tools/rules/replay, table lifecycle real, mobile portrait curato,
  animation polish, visual baselines complete e Playbook v2 distillato.

Rischio strutturale residuo: se il team prova a "sistemare BOXE" con patch
locali, il gioco 3 costera' quasi quanto il gioco 2. La correzione giusta e'
piu' lenta nei primi WP, ma costruisce la piattaforma: estrarre Mines dove
Mines e' ancora reference locale, far consumare BOXE, e lasciare game-specific
solo math, board, payout, copy e assets.

Verdetto brutale: BOXE e' un buon proof tecnico, non ancora un buon secondo
prodotto visivo. Per diventare il modello dei giochi 3-20 deve smettere di
essere "un BOXE che somiglia a un'app" e diventare "un gioco che consuma la
runtime platform".
