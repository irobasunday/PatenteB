
import os

import psycopg
import streamlit as st
from psycopg.rows import dict_row


def get_database_url():
    """Read the existing PostgreSQL connection URL."""

    try:
        url = st.secrets.get("DATABASE_URL")
        if url:
            return url
    except Exception:
        pass

    return os.getenv("DATABASE_URL")


@st.cache_data(ttl=300, show_spinner=False)
def get_learning_questions(subtopic_id):
    """
    Fetch questions belonging to one subtopic.

    Returns:
        vero_questions
        falso_questions
    """

    database_url = get_database_url()

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing from Streamlit "
            "secrets or environment variables."
        )

    with psycopg.connect(
        database_url,
        row_factory=dict_row,
    ) as conn:

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    question,
                    correct_answer,
                    image_path,
                    subtopic_id
                FROM questions
                WHERE subtopic_id = %s
                ORDER BY id
                """,
                (subtopic_id,),
            )

            questions = cur.fetchall()

    vero_questions = [
        question
        for question in questions
        if question["correct_answer"] is True
    ]

    falso_questions = [
        question
        for question in questions
        if question["correct_answer"] is False
    ]

    return vero_questions, falso_questions
