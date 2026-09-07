Status: ACTIVE
Last meaningful update: 2026-09-04

# INT-04 — Manuale di integrazione lato Provider (i giochi)

**Per chi**: un operatore esterno (piattaforma/aggregatore) che vuole integrare
i giochi m&m games (primo titolo: Mines) sul proprio sito, con il **proprio**
wallet.

**Modello**: seamless wallet. Il denaro resta sempre e solo presso l'operatore;
il gioco non vede mai il saldo e non muove mai denaro direttamente: ogni
giocata e' una chiamata verso il wallet dell'operatore.

Riferimento vincolante: `documenti/CONTRATTO-API-SEAMLESS-WALLET-v1.md`
(da qui in poi «il Contratto»). In caso di dubbio, vale il Contratto.

## 1. Chi fa cosa

| Responsabilita' | Operatore (tu) | Provider giochi (noi) |
| --- | --- | --- |
| Autenticazione player | ✔ | — |
| Wallet, saldi, ledger | ✔ | — |
| Emissione `game_launch_token` | ✔ | — |
| Verifica saldo e debit puntata | ✔ (via `rounds/open`) | — |
| RNG, fairness, board, reveal | — | ✔ |
| Calcolo payout della round | — | ✔ |
| Accredito vincita | ✔ (via `rounds/settle`) | — |

## 2. Cosa devi esporre tu (operatore)

Devi implementare, raggiungibili dal nostro backend gioco via HTTPS con
`Authorization: Bearer <service_token>` che ci rilasci:

1. `POST /internal/v1/seamless-wallet/rounds/open` — apre la round
   finanziaria: verifica saldo, debita la puntata, risponde con
   `platform_round_id`. Deve essere **idempotente** su `idempotency_key`.
2. `POST /internal/v1/seamless-wallet/rounds/settle` — chiude la round con
   `outcome` = `won` (accredita `payout_amount`) o `lost` (nessun accredito).
   Idempotente; una round regolata non puo' cambiare esito.
3. (Opzionale v1) `POST /internal/v1/seamless-wallet/play-sessions/close` —
   chiusura della presenza del player nel gioco.

Devi inoltre:

- emettere il `game_launch_token` (JWT con i claim minimi del Contratto,
  sez. 2.1: `sub`, `platform_session_id`, `play_session_id`, `game_code`,
  `iat`, `exp`, `nonce`; TTL <= 5 minuti, monouso), firmato con una chiave che
  ci condividi per la verifica;
- rispondere agli errori con l'envelope e i codici del Contratto (sez. 7):
  in particolare `402 insufficient_funds` su `rounds/open` e
  `409 idempotency_conflict`.

## 3. Cosa ricevi da noi (provider)

- Il **backend gioco**, che espone `POST /internal/v1/game-launch/validate`
  (valida il token e apre la sessione tecnica) e le API pubbliche di gioco
  (`GET /games/{game}/config`, `POST /games/{game}/reveal`,
  `GET /games/{game}/session/{id}`, fairness).
- Il **frontend gioco** embeddabile, a cui passi il `game_launch_token`
  al lancio.

## 4. Flusso completo, passo per passo

1. **Lancio.** Autentichi il player, crei la `play_session`, emetti il
   `game_launch_token` e apri il frontend gioco con quel token.
2. **Validazione.** Il frontend chiama il nostro `game-launch/validate`;
   noi verifichiamo firma, scadenza e `game_code`, e apriamo la sessione
   tecnica.
3. **Puntata.** Il player punta; noi validiamo la configurazione di gioco e
   chiamiamo **il tuo** `rounds/open` con `idempotency_key` nuova. Se rispondi
   `402`, la partita non parte e il player vede «saldo insufficiente».
4. **Gioco.** I reveal avvengono solo tra frontend e nostro backend:
   **nessuna chiamata al tuo wallet** durante la partita.
5. **Chiusura.** A round finita chiamiamo il tuo `rounds/settle`:
   `outcome=won` con `payout_amount` se il player incassa, `outcome=lost` con
   `payout_amount=0` se perde. Tu registri e chiudi.
6. **Uscita.** (Opzionale) notifichiamo `play-sessions/close`.

## 5. Regole che non si negoziano

- Mai scritture finanziarie fuori da `rounds/open` e `rounds/settle`.
- Mai riutilizzare una `idempotency_key` con payload diverso: riceverai
  `409 idempotency_conflict` (e anche noi ci comportiamo cosi' verso di te).
- Importi sempre come stringhe decimali; valuta concordata in onboarding
  (MVP: `CHIP`).
- Il `game_launch_token` non autorizza nient'altro che il lancio del gioco.

## 6. Riconciliazione

Ogni round regolata riporta `platform_round_id` e `ledger_transaction_id`
(nella response di `settle`): sono le chiavi per la riconciliazione
contabile tra i tuoi movimenti e le nostre sessioni di gioco.

## 7. Checklist di go-live

- [ ] Endpoint `rounds/open` e `rounds/settle` attivi, idempotenti, con
      envelope errori del Contratto
- [ ] Emissione `game_launch_token` conforme (claim, TTL, monouso)
- [ ] Scambio credenziali: service token (tu → noi) e chiave di firma token
- [ ] Test: puntata con saldo insufficiente → `402`
- [ ] Test: doppio `settle` stessa chiave → stessa risposta, nessun doppio
      accredito
- [ ] Test: doppio `settle` con esito diverso → `409 round_already_settled`
