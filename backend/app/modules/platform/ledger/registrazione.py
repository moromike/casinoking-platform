"""Registrazione unica dei movimenti in partita doppia (CON-01).

Prima di questo modulo i cinque punti che scrivono il ledger
(``platform/rounds/service.py`` apertura/vincita, ``auth/service.py``
credito iniziale, ``admin/session_force_close.py`` void,
``admin/service.py`` bonus/adjustment) ripetevano a mano la stessa
tripla scrittura: ``ledger_transactions``, ``ledger_entries`` e
aggiornamento dello snapshot in ``wallet_accounts``.

``registra_movimento`` e' l'unico punto autorizzato a fare quella
tripla scrittura. Garantisce:

1. Quadratura verificata PRIMA di scrivere: somma dare == somma avere,
   importi positivi e compatibili con numeric(18, 6).
2. Idempotency key obbligatoria: se la chiave esiste gia' la funzione
   non scrive nulla e restituisce la transazione esistente.
3. Coerenza snapshot: gli aggiornamenti di ``wallet_accounts`` sono
   derivati dalle righe stesse (credit aggiunge, debit sottrae), quindi
   non e' possibile scrivere una scrittura senza aggiornare il saldo
   del portafoglio coinvolto. ``wallet_accounts.ledger_account_id`` e'
   UNIQUE: ogni conto ledger di un giocatore ha al massimo un wallet.
   I conti di sistema (HOUSE_*, PROMO_RESERVE, ...) non hanno wallet e
   non producono aggiornamenti.

NOTA SUI LOCK: la funzione esegue UPDATE secche sulle wallet coinvolte
(che acquisiscono il row lock), ma NON rilegge i saldi. Se il chiamante
deve validare il saldo prima del movimento (es. puntata) deve aver gia'
bloccato la wallet con SELECT ... FOR UPDATE nella stessa transazione,
come fanno tutti i chiamanti attuali.

NOTA SULLE RACE: il pre-check sull'idempotency key copre i replay
sequenziali. In caso di inserimento concorrente sulla stessa chiave il
vincolo UNIQUE di ``ledger_transactions.idempotency_key`` resta il
backstop e solleva UniqueViolation: la transazione del chiamante va in
rollback e il retry vedra' la chiave esistente.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
from typing import Sequence
from uuid import uuid4

import psycopg

ENTRY_SIDE_DEBIT = "debit"
ENTRY_SIDE_CREDIT = "credit"
VALID_ENTRY_SIDES = frozenset({ENTRY_SIDE_DEBIT, ENTRY_SIDE_CREDIT})
MONEY_QUANTUM = Decimal("0.000001")
IDEMPOTENCY_KEY_CONSTRAINT = "ledger_transactions_idempotency_key_key"


class RegistrazioneValidationError(Exception):
    """Input non valido o scrittura non quadrata: niente e' stato scritto."""


@dataclass(frozen=True)
class RigaScrittura:
    """Una riga di ledger_entries: conto, lato (debit/credit), importo."""

    ledger_account_id: str
    entry_side: str
    amount: Decimal


def registra_movimento(
    *,
    cursor: psycopg.Cursor,
    user_id: str,
    transaction_type: str,
    idempotency_key: str,
    righe: Sequence[RigaScrittura],
    reference_type: str | None = None,
    reference_id: str | None = None,
    metadata: dict[str, object] | None = None,
    transaction_id: str | None = None,
) -> dict[str, object]:
    """Registra un movimento in partita doppia e aggiorna gli snapshot.

    Ritorna ``{"transaction_id": str, "already_exists": bool,
    "wallet_updates": [{"wallet_account_id": str, "balance_after": Decimal}]}``.
    Con ``already_exists=True`` non e' stato scritto nulla e
    ``wallet_updates`` e' vuoto.

    Solleva ``RegistrazioneValidationError`` prima di qualsiasi scrittura
    se l'input non e' valido o la scrittura non quadra.
    """
    normalized_idempotency_key = idempotency_key.strip()
    if not normalized_idempotency_key:
        raise RegistrazioneValidationError("Idempotency key is required")
    if not transaction_type or not transaction_type.strip():
        raise RegistrazioneValidationError("Transaction type is required")
    if not user_id or not str(user_id).strip():
        raise RegistrazioneValidationError("User is required")

    normalized_righe = _validate_righe(righe)

    cursor.execute(
        """
        SELECT id
        FROM ledger_transactions
        WHERE idempotency_key = %s
        """,
        (normalized_idempotency_key,),
    )
    existing_row = cursor.fetchone()
    if existing_row is not None:
        return {
            "transaction_id": str(existing_row["id"]),
            "already_exists": True,
            "wallet_updates": [],
        }

    resolved_transaction_id = transaction_id or str(uuid4())
    cursor.execute(
        """
        INSERT INTO ledger_transactions (
            id,
            user_id,
            transaction_type,
            reference_type,
            reference_id,
            idempotency_key,
            metadata_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
        """,
        (
            resolved_transaction_id,
            user_id,
            transaction_type.strip(),
            reference_type,
            reference_id,
            normalized_idempotency_key,
            json.dumps(metadata or {}, separators=(",", ":"), sort_keys=True),
        ),
    )
    cursor.executemany(
        """
        INSERT INTO ledger_entries (
            id,
            transaction_id,
            ledger_account_id,
            entry_side,
            amount
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        [
            (
                str(uuid4()),
                resolved_transaction_id,
                riga.ledger_account_id,
                riga.entry_side,
                riga.amount,
            )
            for riga in normalized_righe
        ],
    )

    wallet_updates = _apply_wallet_deltas(cursor=cursor, righe=normalized_righe)

    return {
        "transaction_id": resolved_transaction_id,
        "already_exists": False,
        "wallet_updates": wallet_updates,
    }


def _validate_righe(
    righe: Sequence[RigaScrittura],
) -> list[RigaScrittura]:
    """Verifica la quadratura PRIMA di scrivere; normalizza gli importi."""
    if len(righe) < 2:
        raise RegistrazioneValidationError(
            "A double-entry movement requires at least two rows"
        )

    total_debit = Decimal("0")
    total_credit = Decimal("0")
    normalized: list[RigaScrittura] = []
    for riga in righe:
        if riga.entry_side not in VALID_ENTRY_SIDES:
            raise RegistrazioneValidationError(
                f"Entry side is not valid: {riga.entry_side!r}"
            )
        if not riga.ledger_account_id or not str(riga.ledger_account_id).strip():
            raise RegistrazioneValidationError("Ledger account is required")
        amount = Decimal(riga.amount)
        if amount <= 0:
            raise RegistrazioneValidationError("Entry amount must be positive")
        if amount != amount.quantize(MONEY_QUANTUM):
            raise RegistrazioneValidationError(
                "Entry amount has more than 6 decimal places"
            )
        normalized.append(
            RigaScrittura(
                ledger_account_id=str(riga.ledger_account_id),
                entry_side=riga.entry_side,
                amount=amount,
            )
        )
        if riga.entry_side == ENTRY_SIDE_DEBIT:
            total_debit += amount
        else:
            total_credit += amount

    if total_debit != total_credit:
        raise RegistrazioneValidationError(
            f"Unbalanced movement: debit {total_debit} != credit {total_credit}"
        )
    return normalized


def _apply_wallet_deltas(
    *,
    cursor: psycopg.Cursor,
    righe: Sequence[RigaScrittura],
) -> list[dict[str, object]]:
    """Aggiorna gli snapshot dei wallet derivandoli dalle righe.

    Per ogni conto ledger il delta del wallet e' credit - debit. I conti
    senza wallet (conti di sistema) non producono alcun aggiornamento.
    """
    deltas: dict[str, Decimal] = {}
    for riga in righe:
        signed_amount = (
            riga.amount
            if riga.entry_side == ENTRY_SIDE_CREDIT
            else -riga.amount
        )
        deltas[riga.ledger_account_id] = (
            deltas.get(riga.ledger_account_id, Decimal("0")) + signed_amount
        )

    wallet_updates: list[dict[str, object]] = []
    for ledger_account_id, delta in deltas.items():
        if delta == 0:
            continue
        cursor.execute(
            """
            UPDATE wallet_accounts
            SET balance_snapshot = balance_snapshot + %s
            WHERE ledger_account_id = %s
            RETURNING id, balance_snapshot
            """,
            (delta, ledger_account_id),
        )
        wallet_row = cursor.fetchone()
        if wallet_row is not None:
            wallet_updates.append(
                {
                    "wallet_account_id": str(wallet_row["id"]),
                    "balance_after": wallet_row["balance_snapshot"],
                }
            )
    return wallet_updates
