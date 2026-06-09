# PROMPT KIMI — FIX Mines replay board tagliata ("Fotografia finale")

> Incollare in KIMI. Fix CSS contenuto. Branch: `feature/pre-coins`. Gate CTO con misura REALE del taglio (NON `overflow`/scrollbar).

## Bug (confermato da screenshot Michele + diagnosi CTO)
Nel replay Mines ("REPLAY MANO / Fotografia finale") la board è **tagliata a destra**: la colonna di destra delle celle esce dalla colonna stretta del pannello.

**Causa (NON re-investigare):** `.mines-board` è un grid item dentro `.mines-replay-board` (`display:grid`). Di default un grid item ha `min-width:auto` → non si restringe sotto la sua min-content → sfora la prima colonna del `.mines-replay-layout` (`grid-template-columns: minmax(220px, 0.9fr) ...`) → `overflow:hidden` la **clippa**. Le celle SANNO restringersi (`MinesBoard` usa `grid-template-columns: repeat(N, minmax(0,1fr))` e `.board-cell` ha `width:100%; aspect-ratio:1`). Manca solo permettere alla board di rimpicciolirsi.

## Fix (in `frontend-v3/app/ui/mines/mines.css`, scoped al replay)
Aggiungi (vicino alle regole `.mines-replay-board`/`.mines-replay-layout`, ~riga 2564+):
```css
.mines-replay-board { min-width: 0; }
.mines-replay-board .mines-board {
  width: 100%;
  max-width: 100%;
  min-width: 0;
}
```
NON toccare il sizing della board di gameplay (regole `.mines-grid .mines-board`, mobile, embedded). SOLO il contesto `.mines-replay-board`.

## Scope
- SOLO il taglio della board nel replay Mines. Niente altro.
- Se noti lo stesso pattern di taglio nel replay di BOXE/HI-LO → **annotalo** (file:line), NON fixarlo ora.

## Gate — misura REALE del taglio (vietato usare overflow/scrollbar come prova)
`overflow:hidden` nasconde il taglio dallo scroll: NON usare `scrollWidth==clientWidth` né "niente scrollbar" come prova. Usa i **bounding box**.
Per ogni grid size **3×3, 5×5, 7×7** (genera i replay con round **demo** veloci di ciascuna dimensione — il layout è uguale a reale), apri il replay Mines "Fotografia finale" e verifica:
1. `boardBox.right <= replayBoardColumnBox.right` (entro 1px) e `boardBox.left >= column.left` → board dentro la colonna.
2. **Tutte le N colonne visibili**: il bordo destro dell'ultima cella di ogni riga ≤ bordo destro della board (entro 1px). Nessuna cella tagliata.
3. Celle quadrate, niente clip orizzontale.
4. Screenshot di ciascuna (3×3, 5×5, 7×7).
Confronto PRIMA/DOPO sul 3×3 (mostra che prima era tagliato, dopo no).

## Vincoli
- `npx tsc --noEmit` + `npm run build` (frontend-v3) verdi.
- NON mutare DB/credenziali/wallet/password per generare i round: usa il flusso demo normale dell'app. (Regola dura.)
- Commit: `git add frontend-v3/app/ui/mines/mines.css && git commit -m "fix(mines): replay board no longer clipped — allow board grid-item to shrink to column"`

## Evidence finale (auto-attestazione)
1. Diff CSS (solo `mines.css`, blocco `.mines-replay-board`).
2. Screenshot replay 3×3 PRIMA (tagliato) e DOPO (intero) + 5×5 e 7×7 DOPO.
3. Misure bounding box (board.right vs column.right; ultima cella per riga dentro la board) per 3×3/5×5/7×7 → tutte dentro.
4. tsc + build verdi. SHA commit.
5. Eventuale nota se BOXE/HI-LO replay hanno lo stesso pattern (senza fixare).

**Clausola forzante:** ogni evidenza esplicita; la prova del NON-taglio DEVE essere via bounding box (non overflow/scrollbar). Manca un'evidenza = FAILED, non dire done.
