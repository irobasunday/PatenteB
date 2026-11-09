
import math
import html
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from database import fetch_quiz_questions
from translator import translate_to_english
from audio_player import show_italian_audio


# =========================================
# QUIZ SETTINGS
# =========================================

TOTAL_QUESTIONS = 30
QUIZ_DURATION_MINUTES = 20
PROJECT_FOLDER = Path(__file__).resolve().parent


# =========================================
# QUIZ STATE
# =========================================

def initialize_quiz():
    """Load 30 questions once and initialize quiz state."""

    if "quiz_questions" not in st.session_state:
        questions = fetch_quiz_questions()

        if len(questions) != TOTAL_QUESTIONS:
            raise ValueError(
                f"Expected {TOTAL_QUESTIONS} questions, "
                f"received {len(questions)}."
            )

        if len({q["id"] for q in questions}) != TOTAL_QUESTIONS:
            raise ValueError(
                "The database returned duplicate question IDs."
            )

        if len({q["chapter_id"] for q in questions}) != 25:
            raise ValueError(
                "The questions do not cover all 25 chapters."
            )

        st.session_state.quiz_questions = questions

    defaults = {
        "quiz_question_index": 0,
        "quiz_answers": {},
        "quiz_finished": False,
        "quiz_completion_prompt_shown": False,
        "quiz_show_completion_dialog": False,
        "quiz_submit_pending": False,
        "quiz_finish_reason": None,
        "quiz_translations_visible": {},
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "quiz_started_at" not in st.session_state:
        st.session_state.quiz_started_at = datetime.now(timezone.utc)


def get_remaining_seconds():
    """Calculate remaining quiz time."""

    elapsed = (
        datetime.now(timezone.utc)
        - st.session_state.quiz_started_at
    ).total_seconds()

    return max(
        0,
        math.ceil(QUIZ_DURATION_MINUTES * 60 - elapsed)
    )


def finish_quiz(reason="time_expired"):
    """Finish the quiz without deleting saved answers."""

    st.session_state.quiz_finished = True
    st.session_state.quiz_finish_reason = reason
    st.session_state.quiz_show_completion_dialog = False


# =========================================
# LIVE COUNTDOWN
# =========================================

@st.fragment(run_every="1s")