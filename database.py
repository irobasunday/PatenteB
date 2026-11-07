
import os
import psycopg
import streamlit as st
from dotenv import load_dotenv

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


def get_connection():
    """Connect to the existing Neon PostgreSQL database."""

    database_url = get_database_url()

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing. "
            "Check your .env or Streamlit secrets."
        )

    return psycopg.connect(database_url)


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
