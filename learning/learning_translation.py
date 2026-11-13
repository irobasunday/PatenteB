
import os

import psycopg
import requests
import streamlit as st
from psycopg.rows import dict_row


def get_database_url():
    """Get the existing PostgreSQL connection URL."""

    try:
        url = st.secrets.get("DATABASE_URL")
        if url:
            return url
    except Exception:
        pass

    return os.getenv("DATABASE_URL")


def get_saved_translation(question_id):
    """Return an existing English translation, if available."""

    database_url = get_database_url()

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing.")

    with psycopg.connect(
        database_url,
        row_factory=dict_row,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT english_text
                FROM question_translations
                WHERE question_id = %s
                LIMIT 1
                """,
                (question_id,),
            )

            result = cur.fetchone()

    if result and result["english_text"]:
        return result["english_text"].strip()

    return None


def generate_translation(italian_text):
    """Translate Italian text into English using MyMemory."""

    if not italian_text or not italian_text.strip():
        return None

    try:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={
                "q": italian_text,
                "langpair": "it|en",
            },
            timeout=15,
        )

        response.raise_for_status()
        data = response.json()

        if data.get("responseStatus") != 200:
            return None

        translated_text = (
            data.get("responseData", {})
            .get("translatedText", "")
            .strip()
        )

        if not translated_text:
            return None

        return translated_text

    except (requests.RequestException, ValueError, AttributeError):
        return None


def save_translation(question_id, english_text):
    """Save a successful translation for future use."""

    if not english_text or not english_text.strip():
        return False

    database_url = get_database_url()

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing.")

    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:

            # Avoid inserting a duplicate translation.
            cur.execute(
                """
                SELECT 1
                FROM question_translations
                WHERE question_id = %s
                LIMIT 1
                """,
                (question_id,),
            )

            if cur.fetchone():
                return True

            cur.execute(
                """
                INSERT INTO question_translations (
                    question_id,
                    english_text
                )
                VALUES (%s, %s)
                """,
                (question_id, english_text.strip()),
            )

        conn.commit()

    return True


def get_or_create_translation(question_id, italian_text):
    """
    Translation workflow:

    1. Check PostgreSQL.
    2. Reuse an existing translation.
    3. Generate only if missing.
    4. Save successful new translations.
    """

    saved = get_saved_translation(question_id)

    if saved:
        return saved

    translated = generate_translation(italian_text)

    if not translated:
        return None

    save_translation(question_id, translated)

    return translated
