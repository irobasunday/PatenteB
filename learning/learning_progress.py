
"""
Patente B - Persistent Argomenti learning progress.

Optimized PostgreSQL queries.
Preserves accumulated mastery across quiz attempts.
"""

from psycopg.rows import dict_row

from database import get_connection


# ==========================================
# CREATE PROGRESS TABLE
# ==========================================

def ensure_progress_table():
    """
    Ensure the existing progress table exists.

    Called when saving progress, not every
    time the Argomenti page loads.
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                learning_question_progress (
                    browser_id UUID NOT NULL,
                    question_id BIGINT NOT NULL
                        REFERENCES questions(id),
                    mastered_at TIMESTAMPTZ
                        NOT NULL DEFAULT NOW(),

                    PRIMARY KEY (
                        browser_id,
                        question_id
                    )
                )
                """
            )


# ==========================================
# SAVE CORRECT ANSWERS
# ==========================================

def save_quiz_progress(
    browser_id,
    subtopic_id,
    answers,
):
    """
    Save correctly answered questions.

    Previously mastered questions are never
    removed when answered incorrectly later.
    """

    if not browser_id:
        raise ValueError(
            "A confirmed browser ID is required."
        )

    ensure_progress_table()

    correct_count = 0
    mastered_ids = []

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:

            cur.execute(
                """
                SELECT id, correct_answer
                FROM questions
                WHERE subtopic_id = %s
                """,
                (subtopic_id,)
            )

            questions = cur.fetchall()

            for question in questions:
                question_id = question["id"]
                correct_answer = question["correct_answer"]

                selected_answer = answers.get(
                    question_id
                )

                if type(selected_answer) is not bool:
                    continue

                if selected_answer != correct_answer:
                    continue

                correct_count += 1
                mastered_ids.append(question_id)

            # Save all correct answers in one query.
            if mastered_ids:
                cur.execute(
                    """
                    INSERT INTO learning_question_progress (
                        browser_id,
                        question_id
                    )
                    SELECT
                        %s::uuid,
                        question_id
                    FROM UNNEST(%s::bigint[])
                        AS question_id
                    ON CONFLICT (
                        browser_id,
                        question_id
                    )
                    DO NOTHING
                    """,
                    (
                        browser_id,
                        mastered_ids,
                    )
                )

    return {
        "correct": correct_count,
        "total": len(questions),
    }


# ==========================================
# ALL CHAPTER PROGRESS - ONE QUERY
# ==========================================

def get_all_category_progress(browser_id):
    """
    Retrieve mastery percentages for all chapters
    using one PostgreSQL query.

    Returns:
        {category_id: percentage}
    """

    if not browser_id:
        return {}

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:

            cur.execute(
                """
                SELECT
                    s.category_id,

                    COUNT(q.id) AS total,

                    COUNT(p.question_id) AS mastered

                FROM questions q

                JOIN subtopics s
                    ON s.id = q.subtopic_id

                LEFT JOIN learning_question_progress p
                    ON p.question_id = q.id
                    AND p.browser_id = %s

                GROUP BY s.category_id
                """,
                (browser_id,)
            )

            rows = cur.fetchall()

    progress = {}

    for row in rows:
        total = row["total"]
        mastered = row["mastered"]

        progress[row["category_id"]] = (
            round(mastered * 100 / total)
            if total > 0
            else 0
        )

    return progress


# ==========================================
# SINGLE CHAPTER PROGRESS
# ==========================================

def get_category_progress(
    browser_id,
    category_id,
):
    """
    Compatibility function for existing callers.
    """

    if not browser_id:
        return 0

    return get_all_category_progress(
        browser_id
    ).get(category_id, 0)


# ==========================================
# ALL SUBTOPIC COMPLETION - ONE QUERY
# ==========================================

def get_all_subtopic_completed(
    browser_id,
    category_id,
):
    """
    Retrieve completion status for every subtopic
    in a chapter using one PostgreSQL query.

    Returns:
        {subtopic_id: True/False}
    """

    if not browser_id:
        return {}

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:

            cur.execute(
                """
                SELECT
                    s.id AS subtopic_id,

                    COUNT(q.id) AS total,

                    COUNT(p.question_id) AS mastered

                FROM subtopics s

                LEFT JOIN questions q
                    ON q.subtopic_id = s.id

                LEFT JOIN learning_question_progress p
                    ON p.question_id = q.id
                    AND p.browser_id = %s

                WHERE s.category_id = %s

                GROUP BY s.id
                """,
                (
                    browser_id,
                    category_id,
                )
            )

            rows = cur.fetchall()

    return {
        row["subtopic_id"]: (
            row["total"] > 0
            and row["mastered"] == row["total"]
        )
        for row in rows
    }


# ==========================================
# SINGLE SUBTOPIC COMPLETION
# ==========================================

def get_subtopic_completed(
    browser_id,
    subtopic_id,
):
    """
    Compatibility function for existing callers.
    """

    if not browser_id:
        return False

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:

            cur.execute(
                """
                SELECT
                    COUNT(q.id) AS total,
                    COUNT(p.question_id) AS mastered

                FROM questions q

                LEFT JOIN learning_question_progress p
                    ON p.question_id = q.id
                    AND p.browser_id = %s

                WHERE q.subtopic_id = %s
                """,
                (
                    browser_id,
                    subtopic_id,
                )
            )

            result = cur.fetchone()

    return (
        result["total"] > 0
        and result["mastered"] == result["total"]
    )
