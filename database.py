
import os
import psycopg
import streamlit as st
from dotenv import load_dotenv
import os
import time
import logging
database_url = os.getenv("DATABASE_URL")
from psycopg_pool import ConnectionPool
from contextlib import contextmanager
load_dotenv()



# =========================================
# DATABASE CONNECTION
# =========================================

def get_database_url():
    """Read the existing PostgreSQL connection URL."""

    try:
        url = st.secrets.get("DATABASE_URL")
        if url:
            return url
    except (FileNotFoundError, KeyError):
        pass

    return os.getenv("DATABASE_URL")



@st.cache_resource
def get_connection_pool(database_url):
    """Create one reusable PostgreSQL connection pool."""
    return ConnectionPool(
        conninfo=database_url,
        min_size=0,
        max_size=5,
        open=True,
        kwargs={"autocommit": True},
    )



@contextmanager
def get_connection():
    """Borrow a PostgreSQL connection from the pool."""

    database_url = get_database_url()

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing. "
            "Check your .env or Streamlit secrets."
        )

    pool = get_connection_pool(database_url)

    with pool.connection() as conn:
        yield conn

# =========================================
# FETCH 30 RANDOM QUESTIONS
# =========================================

def fetch_quiz_questions():
    """
    Select 30 questions:
    - One random question from each of 25 chapters
    - Five additional random questions
    - No duplicate questions
    - Shuffle the final result
    """

    query = """
        WITH ranked_questions AS (
            SELECT
                q.id,
                q.question,
                q.correct_answer,
                q.image_path,
                q.subtopic_id,
                s.category_id AS chapter_id,
                c.name AS chapter_name,
                ROW_NUMBER() OVER (
                    PARTITION BY c.id
                    ORDER BY RANDOM()
                ) AS random_rank
            FROM questions q
            JOIN subtopics s
                ON q.subtopic_id = s.id
            JOIN categories c
                ON s.category_id = c.id
        ),
        first_25 AS (
            SELECT
                id,
                question,
                correct_answer,
                image_path,
                subtopic_id,
                chapter_id,
                chapter_name
            FROM ranked_questions
            WHERE random_rank = 1
        ),
        extra_5 AS (
            SELECT
                q.id,
                q.question,
                q.correct_answer,
                q.image_path,
                q.subtopic_id,
                s.category_id AS chapter_id,
                c.name AS chapter_name
            FROM questions q
            JOIN subtopics s
                ON q.subtopic_id = s.id
            JOIN categories c
                ON s.category_id = c.id
            WHERE q.id NOT IN (
                SELECT id FROM first_25
            )
            ORDER BY RANDOM()
            LIMIT 5
        )
        SELECT *
        FROM (
            SELECT * FROM first_25
            UNION ALL
            SELECT * FROM extra_5
        ) AS selected_questions
        ORDER BY RANDOM();
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)

            column_names = [
                column.name
                for column in cur.description
            ]

            rows = cur.fetchall()

    questions = [
        dict(zip(column_names, row))
        for row in rows
    ]

    if len(questions) != 30:
        raise ValueError(
            f"Expected 30 questions, "
            f"but received {len(questions)}."
        )

    chapter_ids = {
        question["chapter_id"]
        for question in questions
    }

    if len(chapter_ids) != 25:
        raise ValueError(
            "The selected questions do not "
            "cover all 25 chapters."
        )

    return questions

# =========================================
# SAVED ENGLISH TRANSLATIONS
# =========================================



def get_saved_translation(question_id):
    """Retrieve an existing English translation."""

    start = time.perf_counter()

    with get_connection() as conn:
        connection_time = time.perf_counter()

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT english_text
                FROM question_translations
                WHERE question_id = %s
                """,
                (question_id,)
            )

            row = cur.fetchone()

        query_time = time.perf_counter()

    finished_time = time.perf_counter()

    logging.warning(
        "DB DIAGNOSTIC | Connection: %.3f seconds",
        connection_time - start
    )

    logging.warning(
        "DB DIAGNOSTIC | SQL: %.3f seconds",
        query_time - connection_time
    )

    logging.warning(
        "DB DIAGNOSTIC | Transaction/return: %.3f seconds",
        finished_time - query_time
    )

    return row[0] if row else None

    """Retrieve an existing English translation."""

    start = time.perf_counter()

    with get_connection() as conn:
        connection_time = time.perf_counter()

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT english_text
                FROM question_translations
                WHERE question_id = %s
                """,
                (question_id,)
            )

            row = cur.fetchone()

        query_time = time.perf_counter()

    logging.warning(
        "DB DIAGNOSTIC | Lookup connection: %.3f seconds",
        connection_time - start
    )

    logging.warning(
        "DB DIAGNOSTIC | Lookup SQL: %.3f seconds",
        query_time - connection_time
    )

    return row[0] if row else None

    """Retrieve an existing English translation."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT english_text
                FROM question_translations
                WHERE question_id = %s
                """,
                (question_id,)
            )

            row = cur.fetchone()

    return row[0] if row else None


def save_translation(question_id, english_text):
    """Permanently save a successful translation."""

    if not english_text or not english_text.strip():
        return

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO question_translations
                    (question_id, english_text)
                VALUES (%s, %s)
                ON CONFLICT (question_id) DO NOTHING
                """,
                (question_id, english_text.strip())
            )


def get_or_create_translation(question_id, italian_text):
    """
    Retrieve a saved translation, or translate and save it.
    Measure the time taken by each operation.
    """

    from translator import translate_to_english

    total_start = time.perf_counter()

    # STEP 1: Check PostgreSQL
    start = time.perf_counter()

    saved_text = get_saved_translation(question_id)

    logging.warning(
        "TRANSLATION SPEED | PostgreSQL lookup: %.2f seconds",
        time.perf_counter() - start
    )

    if saved_text:
        logging.warning(
            "TRANSLATION SPEED | Total (saved): %.2f seconds",
            time.perf_counter() - total_start
        )
        return saved_text

    # STEP 2: Translate with MyMemory
    start = time.perf_counter()

    english_text = translate_to_english(italian_text)

    logging.warning(
        "TRANSLATION SPEED | MyMemory: %.2f seconds",
        time.perf_counter() - start
    )

    if not english_text or not english_text.strip():
        return ""

    # STEP 3: Save to PostgreSQL
    start = time.perf_counter()

    save_translation(question_id, english_text)

    logging.warning(
        "TRANSLATION SPEED | PostgreSQL save: %.2f seconds",
        time.perf_counter() - start
    )

    logging.warning(
        "TRANSLATION SPEED | Total (new): %.2f seconds",
        time.perf_counter() - total_start
    )

    return english_text
