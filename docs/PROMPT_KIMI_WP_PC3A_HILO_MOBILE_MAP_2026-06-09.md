# PROMPT KIMI — WP-PC3 Parte A: HI-LO mobile layout, mappa + fit (read-only)

> Incollare in KIMI. **READ-ONLY, niente codice, niente commit.** Branch: `feature/pre-coins`. Gate CTO a fine Parte A.

## Contesto (delta)
DIV-F07 (audit `docs/CROSS_GAME_FRONTEND_PARITY_AUDIT_2026-06-05.md`): HI-LO **non usa** i primitive React mobile condivisi (`useMobileLayout` + `GameMobileControlStack` + `GameMobileSettingsSheet`) usati da Mines/BOXE; fa mobile **CSS-driven** con un suo `matchMedia` (`hi-lo-gameplay.tsx:194`). Effort L, **rischio ALTO** (refactor strutturale).

**INQUADRAMENTO IMPORTANTE (non è un mobile rotto):** il mobile portrait di HI-LO è GIÀ stato accettato come giocabile (AMBER chiuso). Quindi F07 è **parità architetturale**, non un bug user-facing. Inoltre HI-LO è **card-centrico**, i primitive condivisi nascono per board/griglia (Mines/BOXE): forzarli potrebbe NON calzare. La Parte A deve **provare il gap reale** e **valutare il fit**, NON assumere che il pattern Mines/BOXE sia il canonico per HI-LO.

## Task (read-only, evidence-based file:line)
1. **Mappa il mobile attuale di HI-LO:** il `matchMedia` (`hi-lo-gameplay.tsx:194`) — che stato/branch di rendering guida? quali classi/CSS media-query in `hi-lo.css` (o equivalente) gestiscono il layout mobile? cosa cambia tra desktop e mobile a livello DOM? (cita file:line).
2. **Mappa i primitive condivisi** usati da Mines/BOXE: dove è definito `useMobileLayout` (file:line, cosa restituisce); contratto/props di `GameMobileControlStack` e `GameMobileSettingsSheet`; cosa forniscono (stack controlli, sheet impostazioni). Come Mines (`mines-standalone.tsx:315`, `mines-gameplay.tsx:880-897`) e BOXE (`boxe-gameplay.tsx:255,988-1003`) li consumano.
3. **PROVA il gap reale (mobile):** cattura HI-LO vs Mines vs BOXE a viewport mobile — **portrait 390×844** e **short-landscape ~740×360** (Playwright). Misura/osserva: controlli bet/azione raggiungibili? impostazioni raggiungibili? board/carte con clipping o scrollbar? overlap? Allegare screenshot + misure DOM. Domanda chiave: **c'è una deficienza funzionale/visiva REALE nel mobile HI-LO, o è solo un meccanismo diverso con esito equivalente?**
4. **Valuta il FIT:** cosa contengono le "impostazioni" di HI-LO (deck size? niente?) → un `GameMobileSettingsSheet` sarebbe utile o vuoto/forzato? Lo `GameMobileControlStack` (pensato per board) mappa sulla UI a carte di HI-LO?
5. **Proponi approccio con tradeoff** (almeno 2 opzioni + raccomandazione):
   - (a) **migrazione piena** ai primitive condivisi (alto rischio);
   - (b) **parziale** (adottare solo `useMobileLayout` come hook, mantenendo il layout card-appropriate);
   - (c) **eccezione documentata by-design** (HI-LO card-UI diverge legittimamente; nessun refactor, si documenta nel Playbook/atlas).

## Vincoli
- READ-ONLY: zero file modificati, zero commit. Solo analisi + screenshot + DOM + file:line.
- Non assumere il pattern Mines/BOXE come canonico obbligato: il Playbook dice "nessun gioco-template unico, il canonico cambia per asse".

## STOP-AND-ASK
- Se le impostazioni HI-LO non hanno contenuto reale per un sheet mobile (rendendo `GameMobileSettingsSheet` inappropriato) → segnalalo come segnale forte verso l'opzione (b)/(c).
- Se il gap "reale" risulta nullo (mobile equivalente) → dillo chiaramente: è un input decisivo per (c).

## Evidence richiesta nella risposta finale (auto-attestazione)
1. Mappa HI-LO mobile attuale (punto 1) con file:line.
2. Mappa primitive condivisi + consumo Mines/BOXE (punto 2) con file:line.
3. **Screenshot mobile** HI-LO/Mines/BOXE a portrait 390×844 e short-landscape 740×360 + misure DOM (clipping/scrollbar/raggiungibilità controlli).
4. Valutazione fit (punto 4) esplicita.
5. Opzioni (a)/(b)/(c) con tradeoff + raccomandazione motivata.
6. Conferma "READ-ONLY: zero file modificati, zero commit" (`git status` pulito sul tracked).

**Clausola forzante:** esplicita CIASCUNA evidenza sopra + auto-attestazione. Se manca anche una sola evidenza (in particolare gli screenshot mobile reali) = task FAILED a priori; non dichiarare done. STOP CTO a fine Parte A.
