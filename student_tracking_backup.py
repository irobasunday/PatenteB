
"""
Patente B - PostgreSQL student identification.
"""

import logging
import uuid

from database import get_connection


def valid_uuid(value):
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return None


def resolve_student(candidate_ids, allow_create=False):
    """
    Recover an existing student from PostgreSQL.

    Create a new student only when the browser identity
    workflow explicitly authorizes registration.
    """

    valid_ids = list(dict.fromkeys(
        student_id
        for value in (candidate_ids or [])
        if (student_id := valid_uuid(value))
    ))

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                if valid_ids:
                    cur.execute(
                        """
                        SELECT browser_id
                        FROM anonymous_students
                        WHERE browser_id = ANY(%s::uuid[])
                        ORDER BY
                            last_seen DESC NULLS LAST,
                            first_seen DESC NULLS LAST,
                            browser_id DESC
                        LIMIT 1
                        """,
                        (valid_ids,)
                    )

                    row = cur.fetchone()

                    if row:
                        student_id = str(row[0])

                        cur.execute(
                            """
                            UPDATE anonymous_students
                            SET last_seen = NOW()
                            WHERE browser_id = %s
                            """,
                            (student_id,)
                        )

                        return student_id, False

                if not allow_create:
                    return None, False

                cur.execute(
                    """
                    INSERT INTO anonymous_students
                        (browser_id, first_seen, last_seen)
                    VALUES
                        (gen_random_uuid(), NOW(), NOW())
                    RETURNING browser_id
                    """
                )

                row = cur.fetchone()

                if not row:
                    return None, False

                return str(row[0]), True

    except Exception:
        logging.exception(
            "Unable to resolve student identity"
        )
        return None, False


def register_student(browser_id):
    """Update an existing student without creating records."""

    student_id = valid_uuid(browser_id)

    if not student_id:
        return False

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE anonymous_students
                    SET last_seen = NOW()
                    WHERE browser_id = %s
                    RETURNING browser_id
                    """,
                    (student_id,)
                )

                return cur.fetchone() is not None

    except Exception:
        logging.exception(
            "Unable to update student visit"
        )
        return False
