Status: ACTIVE
Last meaningful update: 2026-05-30

# Prompt Codex — Site V3 Recovery, Phase 2 PARTE A (approccio, NO codice)

Il CTO ha approvato l'audit di Phase 1
(`docs/SITE_V3_RECOVERY_PARITY_INVENTORY_2026-05-30.md`). Ottimo lavoro: 30
screenshot, mappa selettori precisa, limiti dichiarati.

Phase 2 = isolamento CSS. E' il primo punto in cui si tocca codice ed e'
esattamente dove la run precedente e' fallita. Quindi si fa in DUE parti.

QUESTO PROMPT = SOLO PARTE A: proponi l'APPROCCIO. NIENTE codice, niente CSS,
niente fix. Solo un documento di proposta che il CTO valida prima della Parte B.

## Obiettivo della Parte A

Produrre `docs/SITE_V3_RECOVERY_PHASE2_APPROACH_2026-05-30.md` che risponda, con
precisione e con riferimenti a file:riga, a queste domande.

### A1. Strategia di isolamento — scegli e motiva UNA via
Confronta esplicitamente due opzioni e raccomandane una:
- Opzione 1 "revert + re-scope": ripartire dal `globals.css` di main (766 righe)
  e re-introdurre SOLO il CSS davvero necessario alle nuove superfici V3 (CMS,
  builder, module studio) sotto selettori scoped. Rischio: rompere superfici V3
  nuove legittime.
- Opzione 2 "scope-in-place": tenere il globals.css attuale ma namespacizzare i
  selettori contaminanti cosi' non escono dal loro contenitore. Rischio: file
  resta gonfio, possibile contaminazione residua.
Per ciascuna: cosa rompe, cosa salva, sforzo, reversibilita'.

### A2. Confine di scoping per i GIOCHI
- Come garantire che NESSUN selettore di V3/admin/globals faccia piu' match sul
  DOM dentro gli iframe gioco.
- Cosa fare di `game-runtime.css` (935 righe, nuovo): tenere namespacizzato?
  spostare sotto una root gioco? Spiega.
- IMPORTANTE: la baseline visiva dei giochi e' il vecchio `frontend` su main
  (i giochi in v3 sono re-implementazioni). Chiarisci come la Parte B verifichera'
  la parita' verso main, non verso lo stato attuale.

### A3. Confine di scoping per ADMIN/FINANCE
- Come togliere la contaminazione del wrapper `site-v3-admin-page
  admin-console-page` (`casinoking-console.tsx:2235`) e dei selettori generici
  ridefiniti, riportando Finance/report al dark-compact di main.
- Come isolare il CSS che serve davvero alle superfici CMS/builder V3 nuove
  senza farlo ricadere su Finance/Player admin/LOG ecc.

### A4. Copertura delle 6 superfici admin non fotografate
Games, Site, Site V3, LOG, Administrators, Platform Settings: la Parte B le deve
verificare con screenshot. Dichiara qui che entreranno nella verifica.

### A5. Le 3 ambiguita' aperte
- HI-LO: e' rotto solo nella X o c'e' un break funzionale? Indaga (senza fix) e
  riporta lo stato reale.
- X close gioco: qual e' lo stato attuale reale vs l'artifact
  `native_game_close_restore` precedente? Chiarisci.
- Player account: la striscia "Dettagli account" rimossa e' regressione o scelta
  product? Segnala come DECISIONE CTO/Michele, non deciderla tu.

### A6. Ordine di esecuzione proposto per la Parte B
Micro-step gated, ciascuno verificabile con screenshot, con il gate associato.

## Divieti (Parte A)
- NIENTE modifiche a codice/CSS/UI/backend. Solo il documento di proposta.
- NON iniziare la Parte B finche' il CTO non approva l'approccio.
- NON toccare game logic (RNG/math/payout/board/reveal) in nessun caso.
- NON toccare i file backend GMP (CTO-approved).

## Consegna
Solo `docs/SITE_V3_RECOVERY_PHASE2_APPROACH_2026-05-30.md` + report di consegna
esplicito. Poi stop: attendi gate CTO.
