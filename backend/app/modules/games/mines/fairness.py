from datetime import datetime
from hashlib import sha256
from uuid import uuid4

import psycopg

from app.core.config import settings
from app.db.connection import db_connection
from app.modules.games.mines.randomness import build_server_seed_hash, generate_board
from app.modules.games.mines.runtime import FAIRNESS_VERSION, RUNTIME_FILE_NAME
import secrets

FAIRNESS_PHASE = "B"
RANDOM_SOURCE = "internal_seed_engine"
GAME_CODE = "mines"


class FairnessIdempotencyConflictError(Exception):
    pass


def create_fairness_artifacts(
    *,
    cursor: psycopg.Cursor,
    grid_size: int,
    mine_count: int,
    nonce: int,
) -> dict[str, object]:
    active_seed = _get_or_create_active_seed(cursor=cursor)
    server_seed = str(active_seed["server_seed"])
    server_seed_hash = str(active_seed["server_seed_hash"])

    mine_positions, rng_material, board_hash = generate_board(
        grid_size=grid_size,
        mine_count=mine_count,
        fairness_version=FAIRNESS_VERSION,
        server_seed=server_seed,
        nonce=nonce,
    )
    return {
        "fairness_version": FAIRNESS_VERSION,
        "nonce": nonce,
        "server_seed_hash": server_seed_hash,
        "mine_positions": mine_positions,
        "rng_material": rng_material,
        "board_hash": board_hash,
    }


def get_current_fairness_config() -> dict[str, object]:
    active_seed = get_active_fairness_seed()
    return {
        "game_code": GAME_CODE,
        "fairness_version": FAIRNESS_VERSION,
        "fairness_phase": FAIRNESS_PHASE,
        "random_source": RANDOM_SOURCE,
        "board_hash_persisted": True,
        "server_seed_hash_persisted": True,
        "active_server_seed_hash": active_seed["server_seed_hash"],
        "seed_activated_at": active_seed["activated_at"],
        "user_verifiable": False,
        "payout_runtime_file": RUNTIME_FILE_NAME,
    }


def verify_session_fairness_for_admin(*, session_id: str) -> dict[str, object] | None:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    pr.id,
                    pr.status,
                    mgr.grid_size,
                    mgr.mine_count,
                    mgr.fairness_version,
                    mgr.nonce,
                    mgr.server_seed_hash,
                    mgr.board_hash,
                    mgr.mine_positions_json,
                    fsr.server_seed,
                    fsr.server_seed_hash AS rotation_server_seed_hash
                FROM mines_game_rounds mgr
                JOIN platform_rounds pr
                  ON mgr.platform_round_id = pr.id
                JOIN fairness_seed_rotations fsr
                  ON fsr.server_seed_hash = mgr.server_seed_hash
                WHERE pr.id = %s
                """,
                (session_id,),
            )
            row = cursor.fetchone()

    if row is None:
        return None

    expected_server_seed_hash = build_server_seed_hash(str(row["server_seed"]))
    expected_mine_positions, expected_rng_material, expected_board_hash = generate_board(
        grid_size=row["grid_size"],
        mine_count=row["mine_count"],
        fairness_version=row["fairness_version"],
        server_seed=str(row["server_seed"]),
        nonce=row["nonce"],
    )

    stored_mine_positions = sorted(row["mine_positions_json"])
    computed_mine_positions = sorted(expected_mine_positions)

    return {
        "game_session_id": str(row["id"]),
        "status": row["status"],
        "fairness_version": row["fairness_version"],
        "nonce": row["nonce"],
        "stored_server_seed_hash": row["server_seed_hash"],
        "computed_server_seed_hash": expected_server_seed_hash,
        "stored_board_hash": row["board_hash"],
        "computed_board_hash": expected_board_hash,
        "stored_mine_positions": stored_mine_positions,
        "computed_mine_positions": computed_mine_positions,
        "rng_material": expected_rng_material,
        "server_seed_hash_match": row["server_seed_hash"] == expected_server_seed_hash,
        "board_hash_match": row["board_hash"] == expected_board_hash,
        "mine_positions_match": stored_mine_positions == computed_mine_positions,
        "verified": (
            row["server_seed_hash"] == expected_server_seed_hash
            and row["board_hash"] == expected_board_hash
            and stored_mine_positions == computed_mine_positions
        ),
    }


def get_active_fairness_seed() -> dict[str, object]:
    with db_connection() as connection:
        with connection.cursor() as cursor:
            row = _get_or_create_active_seed(cursor=cursor)
    return {
        "id": str(row["id"]),
        "fairness_version": row["fairness_version"],
        "server_seed_hash": row["server_seed_hash"],
        "activated_at": row["activated_at"].isoformat(),
    }


def rotate_active_fairness_seed(
    *,
    admin_user_id: str,
    idempotency_key: str,
) -> dict[str, object]:
    namespaced_idempotency_key = _build_rotation_idempotency_key(
        admin_user_id=admin_user_id,
        client_idempotency_key=idempotency_key,
    )

    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                existing_rotation = _get_rotation_by_idempotency_key(
                    cursor=cursor,
                    idempotency_key=namespaced_idempotency_key,
                )
                if existing_rotation is not None:
                    return _serialize_rotation_response(existing_rotation)

                previous_active_seed = _get_or_create_active_seed(
                    cursor=cursor,
                    for_update=True,
                )
                existing_rotation = _get_rotation_by_idempotency_key(
                    cursor=cursor,
                    idempotency_key=namespaced_idempotency_key,
                )
                if existing_rotation is not None:
                    return _serialize_rotation_response(existing_rotation)

                activated_at = _mark_previous_seed_retired_and_build_activation_time(
                    cursor=cursor,
                    previous_active_seed_id=str(previous_active_seed["id"]),
                )
                new_server_seed = secrets.token_hex(32)
                new_server_seed_hash = build_server_seed_hash(new_server_seed)
                new_rotation_id = str(uuid4())

                cursor.execute(
                    """
                    INSERT INTO fairness_seed_rotations (
                        id,
                        game_code,
                        fairness_version,
                        server_seed,
                        server_seed_hash,
                        status,
                        rotated_by_admin_user_id,
                        idempotency_key,
                        activated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        new_rotation_id,
                        GAME_CODE,
                        FAIRNESS_VERSION,
                        new_server_seed,
                        new_server_seed_hash,
                        "active",
                        admin_user_id,
                        namespaced_idempotency_key,
                        activated_at,
                    ),
                )

                return {
                    "game_code": GAME_CODE,
                    "fairness_version": FAIRNESS_VERSION,
                    "previous_server_seed_hash": str(previous_active_seed["server_seed_hash"]),
                    "active_server_seed_hash": new_server_seed_hash,
                    "activated_at": activated_at.isoformat(),
                }
    except psycopg.errors.UniqueViolation as exc:
        if exc.diag.constraint_name == "fairness_seed_rotations_idempotency_key_key":
            with db_connection() as connection:
                with connection.cursor() as cursor:
                    existing_rotation = _get_rotation_by_idempotency_key(
                        cursor=cursor,
                        idempotency_key=namespaced_idempotency_key,
                    )
                    if existing_rotation is not None:
                        return _serialize_rotation_response(existing_rotation)
        raise FairnessIdempotencyConflictError(
            "Idempotency key already used with a different payload"
        ) from exc


def _get_or_create_active_seed(
    *,
    cursor: psycopg.Cursor,
    for_update: bool = False,
) -> dict[str, object]:
    cursor.execute(
        f"""
        SELECT
            id,
            fairness_version,
            server_seed,
            server_seed_hash,
            activated_at
        FROM fairness_seed_rotations
        WHERE game_code = %s
          AND status = 'active'
        {"FOR UPDATE" if for_update else ""}
        """,
        (GAME_CODE,),
    )
    row = cursor.fetchone()
    if row is not None:
        return row

    bootstrap_seed = settings.mines_server_seed
    bootstrap_seed_hash = build_server_seed_hash(bootstrap_seed)
    bootstrap_id = str(uuid4())

    cursor.execute(
        """
        INSERT INTO fairness_seed_rotations (
            id,
            game_code,
            fairness_version,
            server_seed,
            server_seed_hash,
            status,
            activated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, now())
        ON CONFLICT DO NOTHING
        """,
        (
            bootstrap_id,
            GAME_CODE,
            FAIRNESS_VERSION,
            bootstrap_seed,
            bootstrap_seed_hash,
            "active",
        ),
    )
    if cursor.rowcount == 0:
        cursor.execute(
            """
            SELECT
                id,
                fairness_version,
                server_seed,
                server_seed_hash,
                activated_at
            FROM fairness_seed_rotations
            WHERE game_code = %s
              AND status = 'active'
            """,
            (GAME_CODE,),
        )
        row = cursor.fetchone()
        assert row is not None
        return row
    cursor.execute(
        """
        SELECT
            id,
            fairness_version,
            server_seed,
            server_seed_hash,
            activated_at
        FROM fairness_seed_rotations
        WHERE id = %s
        """,
        (bootstrap_id,),
    )
    row = cursor.fetchone()
    assert row is not None
    return row


def _mark_previous_seed_retired_and_build_activation_time(
    *,
    cursor: psycopg.Cursor,
    previous_active_seed_id: str,
) -> datetime:
    cursor.execute(
        """
        UPDATE fairness_seed_rotations
        SET
            status = 'retired',
            retired_at = now()
        WHERE id = %s
        RETURNING retired_at
        """,
        (previous_active_seed_id,),
    )
    row = cursor.fetchone()
    assert row is not None
    return row["retired_at"]


def _get_rotation_by_idempotency_key(
    *,
    cursor: psycopg.Cursor,
    idempotency_key: str,
) -> dict[str, object] | None:
    cursor.execute(
        """
        SELECT
            fsr.id,
            fsr.game_code,
            fsr.fairness_version,
            fsr.server_seed_hash,
            fsr.activated_at,
            fsr.idempotency_key,
            (
                SELECT prev.server_seed_hash
                FROM fairness_seed_rotations prev
                WHERE prev.game_code = fsr.game_code
                  AND prev.retired_at = fsr.activated_at
                ORDER BY prev.created_at DESC
                LIMIT 1
            ) AS previous_server_seed_hash
        FROM fairness_seed_rotations fsr
        WHERE fsr.idempotency_key = %s
        """,
        (idempotency_key,),
    )
    return cursor.fetchone()


def _serialize_rotation_response(row: dict[str, object]) -> dict[str, object]:
    return {
        "game_code": row["game_code"],
        "fairness_version": row["fairness_version"],
        "previous_server_seed_hash": row["previous_server_seed_hash"],
        "active_server_seed_hash": row["server_seed_hash"],
        "activated_at": row["activated_at"].isoformat(),
    }


def _build_rotation_idempotency_key(
    *,
    admin_user_id: str,
    client_idempotency_key: str,
) -> str:
    raw_key = f"mines:fairness:rotate:{admin_user_id}:{client_idempotency_key.strip()}"
    return f"mines:fairness:rotate:{sha256(raw_key.encode('utf-8')).hexdigest()}"
