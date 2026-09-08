# MANDATO DELLA CORSA GOAL 02 — le due diagnosi

**Leggi questo file per intero prima di fare qualunque cosa.** Le condizioni di arresto
valgono piu' dell'obiettivo.

Autorizzato da Michele l'8/09/2026. Motore: Codex in modalita' GOAL.
Ramo `fase9/diagnosi`, worktree usa-e-getta `wt-diag`.
**Non lavorare mai in `../casinoking-platform` ne' in `../wt-rip`.**

---

## 1. L'obiettivo, in una riga

Due **diagnosi scritte**, non due riparazioni: capire cosa e' rotto e chi ha torto, senza
aggiustare niente.

## 2. Cosa e' cambiato, e devi saperlo

**Tu raggiungi Docker.** Per due giorni si e' creduto di no; era il sandbox. Se questa
sessione e' partita con l'accesso pieno, `./scripts/ck-test.sh ...` gira. **Provalo subito
con un collaudo solo**, e se non gira dillo nell'esito invece di dedurre che sia
impossibile.

## 3. DIAGNOSI A — il caso REG-02

`tests/integration/test_seamless_controlli_di_casa.py::test_reg02_sospensione_non_blocca_sessione_aperta_ma_blocca_sessione_nuova`
e' rosso. Il contratto dice che risponde `400` e che **non e' accertato se sbagli la regola
o il collaudo.**

Devi rispondere a **una domanda sola**: *ha torto il prodotto o ha torto il collaudo?*

- Riproduci il caso a mano, con i comandi, e riporta la risposta vera.
- **Leggi il registro del backend** (`docker logs casinoking-backend-1`): stanotte e'
  stato li' che si sono trovate le due cause piu' importanti della fase.
- Concludi in una delle due direzioni, **motivando**. Se sbaglia il collaudo, scrivi
  **perche' e' stato scritto male**: un collaudo costruito male su una regola di sessione
  e' esattamente il tipo di errore che si ripete.

**Attenzione, un'insidia misurata stanotte.** Tutti e sei i collaudi di quel file oggi
falliscono con lo stesso `500` + `retryable:true`, perche' un'eccezione non tradotta sale
fino in cima. **Quel 500 puo' nascondere il vero comportamento di REG-02.** Se e' cosi',
dillo: la diagnosi diventa *«non accertabile finche' RIP-01 non traduce gli errori»*, ed e'
una risposta legittima e utile. **Non inventare una conclusione per averne una.**

## 4. DIAGNOSI B — le due voci del censimento

`test_censimento_open_round_db_requirements` e `test_censimento_rollback_missing_in_platform`
sono rossi. Non sono difetti di codice: sono **capacita' mancanti**.

Devi produrre, per ciascuno: **cosa esattamente manca**, e **quanto costerebbe farlo** —
in termini di quali file andrebbero toccati e se serve una migrazione, non in ore.

**Un aggancio gia' trovato, verificalo e usalo.** La diagnosi di RIP-07 ha accertato che
l'adattatore Boxe non soddisfa il protocollo `PlatformGameAdapter` perche' gli manca
`rollback_round` — il verbo che restituisce i soldi — mentre il protocollo ne chiede
quattro (`backend/app/modules/platform/game_modules/adapter.py:139`). **Il rollback
mancante nella piattaforma e il rollback mancante nell'adattatore sono probabilmente la
stessa lacuna vista da due lati.** Verificalo: se e' cosi', vanno chiusi insieme, e la
decisione di Michele e' una sola invece di due.

**La decisione «si costruisce o si registra» NON e' tua.** Tu produci il dossier che la
rende prendibile.

## 5. Cosa NON puoi fare, mai

- **Nessuna modifica al codice di produzione.** Niente `backend/`, niente `scripts/`,
  niente migrazioni. Neanche una riga, neanche se e' ovvia.
- **Nessuna modifica ai collaudi esistenti.** Sono la specifica: si leggono.
- Puoi creare **solo** file nuovi sotto `missioni/2026-09-08-goal-diagnosi/`.
- Se per capire ti serve modificare qualcosa, **scrivi cosa modificheresti e perche'**, e
  fermati. E' un dossier, non un tentativo.

## 6. Condizioni di arresto — ti fermi anche se non hai finito

1. **Novanta minuti di orologio.** La modalita' GOAL non ha tetto di spesa: il tetto e'
   questo.
2. **Tre turni consecutivi senza progresso.** Progresso = un file scritto, o una domanda
   che passa da aperta a chiusa. «Sto ancora analizzando» e' progresso al primo turno e
   stallo al terzo.
3. **Un collaudo verde diventa rosso: ti fermi.** Il metro e' **663 verdi**. Non dovresti
   toccare niente, quindi se succede hai violato il punto 5.
4. **Non riesci a eseguire i collaudi?** Consegna dichiarandolo non verificato. Un lavoro
   non verificato si consegna come non verificato, mai come finito.
5. **Le due diagnosi sono indipendenti.** Se A si impantana, passa a B: non restare fermo
   su una sola.

## 7. Come si chiude

Non lo dichiari tu marcando l'obiettivo completo. Scrivi
`missioni/2026-09-08-goal-diagnosi/ESITO.md` con:

- la risposta alla domanda di A, o il motivo per cui non e' accertabile adesso;
- il dossier di B, con i file coinvolti;
- **l'output vero dei comandi**, incollato, non riassunto;
- quali comandi non sei riuscito a lanciare;
- una sezione **«cosa queste diagnosi NON dimostrano»**.

Poi il lavoro passa a un revisore che non sei tu. **Non marcare l'obiettivo `complete`
sulla base dell'intenzione o di una risposta finale plausibile.**

## 8. Se scopri che il mandato e' sbagliato

Fermati e scrivilo. **Un mandato sbagliato eseguito bene resta lavoro buttato**, e stanotte
un lavoro impeccabile e' stato respinto proprio perche' rispondeva alla domanda sbagliata.
