
import streamlit as st
from datetime import datetime, timezone

from database import fetch_quiz_questions


# =========================================
# INSTANT CORRECTION SETTINGS
# =========================================

TOTAL_QUESTIONS = 30
QUIZ_DURATION_MINUTES = 20


# =========================================
# INITIALIZE INSTANT CORRECTION
# =========================================

def initialize_instant_quiz():

    if "instant_questions" not in st.session_state:

        questions = fetch_quiz_questions()

        if len(questions) != TOTAL_QUESTIONS:
            raise ValueError(
                "Expected exactly 30 questions."
            )

        if len({q["id"] for q in questions}) != TOTAL_QUESTIONS:
            raise ValueError(
                "Duplicate question IDs detected."
            )

        if len({q["chapter_id"] for q in questions}) != 25:
            raise ValueError(
                "Questions must cover all 25 chapters."
            )

        st.session_state.instant_questions = questions

    defaults = {
        "instant_question_index": 0,
        "instant_answers": {},
        "instant_finished": False,
        "instant_finish_reason": None,
        "instant_finished_at": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "instant_started_at" not in st.session_state:
        st.session_state.instant_started_at = (
            datetime.now(timezone.utc)
        )


# =========================================
# NORMALIZE CORRECT ANSWER
# =========================================

def normalize_instant_answer(value):

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        mapping = {
            "t": True,
            "true": True,
            "vero": True,
            "f": False,
            "false": False,
            "falso": False,
        }

        normalized = value.strip().lower()

        if normalized in mapping:
            return mapping[normalized]

    if value in (0, 1):
        return bool(value)

    raise ValueError(
        f"Unexpected correct answer: {value!r}"
    )


# =========================================
# SAVE AND LOCK ANSWER
# =========================================

def select_instant_answer(question_id, answer):

    if st.session_state.instant_finished:
        return

    answers = st.session_state.instant_answers

    # Once marked, the answer cannot be changed.
    if question_id in answers:

        st.toast(
            "You cannot change your answer.",
            icon="⚠️",
            duration="short",
        )
        return

    # Find the question using its PostgreSQL ID.
    question = next(
        (
            q for q in st.session_state.instant_questions
            if q["id"] == question_id
        ),
        None,
    )

    if question is None:
        raise ValueError("Question not found.")

    correct_answer = normalize_instant_answer(
        question["correct_answer"]
    )

    # Save the answer permanently for this attempt.
    answers[question_id] = answer

    # The question is now automatically marked.
    is_correct = answer == correct_answer

    # Move to the next unanswered question.
    questions = st.session_state.instant_questions

    for index, item in enumerate(questions):
        if item["id"] not in answers:
            st.session_state.instant_question_index = index
            break

    st.rerun()
