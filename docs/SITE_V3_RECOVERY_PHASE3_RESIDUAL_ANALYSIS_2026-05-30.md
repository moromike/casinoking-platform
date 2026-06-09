Status: ACTIVE
Last meaningful update: 2026-05-30
Owner: CTO (Claude) — Executor: Codex — Validation: Michele on :3000

# Site V3 Recovery — Phase 3: Residual Regressions + Missing Feature Analysis

Dopo Phase 2B (admin/finance ripristinati, giochi a parita' visiva statica),
Michele ha validato su :3000 e trovato problemi residui. Questo doc separa
RIGRESSIONI (da ripristinare) da GAP DI FEATURE (mai completati). Diagnosi
verificata contro git/CSS, non sul racconto.

## Verdetto onesto: cosa e' salvo, cosa no

SALVO (vero valore, non perso):
- Backend GMP (fondamento direzione B = giochi come moduli esterni): intatto, 0 diff, testato.
- Admin/Finance: ripristinati dark-compact verso main, verificati a schermo dal CTO (gate Batch 1).
- Isolamento CSS strutturale: 2 root (`ck-admin-legacy-page` / `site-v3-cms-admin-page`) impediscono il ri-inquinamento.
- Migrazione V3 = unico frontend: fatta.
- Game logic / RNG / payout / board / reveal: mai toccati.

NON CHIUSO (debito reale):
- 3 regressioni residue (sotto: R1, R2, R3) introdotte DAL recovery stesso.
- 1 feature mai completata: module building/editing (G1) = il motivo originale del lavoro.

Risposta a "abbiamo perso tempo/soldi": parzialmente sprecato, NON tutto. Il
fondamento (GMP backend + isolamento CSS + admin ripristinato) regge. Ma la
feature-obiettivo (CMS module building) non e' mai arrivata, e il recovery ha
lasciato 3 code da chiudere. La via d'uscita e' chiudere le 3 regressioni (poche
righe, chirurgiche) e poi trattare il module building come WP pianificato pulito.

## R1 — Login/header pubblico player ROTTI (regressione Batch 1)

Sintomo (Michele): pagina login "rotta, fa vomitare"; campi email/password senza stile, inline crudi.

Causa (verificata): il revert+re-scope del Batch 1 ha riportato globals.css alla
baseline main e RI-AGGIUNTO admin/CMS/account, ma ha DIMENTICATO il blocco CSS
del player pubblico:
- `site-v3-player-panel`: backup 7 -> ora 0
- `site-v3-player-form`: backup 4 -> ora 0
- `site-v3-text-link`: backup 1 -> ora 0
- `site-v3-player` complessivo: backup 210 -> ora 125 (~85 regole perse)

I componenti `player-login-page.tsx` USANO ancora quelle classi (`site-v3-player-panel`,
`site-v3-player-form`, `site-v3-player-field-grid`, `site-v3-player-form-actions`,
`site-v3-button is-secondary`, `site-v3-text-link`) ma il CSS non esiste piu'.

Era il rischio che il CTO aveva segnalato in Phase 2A (A3: "alcune pagine player
Site V3 potrebbero perdere stile e vanno ri-aggiunte scoped"). Non e' stato fatto.

Fix: ri-portare dal backup 6141c17 le regole player pubbliche mancanti
(login/header/text-link e il delta site-v3-player), scoped, senza re-inventare.
Baseline = stato backup pre-recovery (era visivamente accettabile).

## R2 — Giochi "non ottimizzati" / finestra piu' grande dello schermo (regressione Batch 2)

Sintomo (Michele): i giochi si lanciano in modalita' non ottimizzata; la finestra
di lancio e' piu' grande dello schermo; problemi di layout interni.

Causa (verificata): nel Batch 2, per ripristinare la X e togliere l'host chrome,
Codex ha rimosso da mines/boxe/hi-lo standalone le righe:
- `isEmbeddedView ? "mines-page-shell-embedded" : null`
- `isEmbeddedView ? "mines-product-shell-embedded" : null`
(stesso pattern per boxe/hi-lo).

MA le regole CSS `.mines-page-shell-embedded` / `.mines-product-shell-embedded`
ESISTONO ANCORA (mines.css: 18 regole embedded; boxe.css: 4; hi-lo.css: 2) ed
erano l'OTTIMIZZAZIONE del layout quando il gioco gira dentro l'iframe. Rimuovendo
l'applicazione della classe, il gioco rende in modalita' "piena" dentro un iframe
a 100vh -> overflow / finestra piu' grande dello schermo / layout non compatto.

Codex ha equiparato "embedded = host chrome cattivo" e ha buttato anche
l'ottimizzazione. Le due cose erano separate: `mines-host-controls-embedded`
(host chrome, giustamente gestito) vs `*-page-shell-embedded` / `*-product-shell-embedded`
(ottimizzazione layout iframe, da TENERE).

Fix chirurgico: ri-aggiungere le 2 righe `isEmbeddedView ? "...-embedded"` su
page-shell e product-shell per i 3 giochi, MANTENENDO la X ripristinata e SENZA
re-introdurre l'host topbar. 6 righe totali. Verifica: finestra dentro lo schermo,
no scrollbar, X presente.

## R3 — Admin polish: posizionamento bottoni/spazi/CSS (da rifinire)

Sintomo (Michele): admin "fatto da un ubriaco" — posizionamento tasti/bottoni,
ottimizzazione spazi, CSS da rivedere. Builder Site V3: bottoni Publish/Validate/Archive
mal posizionati.

Stato: il re-scope sotto `.ck-admin-legacy-page` / `.site-v3-cms-admin-page` ha
riportato lo stile ma con rifinitura di spacing/allineamento incompleta. Da
verificare superficie per superficie con gli screenshot admin di Michele.

Fix: pass di rifinitura CSS scoped (spacing, allineamento bottoni, densita').
NON re-design. Riferimento = layout pre-disastro dove esisteva.

## G1 — Module building/editing MANCANTE (gap di feature, NON regressione)

Sintomo (Michele, "detto 1000 volte"): manca la parte di BUILDING dei moduli e
di EDITING di quelli esistenti. Module Studio mostra "0 definitions / No custom
definitions yet".

Stato (verificato): `site-v3-module-studio-screen.tsx` ha `onCreateDefinition`
(creazione definizioni custom da template). MANCA: editing di definizioni
esistenti, e il vero page-builder/edit dei moduli montati nelle pagine.

Questo NON e' una regressione: e' la feature-obiettivo che ha motivato l'intero
lavoro e non e' mai stata completata. Va trattata come WP pianificato a se',
DOPO la stabilizzazione (R1-R3), con brief in 2 parti (approccio + esecuzione)
come da regola WP critici.

## Replay giochi — NON verificati

Michele si aspetta i replay "perfetti" ma non li ha testati. Il CTO NON puo'
garantirli senza prova: i componenti esistono (mines/boxe/hi-lo-replay-viewer.tsx)
ma il replay e' passato attraverso le modifiche CSS runtime del Batch 2. Vanno
testati esplicitamente (apertura da account + da finance + post-round) prima di
dichiararli ok. Inseriti come gate in Phase 3.

## Sequenza proposta (stabilita' prima, feature dopo)

FASE 3A — Stabilizzazione regressioni (chirurgica, priorita'):
- R2 giochi embedded (6 righe) — sblocca subito il "non ottimizzato"
- R1 login/header player CSS (ri-porta blocco dal backup, scoped)
- R3 admin polish (pass spacing/bottoni scoped)
- Gate: replay 3 giochi testati; login/account/giochi/admin a parita' baseline.
- CTO controlla di persona finance + giochi (richiesta esplicita Michele): devono
  essere "come erano", ripristino non re-design.

FASE 3B — Module building/editing (feature nuova, WP pianificato):
- Brief Parte A (approccio) + Parte B (esecuzione), gate CTO, validazione Michele.

## Gate duri (invariati)
- Game logic / RNG / payout / board / reveal: 0 diff.
- Backend GMP: 0 diff.
- Parita' verso baseline (backup pre-recovery per player; main per admin/finance), screenshot side-by-side.
- Replay funzionante e leggibile sui 3 giochi.
- Nessuna feature nuova durante 3A.
