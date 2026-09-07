Status: ACTIVE
Last meaningful update: 2026-09-04

# INT-05 — Manuale di integrazione lato Piattaforma

**Per chi**: un provider esterno che vuole portare i **propri** giochi sulla
piattaforma CasinoKing.

**Modello**: seamless wallet. Wallet, saldi e ledger sono della piattaforma
CasinoKing; il tuo gioco **non tocca mai il denaro**: ogni giocata e' una
chiamata verso il nostro seamless wallet.

Riferimento vincolante: `documenti/CONTRATTO-API-SEAMLESS-WALLET-v1.md`
(da qui in poi «il Contratto»). In caso di dubbio, vale il Contratto.

## 1. Chi fa cosa

| Responsabilita' | Piattaforma CasinoKing (noi) | Provider (tu) |
| --- | --- | --- |
| Autenticazione player, sessione | ✔ | — |
| Wallet, saldi, ledger, idempotenza finanziaria | ✔ | — |
| Emissione `game_launch_token` | ✔ | — |
| Verifica del token al lancio | — | ✔ |
| RNG, fairness, board, reveal, esito tecnico | — | ✔ |
| Calcolo payout finale della round | — | ✔ |
| Debit puntata / credit vincita | ✔ | — |

## 2. Cosa ricevi da noi (piattaforma)

- Il `game_launch_token`: JWT che emettiamo quando un player lancia il tuo
  gioco (claim minimi nel Contratto, sez. 2.1: `sub` = player, sessioni,
  `game_code`, scadenza, `nonce`; TTL <= 5 minuti, monouso). Lo verifichi con
  la chiave pubblica/issuer che ti comunichiamo in onboarding.
- Gli endpoint seamless wallet, raggiungibili via HTTPS con il service token
  che ti rilasciamo:
  - `POST /internal/v1/seamless-wallet/rounds/open`
  - `POST /internal/v1/seamless-wallet/rounds/settle`
  - (opzionale v1) `POST /internal/v1/seamless-wallet/play-sessions/close`

## 3. Cosa devi implementare tu (provider)

1. **`POST /internal/v1/game-launch/validate`** sul tuo backend gioco:
   riceve il `game_launch_token` dal frontend, ne verifica firma, scadenza e
   `game_code`, apre la sessione tecnica di gioco e risponde come da
   Contratto (sez. 4).
2. **Le API pubbliche del tuo gioco** (configurazione, azioni di gioco,
   stato sessione, fairness) con payload di dominio gioco puro: **nessun
   campo finanziario** (saldo, wallet) esposto o gestito.
3. **Le chiamate al nostro wallet**:
   - all'accettazione della puntata → `rounds/open` (con `idempotency_key`
     nuova generata da te per quel tentativo);
   - alla chiusura della round → `rounds/settle` con `outcome` = `won` +
     `payout_amount`, oppure `lost` + `payout_amount: "0"`.

## 4. Flusso completo, passo per passo

1. **Lancio.** Il player autenticato lancia il tuo gioco; il frontend lo apre
   con il `game_launch_token`.
2. **Validazione.** Il tuo frontend chiama il tuo `game-launch/validate`;
   tu verifichi il token e apri la sessione tecnica.
3. **Puntata.** Validi la configurazione di gioco, poi chiami il nostro
   `rounds/open`. Se rispondiamo `402 insufficient_funds`, la partita non
   parte. Se va bene, ricevi `platform_round_id`: legalo alla tua round
   tecnica.
4. **Gioco.** Le azioni di gioco (reveal e simili) restano tra frontend e
   tuo backend: **nessuna chiamata al wallet** durante la partita.
5. **Chiusura.** Calcoli l'esito e il payout finale e chiami il nostro
   `rounds/settle` con il `platform_round_id` della round. Noi registriamo e
   rispondiamo con `ledger_transaction_id`.

## 5. Regole che non si negoziano

- Il tuo backend **non scrive mai** su saldi o ledger: passa tutto da
  `rounds/open` e `rounds/settle`.
- Idempotenza obbligatoria: stessa chiave + stesso payload = stessa risposta;
  stessa chiave + payload diverso → `409 idempotency_conflict`; secondo settle
  con esito diverso → `409 round_already_settled`.
- Importi come stringhe decimali; valuta `CHIP` (MVP).
- Il payout che dichiari in `settle` e' il payout finale teorico della round:
  deve essere determinato dalle tue regole di gioco, non dal saldo del player.

## 6. Errori

Gestisci l'envelope e i codici del Contratto (sez. 7): `invalid_token` /
`token_expired` al lancio, `insufficient_funds` su open, `round_not_found` e
`round_already_settled` su settle, `idempotency_conflict` su chiavi riusate.

## 7. Checklist di go-live

- [ ] `game-launch/validate` attivo e conforme (verifica firma, TTL, monouso)
- [ ] Nessun campo finanziario nelle API pubbliche del gioco
- [ ] `rounds/open` chiamato una sola volta per puntata accettata, con chiave
      di idempotenza nuova
- [ ] `rounds/settle` chiamato esattamente una volta per round (retry sicuri
      con stessa chiave)
- [ ] Test: saldo insufficiente → partita non avviata
- [ ] Test: retry di settle → nessun doppio accredito
