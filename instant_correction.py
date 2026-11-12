
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

from database import fetch_quiz_questions

from browser_identity import get_browser_id
from quiz_question_recovery import fetch_questions_by_ids
from quiz_attempt_storage import (
    load_active_attempt,
    start_attempt,
    save_progress,
    finish_attempt,
)

def normalize_instant_answer(value):
    """
    Convert a stored quiz answer into True or False.
    """

    if isinstance(value, bool):
        return value

    if value is None:
        return None

    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False
        return None

    text = str(value).strip().lower()

    if text in ("vero", "true", "1", "v"):
        return True

    if text in ("falso", "false", "0", "f"):
        return False

    return None


# =========================================
# SETTINGS
# =========================================

TOTAL_QUESTIONS = 30
QUIZ_DURATION_MINUTES = 20

PROJECT_FOLDER = Path(__file__).resolve().parent


# =========================================
# INITIALIZE QUIZ
# =========================================

def initialize_instant_quiz():

    if "instant_questions" not in st.session_state:

        questions = fetch_quiz_questions()

        if len(questions) != TOTAL_QUESTIONS:
            raise ValueError("Expected exactly 30 questions.")

        if len({q["id"] for q in questions}) != TOTAL_QUESTIONS:
            raise ValueError("Duplicate question IDs detected.")

        if len({q["chapter_id"] for q in questions}) != 25:
            raise ValueError("Questions must cover all 25 chapters.")

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
        st.session_state.instant_started_at = datetime.now(
            timezone.utc
        )


# =========================================
# NORMALIZE ANSWERS
# =========================================


def clear_instant_session():
    """Clear only Instant Correction quiz state."""

    keys = (
        "instant_questions",
        "instant_attempt_id",
        "instant_question_index",
        "instant_answers",
        "instant_started_at",
        "instant_finished",
        "instant_finish_reason",
        "instant_finished_at",
    )

    for key in keys:
        st.session_state.pop(key, None)


def save_instant_progress():
    """Save Instant Correction progress to PostgreSQL."""

    saved = save_progress(
        st.session_state.instant_attempt_id,
        st.session_state.browser_id,
        "instant_correction",
        st.session_state.instant_answers,
        st.session_state.instant_question_index,
    )

    if not saved:
        raise RuntimeError(
            "Instant Correction progress could not be saved."
        )


def start_new_instant_quiz():
    """Create a new saved Instant Correction attempt."""

    browser_id = get_browser_id()

    if not browser_id:
        raise RuntimeError(
            "Browser identifier is not ready."
        )

    questions = fetch_quiz_questions()

    if (
        len(questions) != TOTAL_QUESTIONS
        or len({q["id"] for q in questions}) != TOTAL_QUESTIONS
        or len({q["chapter_id"] for q in questions}) != 25
    ):
        raise ValueError(
            "Expected 30 unique questions covering 25 chapters."
        )

    started_at = datetime.now(timezone.utc)

    attempt_id = start_attempt(
        browser_id,
        "instant_correction",
        [question["id"] for question in questions],
        started_at,
    )

    clear_instant_session()

    st.session_state.browser_id = browser_id
    st.session_state.instant_questions = questions
    st.session_state.instant_attempt_id = attempt_id
    st.session_state.instant_question_index = 0
    st.session_state.instant_answers = {}
    st.session_state.instant_started_at = started_at
    st.session_state.instant_finished = False
    st.session_state.instant_finish_reason = None
    st.session_state.instant_finished_at = None


def initialize_instant_quiz():
    """Restore unfinished quiz or create a saved attempt."""

    if "instant_questions" not in st.session_state:

        browser_id = get_browser_id()

        if not browser_id:
            raise RuntimeError(
                "Browser identifier is not ready."
            )

        st.session_state.browser_id = browser_id

        attempt = load_active_attempt(
            browser_id,
            "instant_correction",
        )

        if attempt is None:
            start_new_instant_quiz()

        else:
            questions = fetch_questions_by_ids(
                attempt["question_ids"]
            )

            if len(questions) != TOTAL_QUESTIONS:
                raise ValueError(
                    "Saved quiz does not contain 30 questions."
                )

            valid_ids = {q["id"] for q in questions}

            answers = {
                int(key): value
                for key, value in
                (attempt["answers"] or {}).items()
                if int(key) in valid_ids
                and isinstance(value, bool)
            }

            st.session_state.instant_questions = questions
            st.session_state.instant_attempt_id = attempt["id"]
            st.session_state.instant_answers = answers
            st.session_state.instant_question_index = max(
                0,
                min(
                    int(attempt["question_index"]),
                    len(questions) - 1,
                ),
            )
            st.session_state.instant_started_at = (
                attempt["started_at"]
            )
            st.session_state.instant_finished = False
            st.session_state.instant_finish_reason = None
            st.session_state.instant_finished_at = None

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
# TIMER HELPERS
# =========================================

def get_instant_remaining_seconds():

    elapsed = (
        datetime.now(timezone.utc)
        - st.session_state.instant_started_at
    ).total_seconds()

    return max(
        0,
        math.ceil(
            QUIZ_DURATION_MINUTES * 60 - elapsed
        ),
    )


def finish_instant_quiz(reason):

    if st.session_state.instant_finished:
        return

    if reason == "time_expired":

        finished_at = (
            st.session_state.instant_started_at
            + timedelta(minutes=QUIZ_DURATION_MINUTES)
        )

    else:
        finished_at = datetime.now(timezone.utc)

    updated = finish_attempt(
        st.session_state.instant_attempt_id,
        st.session_state.browser_id,
        "instant_correction",
        st.session_state.instant_answers,
        (
            "expired"
            if reason == "time_expired"
            else "submitted"
        ),
    )

    if not updated:
        raise RuntimeError(
            "Unable to finalize Instant Correction quiz."
        )

    st.session_state.instant_finished = True
    st.session_state.instant_finish_reason = reason
    st.session_state.instant_finished_at = finished_at


@st.fragment(run_every="1s")
def show_instant_timer():

    if st.session_state.instant_finished:
        return

    remaining = get_instant_remaining_seconds()

    if remaining == 0:
        finish_instant_quiz("time_expired")
        st.rerun(scope="app")

    minutes, seconds = divmod(remaining, 60)

    if remaining <= 300:

        st.error(
            f"⏱ Time Remaining: {minutes:02d}:{seconds:02d}"
        )

    else:

        st.info(
            f"⏱ Time Remaining: {minutes:02d}:{seconds:02d}"
        )


# =========================================
# SAVE AND LOCK ANSWER
# =========================================

def select_instant_answer(question_id, answer):

    if st.session_state.instant_finished:
        return

    if get_instant_remaining_seconds() == 0:
        finish_instant_quiz("time_expired")
        st.rerun()

    answers = st.session_state.instant_answers

    if question_id in answers:

        st.toast(
            "You cannot change your answer.",
            icon="⚠️",
            duration="short",
        )
        return

    questions = st.session_state.instant_questions

    current_index = next(
        (
            index
            for index, item in enumerate(questions)
            if item["id"] == question_id
        ),
        None,
    )

    if current_index is None:
        raise ValueError("Question not found.")

    question = questions[current_index]

    normalize_instant_answer(
        question["correct_answer"]
    )

    answers[question_id] = answer

    # Finish immediately when all questions are answered.
    if len(answers) == len(questions):
        finish_instant_quiz("all_answered")
        st.rerun()

    next_index = None

    # Search forward for the next unanswered question.
    for index in range(
        current_index + 1,
        len(questions),
    ):

        if questions[index]["id"] not in answers:
            next_index = index
            break

    # Return to earlier unanswered questions.
    if next_index is None:

        for index in range(current_index):

            if questions[index]["id"] not in answers:
                next_index = index
                break

    
    if next_index is not None:
        st.session_state.instant_question_index = next_index

    save_instant_progress()
    st.rerun()


# =========================================
# QUESTION NAVIGATION
# =========================================

def go_to_instant_question(index):

    if st.session_state.instant_finished:
        return

    if get_instant_remaining_seconds() == 0:
        finish_instant_quiz("time_expired")
        st.rerun()

    questions = st.session_state.instant_questions

    if 0 <= index < len(questions):

        
        st.session_state.instant_question_index = index
        save_instant_progress()
        st.rerun()


# =========================================
# LOAD DEDICATED PAGINATION CSS
# =========================================

def load_instant_pagination_css():

    css_file = (
        PROJECT_FOLDER
        / "styles"
        / "instant_pagination.css"
    )

    if not css_file.is_file():
        st.error(
            "Instant pagination stylesheet not found: "
            "styles/instant_pagination.css"
        )
        return

    css = css_file.read_text(encoding="utf-8")

    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True,
    )


# =========================================
# INSTANT CORRECTION STYLING
# =========================================

def load_instant_styles():

    st.markdown(
        """
        <style>

        /* =================================
           VERO AND FALSO BUTTONS
           ================================= */

        .st-key-instant_answer_vero button {
            border: 1.5px solid #22c55e !important;
            color: #4ade80 !important;
            border-radius: 10px !important;
            min-height: 42px !important;
        }

        .st-key-instant_answer_falso button {
            border: 1.5px solid #ef4444 !important;
            color: #f87171 !important;
            border-radius: 10px !important;
            min-height: 42px !important;
        }

        .st-key-instant_answer_vero button:hover {
            background-color: #14532d !important;
        }

        .st-key-instant_answer_falso button:hover {
            background-color: #7f1d1d !important;
        }

        /* =================================
           PREVIOUS AND NEXT BUTTONS
           ================================= */

        .st-key-instant_previous button,
        .st-key-instant_next button {
            border-radius: 10px !important;
            min-height: 40px !important;
        }

        /* =================================
           RESULTS BADGES
           ================================= */

        .instant-results {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 18px 0 24px;
        }

        .instant-result-badge {
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            align-self: flex-start;

            width: fit-content;
            min-width: 85px;
            padding: 9px 14px;

            border: 1px solid #475569;
            border-radius: 12px;
            background: #111827;

            text-align: center;
        }

        .instant-result-label {
            font-size: 12px;
            color: #cbd5e1;
        }

        .instant-result-value {
            font-size: 21px;
            font-weight: 700;
            line-height: 1.4;
            color: #f8fafc;
        }

        .instant-result-correct {
            border-color: #22c55e;
        }

        .instant-result-correct .instant-result-value {
            color: #4ade80;
        }

        .instant-result-wrong {
            border-color: #ef4444;
        }

        .instant-result-wrong .instant-result-value {
            color: #f87171;
        }

        @media (max-width: 480px) {

            .instant-results {
                gap: 8px;
            }

            .instant-result-badge {
                min-width: 75px;
                padding: 7px 11px;
            }

        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================
# HORIZONTAL QUESTION PAGINATION
# =========================================

def show_instant_pagination():
    """
    Display question numbers in a single
    horizontally scrollable row.

    Each button retains its correct,
    wrong, or unanswered status.
    """

    questions = st.session_state.instant_questions
    answers = st.session_state.instant_answers

    with st.container(
        key="instant_pagination_scroll",
        horizontal=True,
        horizontal_alignment="left",
        gap="small",
        width="stretch",
    ):

        for index, question in enumerate(questions):

            number = index + 1
            question_id = question["id"]

            if question_id not in answers:

                status = "unanswered"

            else:

                expected = normalize_instant_answer(
                    question["correct_answer"]
                )

                if answers[question_id] == expected:
                    status = "correct"
                else:
                    status = "wrong"

            with st.container(
                key=f"instant_page_{status}_{number}"
            ):

                if st.button(
                    str(number),
                    key=f"instant_page_button_{number}",
                    width=75,
                ):

                    go_to_instant_question(index)


# =========================================
# QUESTION INTERFACE
# =========================================

def show_instant_question():

    questions = st.session_state.instant_questions
    index = st.session_state.instant_question_index

    question = questions[index]
    question_id = question["id"]

    answers = st.session_state.instant_answers

    st.write(
        f"Question {index + 1} of {len(questions)}"
    )

    st.progress(
        len(answers) / len(questions)
    )

    # =====================================
    # ITALIAN QUESTION CARD
    # =====================================

    with st.container(border=True):

        st.markdown(
            f"### DOMANDA {index + 1}"
        )

        st.write(
            question["question"]
        )

        from quiz_backup import get_question_image
        from audio_player import show_italian_audio

        image_file = get_question_image(
            question.get("image_path")
        )

        if image_file:

            st.image(
                str(image_file),
                width=150,
            )

        show_italian_audio(
            question_text=str(question["question"]),
            question_id=question_id,
        )

    # =====================================
    # DISPLAY CORRECTION
    # =====================================

    already_answered = question_id in answers

    if already_answered:

        selected = answers[question_id]

        correct_answer = normalize_instant_answer(
            question["correct_answer"]
        )

        if selected == correct_answer:

            st.success(
                "✓ Correct answer!"
            )

        else:

            st.error(
                "✕ Incorrect answer!"
            )

            st.markdown(
                "**Correct answer: "
                + ("VERO" if correct_answer else "FALSO")
                + "**"
            )

    # =====================================
    # VERO / FALSO BUTTONS
    # =====================================

    left_space, vero_col, falso_col, right_space = (
        st.columns(
            [0.2, 1, 1, 0.2],
            gap="small",
        )
    )

    with vero_col:

        with st.container(
            key="instant_answer_vero"
        ):

            if st.button(
                "VERO",
                key=f"instant_vero_{question_id}",
                use_container_width=True,
            ):

                select_instant_answer(
                    question_id,
                    True,
                )

    with falso_col:

        with st.container(
            key="instant_answer_falso"
        ):

            if st.button(
                "FALSO",
                key=f"instant_falso_{question_id}",
                use_container_width=True,
            ):

                select_instant_answer(
                    question_id,
                    False,
                )

    # =====================================
    # PREVIOUS / NEXT NAVIGATION
    # =====================================

    st.divider()

    left_space, previous_col, next_col, right_space = (
        st.columns(
            [0.2, 1, 1, 0.2],
            gap="small",
        )
    )

    with previous_col:

        if st.button(
            "← Previous",
            key="instant_previous",
            disabled=index == 0,
            use_container_width=True,
        ):

            go_to_instant_question(
                index - 1
            )

    with next_col:

        if st.button(
            "Next →",
            key="instant_next",
            disabled=index == len(questions) - 1,
            use_container_width=True,
        ):

            go_to_instant_question(
                index + 1
            )

    # =====================================
    # HORIZONTAL QUESTION PAGINATION
    # =====================================

    show_instant_pagination()


# =========================================
# RESULTS DASHBOARD
# =========================================

def show_instant_results():

    questions = st.session_state.instant_questions
    answers = st.session_state.instant_answers

    correct = 0
    wrong = 0

    for question in questions:

        question_id = question["id"]

        if question_id not in answers:
            continue

        expected = normalize_instant_answer(
            question["correct_answer"]
        )

        if answers[question_id] == expected:
            correct += 1
        else:
            wrong += 1

    unanswered = len(questions) - len(answers)
    total_errors = wrong + unanswered

    passed = total_errors <= 3

    started_at = st.session_state.instant_started_at
    finished_at = st.session_state.instant_finished_at

    if finished_at is None:
        finished_at = datetime.now(timezone.utc)

    elapsed_seconds = max(
        0,
        int(
            (finished_at - started_at).total_seconds()
        ),
    )

    minutes, seconds = divmod(
        elapsed_seconds,
        60,
    )

    # =====================================
    # PASS / FAIL
    # =====================================

    if passed:

        st.success(
            "✓ PASS — Congratulations!"
        )

    else:

        st.error(
            "✕ FAIL — Keep practicing!"
        )

    if (
        st.session_state.instant_finish_reason
        == "time_expired"
    ):

        st.warning(
            "Time expired. Your quiz was submitted automatically."
        )

    else:

        st.info(
            "All 30 questions completed."
        )

    # =====================================
    # RESULTS BADGES
    # =====================================

    badges = [
        (
            "Correct",
            correct,
            "instant-result-correct",
        ),
        (
            "Wrong",
            wrong,
            "instant-result-wrong",
        ),
        (
            "Unanswered",
            unanswered,
            "",
        ),
        (
            "Total Errors",
            total_errors,
            "instant-result-wrong",
        ),
        (
            "Time Taken",
            f"{minutes:02d}:{seconds:02d}",
            "",
        ),
    ]

    badge_html = ""

    for label, value, status_class in badges:

        badge_html += (
            f'<div class="instant-result-badge {status_class}">'
            f'<span class="instant-result-label">{label}</span>'
            f'<span class="instant-result-value">{value}</span>'
            '</div>'
        )

    results_html = (
        '<div class="instant-results">'
        + badge_html
        + '</div>'
    )

    st.markdown(
        results_html,
        unsafe_allow_html=True,
    )

    st.divider()

    # =====================================
    # REVIEW YOUR ANSWERS
    # =====================================

    st.markdown(
        "### Review Your Answers"
    )

    for index, question in enumerate(questions):

        question_id = question["id"]

        expected = normalize_instant_answer(
            question["correct_answer"]
        )

        selected = answers.get(question_id)

        if question_id not in answers:

            status = "⚪ Unanswered"

        elif selected == expected:

            status = "🟢 Correct"

        else:

            status = "🔴 Incorrect"

        with st.expander(
            f"Question {index + 1} — {status}"
        ):

            st.write(
                question["question"]
            )

            if question_id in answers:

                st.write(
                    "Your answer:",
                    "VERO" if selected else "FALSO",
                )

            else:

                st.write(
                    "Your answer: Not answered"
                )

            st.write(
                "Correct answer:",
                "VERO" if expected else "FALSO",
            )


@st.fragment(run_every="1s")
def wait_for_instant_browser_identity():
    """
    Wait automatically for browser identity
    without creating a new quiz.
    """

    browser_id = get_browser_id()

    if browser_id:
        st.session_state.browser_id = browser_id
        st.rerun(scope="app")

    st.info("Restoring your Instant Correction quiz...")

# =========================================
# MAIN INSTANT CORRECTION PAGE
# =========================================


def show_instant_correction():
    """
    Display Instant Correction and automatically
    restore an unfinished quiz after refresh.
    """

    # =====================================
    # RESTORE BROWSER IDENTITY FIRST
    # =====================================

    browser_id = get_browser_id()

    if not browser_id:
        wait_for_instant_browser_identity()
        return

    st.session_state.browser_id = browser_id

    # =====================================
    # RESTORE SAVED QUIZ
    # =====================================

    try:
        initialize_instant_quiz()

    except Exception as exc:
        st.error(
            "Unable to restore Instant Correction quiz."
        )
        st.caption(
            f"Recovery error: {exc}"
        )
        return

    # =====================================
    # EXISTING STYLING
    # =====================================

    load_instant_styles()
    load_instant_pagination_css()

    # =====================================
    # TIMER
    # =====================================

    if (
        not st.session_state.instant_finished
        and get_instant_remaining_seconds() == 0
    ):
        finish_instant_quiz("time_expired")

    # =====================================
    # RESULTS
    # =====================================

    if st.session_state.instant_finished:
        show_instant_results()
        return

    # =====================================
    # ACTIVE QUIZ
    # =====================================

    show_instant_timer()
    show_instant_question()


    initialize_instant_quiz()

    # Existing Instant Correction styling.
    load_instant_styles()

    # Dedicated horizontal pagination styling.
    load_instant_pagination_css()

    # Automatically finish when time expires.
    if (
        not st.session_state.instant_finished
        and get_instant_remaining_seconds() == 0
    ):

        finish_instant_quiz(
            "time_expired"
        )

    # Show results when finished.
    if st.session_state.instant_finished:

        show_instant_results()
        return

    # Question, answers, and pagination.
   
