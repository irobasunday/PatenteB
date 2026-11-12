"""PostgreSQL persistence for anonymous Patente B quiz attempts.

Does not change the existing question bank or translation tables.
Call ensure_quiz_attempts_table() once before using the functions.
"""
from datetime import datetime, timezone
from uuid import UUID

from psycopg.types.json import Jsonb
from database import get_connection

MODES = {"quiz", "instant_correction"}


def _identity(browser_id, mode):
    browser_id = str(UUID(str(browser_id)))
    if mode not in MODES:
        raise ValueError(f"Unsupported quiz mode: {mode}")
    return browser_id


def ensure_quiz_attempts_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    browser_id UUID NOT NULL,
                    mode TEXT NOT NULL CHECK (mode IN ('quiz', 'instant_correction')),
                    question_ids JSONB NOT NULL,
                    answers JSONB NOT NULL DEFAULT '{}'::jsonb,
                    question_index INTEGER NOT NULL DEFAULT 0,
                    started_at TIMESTAMPTZ NOT NULL,
                    finished_at TIMESTAMPTZ,
                    status TEXT NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'submitted', 'expired', 'abandoned')),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS uq_quiz_attempts_active_browser_mode
                ON quiz_attempts (browser_id, mode)
                WHERE status = 'active'
            """)


def load_active_attempt(browser_id, mode):
    browser_id = _identity(browser_id, mode)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, question_ids, answers, question_index, started_at,
                       status, finished_at
                FROM quiz_attempts
                WHERE browser_id = %s AND mode = %s AND status = 'active'
                ORDER BY id DESC LIMIT 1
            """, (browser_id, mode))
            row = cur.fetchone()
    if not row:
        return None
    return dict(zip(("id", "question_ids", "answers", "question_index",
                     "started_at", "status", "finished_at"), row))


def start_attempt(browser_id, mode, question_ids, started_at=None):
    browser_id = _identity(browser_id, mode)
    ids = [int(x) for x in question_ids]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("Question IDs must be nonempty and unique")
    started_at = started_at or datetime.now(timezone.utc)
    with get_connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                # Starting fresh explicitly abandons any previous active attempt.
                cur.execute("""
                    UPDATE quiz_attempts SET status='abandoned',
                        finished_at=NOW(), updated_at=NOW()
                    WHERE browser_id=%s AND mode=%s AND status='active'
                """, (browser_id, mode))
                cur.execute("""
                    INSERT INTO quiz_attempts
                        (browser_id, mode, question_ids, started_at)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (browser_id, mode, Jsonb(ids), started_at))
                return cur.fetchone()[0]


def save_progress(attempt_id, browser_id, mode, answers, question_index):
    browser_id = _identity(browser_id, mode)
    normalized_answers = {str(int(k)): bool(v) for k, v in answers.items()}
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE quiz_attempts
                SET answers=%s, question_index=%s, updated_at=NOW()
                WHERE id=%s AND browser_id=%s AND mode=%s AND status='active'
                RETURNING id
            """, (Jsonb(normalized_answers), int(question_index),
                  int(attempt_id), browser_id, mode))
            return cur.fetchone() is not None


def finish_attempt(attempt_id, browser_id, mode, answers, status):
    browser_id = _identity(browser_id, mode)
    if status not in ('submitted', 'expired', 'abandoned'):
        raise ValueError("Invalid finish status")
    normalized_answers = {str(int(k)): bool(v) for k, v in answers.items()}
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE quiz_attempts
                SET answers=%s, status=%s, finished_at=NOW(), updated_at=NOW()
                WHERE id=%s AND browser_id=%s AND mode=%s AND status='active'
                RETURNING id
            """, (Jsonb(normalized_answers), status, int(attempt_id),
                  browser_id, mode))
            return cur.fetchone() is not None

def load_latest_active_attempt(browser_id):
    """
    Load the latest unfinished quiz, regardless
    of whether it is Translate or Instant Correction.

    Uses one PostgreSQL query.
    """
    browser_id = str(UUID(str(browser_id)))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, mode, question_ids, answers,
                       question_index, started_at
                FROM quiz_attempts
                WHERE browser_id = %s
                  AND status = 'active'
                ORDER BY id DESC
                LIMIT 1
                """,
                (browser_id,),
            )

            row = cur.fetchone()

    if row is None:
        return None

    return dict(
        zip(
            (
                "id",
                "mode",
                "question_ids",
                "answers",
                "question_index",
                "started_at",
            ),
            row,
        )
    )

def abandon_active_attempts(browser_id):
    """
    Permanently abandon all unfinished quiz attempts
    for this browser.

    Completed quiz results are not affected.
    """

    from uuid import UUID

    browser_id = str(UUID(str(browser_id)))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE quiz_attempts
                SET status = 'abandoned',
                    finished_at = NOW(),
                    updated_at = NOW()
                WHERE browser_id = %s
                  AND status = 'active'
                """,
                (browser_id,),
            )

            abandoned_count = cur.rowcount

        conn.commit()

    return abandoned_count
