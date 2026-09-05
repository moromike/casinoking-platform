# Resoconto Confronto Tecnico con Codex (POR-08)

A seguito dell'esito del censimento POR-00 (in cui è emerso che `PlatformGameAdapter` non possiede un'operazione contabile nativa di `rollback_round`), ho ingaggiato Codex per validare una soluzione tecnica prima di aggiornare il contratto e i documenti, come da istruzioni di Michele.

## Sintesi della sfida tecnica
Ho proposto a Codex di aggiungere un metodo `rollback_round` in `PlatformGameAdapter` e `cancel_game_round` in `rounds/service.py`, che cercasse il round in `platform_rounds`, creasse una transazione di rollback, rimborsasse il `bet_amount` sul ledger e impostasse il round a `cancelled`.

## Riscontro di Codex
Codex ha validato la direzione, confermando che la lacuna è reale e `force_cancel_platform_round` non è usabile a tale scopo. Ha prescritto i seguenti vincoli tecnici vincolanti per l'implementazione:

1. **Locking Corretto**: Cercare il round con `FOR UPDATE OF pr, wa` **prima** di validare lo stato (`status == 'active'`). Non usare un `UPDATE ... WHERE status='active'` ignorando il count delle righe.
2. **Scrittura sul Ledger**: Il rimborso deve avvenire esclusivamente chiamando `registra_movimento()` (l'unico punto autorizzato). Non si devono scrivere direttamente le tabelle `ledger_transactions` e `ledger_entries` per rispettare il vincolo POR-01.
3. **Metadati della transazione**: Usare `transaction_type='rollback'`, `reference_type='game_session'`, e includere nel metadata il provider, round, chiave esterna e impronta della richiesta.
4. **Idempotenza e Fingerprint**: Usare una chiave di idempotenza namespaced specifica per il rollback (es: `{provider_code}:rollback:{user_id}:{provider_transaction_id}`). In caso di collisione:
    * Stessa chiave + stesso payload -> restituisce esito della prima richiesta.
    * Stessa chiave + payload diverso -> conflitto.
    * Tentativo di rollback su round già chiuso -> rifiuto, saldo invariato.
5. **Legame con il Fornitore (POR-02)**: Il lookup non può avvenire solo per `game_round_ref`, ma deve validare l'appartenenza al fornitore aggiungendo `provider_id` su `platform_rounds` (come previsto per POR-02).
6. **Collaudi Specifici**: Deve essere creata una suite per testare: rollback riuscito, retry identico, retry divergente, rollback dopo commit, rollback da altro provider.

## Esito
La soluzione validata da Codex è diventata formalmente il nuovo vincolo di prodotto **POR-08**, che ho inserito in `CONTRATTO_FASE_9.md`. Questo risolve il punto cieco della Fase 9.
