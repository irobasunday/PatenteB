
import math
import html
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from database import fetch_quiz_questions, get_or_create_translation
from audio_player import show_italian_audio

from browser_identity import get_browser_id, create_browser_id
from quiz_question_recovery import fetch_questions_by_ids
from quiz_attempt_storage import (
    load_active_attempt,
    start_attempt,
    save_progress,
    finish_attempt,
)



# =========================================
# QUIZ SETTINGS
# =========================================

TOTAL_QUESTIONS = 30
QUIZ_DURATION_MINUTES = 20
PROJECT_FOLDER = Path(__file__).resolve().parent


# =========================================
# QUIZ STATE
# =========================================


def persist_quiz_progress():
    """Save answers and question position to PostgreSQL."""

    if st.session_state.get("quiz_retry_mode"):
        return

    saved = save_progress(
        st.session_state.quiz_attempt_id,
        st.session_state.browser_id,
        "quiz",
        st.session_state.quiz_answers,
        st.session_state.quiz_question_index,
    )

    if not saved:
        raise RuntimeError(
            "Unable to save the active quiz attempt."
        )


def start_persisted_quiz(questions):
    """Start a new quiz and save its question IDs."""

    started_at = datetime.now(timezone.utc)

    attempt_id = start_attempt(
        st.session_state.browser_id,
        "quiz",
        [question["id"] for question in questions],
        started_at,
    )

    reset_quiz(questions)

    st.session_state.quiz_attempt_id = attempt_id
    st.session_state.quiz_started_at = started_at
    st.session_state.quiz_retry_mode = False



def initialize_quiz():
    """Restore an active quiz or start a new one."""

    if "quiz_questions" not in st.session_state:

        browser_id = st.session_state.get("browser_id")

        if not browser_id:
            raise RuntimeError(
                "Browser identity is not available."
            )

        attempt = load_active_attempt(browser_id, "quiz")

        if attempt is not None:

            questions = fetch_questions_by_ids(
                attempt["question_ids"]
            )

            if len(questions) != TOTAL_QUESTIONS:
                raise ValueError(
                    "Saved quiz must contain 30 questions."
                )

            st.session_state.quiz_questions = questions
            st.session_state.quiz_attempt_id = attempt["id"]

            st.session_state.quiz_question_index = max(
                0,
                min(
                    int(attempt["question_index"]),
                    len(questions) - 1,
                ),
            )

            valid_ids = {
                question["id"] for question in questions
            }

            st.session_state.quiz_answers = {
                int(key): value
                for key, value in attempt["answers"].items()
                if int(key) in valid_ids
                and isinstance(value, bool)
            }

            st.session_state.quiz_started_at = (
                attempt["started_at"]
            )

            st.session_state.quiz_retry_mode = False

            st.session_state.quiz_completion_prompt_shown = (
                len(st.session_state.quiz_answers)
                == len(questions)
            )

        else:

            questions = fetch_quiz_questions()

            if (
                len(questions) != TOTAL_QUESTIONS
                or len({
                    question["id"]
                    for question in questions
                }) != TOTAL_QUESTIONS
                or len({
                    question["chapter_id"]
                    for question in questions
                }) != 25
            ):
                raise ValueError(
                    "Expected 30 unique questions "
                    "covering all 25 chapters."
                )

            start_persisted_quiz(questions)

    defaults = {
        "quiz_question_index": 0,
        "quiz_answers": {},
        "quiz_finished": False,
        "quiz_completion_prompt_shown": False,
        "quiz_show_completion_dialog": False,
        "quiz_submit_pending": False,
        "quiz_finish_reason": None,
        "quiz_translations_visible": {},
        "quiz_translation_cache": {},
        "quiz_results_view": "summary",
        "quiz_retry_mode": False,
        "quiz_finished_at": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "quiz_started_at" not in st.session_state:
        st.session_state.quiz_started_at = (
            datetime.now(timezone.utc)
        )


def active_question_count():
    return len(st.session_state.quiz_questions)


# =========================================
# ANSWER NORMALIZATION AND GRADING
# =========================================

def normalize_correct_answer(value):
    """Convert PostgreSQL correct answers to Python Boolean."""

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
        f"Unexpected correct_answer value: {value!r}"
    )


def grade_quiz():
    """Grade the active quiz using PostgreSQL correct answers."""

    questions = st.session_state.quiz_questions
    answers = st.session_state.quiz_answers

    failed = []
    correct = 0

    for question in questions:
        question_id = question["id"]

        expected = normalize_correct_answer(
            question["correct_answer"]
        )

        if (
            question_id in answers
            and answers[question_id] == expected
        ):
            correct += 1
        else:
            failed.append(question)

    answered = sum(
        question["id"] in answers
        for question in questions
    )

    return {
        "answered": answered,
        "unanswered": len(questions) - answered,
        "correct": correct,
        "errors": len(failed),
        "failed": failed,
        "answers": dict(answers),
    }


# =========================================
# RESET / RETRY QUIZ
# =========================================

def reset_quiz(questions):
    """Start a fresh attempt with the supplied questions."""

    st.session_state.quiz_questions = list(questions)
    st.session_state.quiz_question_index = 0
    st.session_state.quiz_answers = {}
    st.session_state.quiz_finished = False
    st.session_state.quiz_completion_prompt_shown = False
    st.session_state.quiz_show_completion_dialog = False
    st.session_state.quiz_submit_pending = False
    st.session_state.quiz_finish_reason = None
    st.session_state.quiz_translations_visible = {}
    st.session_state.quiz_translation_cache = {}
    st.session_state.quiz_results_view = "summary"
    st.session_state.quiz_started_at = datetime.now(timezone.utc)
    st.session_state.quiz_finished_at = None


# =========================================
# QUIZ RESULTS

# =========================================
# QUIZ RESULTS
# =========================================

@st.dialog("📖 Study Failed Question", width="large")
def show_quiz_failed_question_modal(question, number):
    """
    Display the exact failed question in a popup
    without leaving Quiz Translate Mode.
    """

    st.caption("Quiz Translate Mode — Question Review")

    chapter_name = question.get("chapter_name")
    subtopic_name = question.get("subtopic_name")

    if chapter_name:
        st.caption(f"Chapter: {chapter_name}")

    if subtopic_name:
        st.caption(f"Subtopic: {subtopic_name}")

    # Unique widget keys for the popup
    show_question_card(
        question,
        number,
        key_prefix="quiz_failed_modal",
    )

    correct_answer = normalize_correct_answer(
        question["correct_answer"]
    )

    correct_text = "VERO" if correct_answer else "FALSO"

    st.markdown(
        f"Correct answer: :green[**{correct_text}**]"
    )

    st.divider()

    if st.button(
        "Close",
        key="close_quiz_failed_modal",
        use_container_width=True,
        type="primary",
    ):
        st.rerun()
                # =====================================
                # DISPLAY STUDENT ANSWER
                # =====================================


                # =====================================
                # DISPLAY STUDENT ANSWER
                # =====================================

                if question_id not in answers:
                    selected_text = "Not answered"
                else:
                    selected_text = (
                        "VERO" if selected else "FALSO"
                    )

                correct_text = (
                    "VERO" if expected else "FALSO"
                )

                st.write(
                    f"Your answer: **{selected_text}**"
                )

                st.markdown(
                    f"Correct answer: :green[**{correct_text}**]"
                )

                # =====================================
                # RELATED TOPIC
                # =====================================

                topic_name = (
                    question.get("subtopic_name")
                    or question.get("chapter_name")
                    or "Unknown"
                )

                st.caption(
                    f"Related topic: {topic_name}"
                )

                # =====================================
                # STUDY FAILED QUESTION
                # =====================================

                if not is_correct:

                    if st.button(
                        "📖 Study this question",
                        key=f"study_failed_question_{question_id}",
                        use_container_width=True,
                    ):
                        # Open the exact failed question
                        # in a popup without navigation.

                        show_quiz_failed_question_modal(
                            question,
                            number,
                        )

                st.divider()

    else:

        if st.button(
            f"View Quiz Questions ({len(st.session_state.quiz_questions)})",
            use_container_width=True,
        ):
            st.session_state.quiz_results_view = "all_questions"
            st.rerun()

    # =====================================
    # RETRY FAILED QUESTIONS
    # =====================================
    
    # =====================================
    # RETRY FAILED QUESTIONS
    # =====================================

    if result["failed"]:

        if st.button(
            f"Retry Failed Questions ({result['errors']})",
            use_container_width=True,
        ):

            failed_questions = list(
                result["failed"]
            )

            reset_quiz(failed_questions)

            st.session_state.quiz_retry_mode = True

            st.rerun()

    # =====================================
    # START NEW FULL QUIZ
    # =====================================

    if st.button(
        "Start New 30-Question Quiz",
        use_container_width=True,
    ):

        try:
            questions = fetch_quiz_questions()

            if (
                len(questions) != TOTAL_QUESTIONS
                or len({q["id"] for q in questions}) != TOTAL_QUESTIONS
                or len({q["chapter_id"] for q in questions}) != 25
            ):
                raise ValueError(
                    "Expected 30 unique questions "
                    "covering 25 chapters."
                )

        except Exception as exc:
            st.error(
                f"Unable to load a new quiz: {exc}"
            )

        else:
            start_persisted_quiz(questions)

            st.session_state.quiz_retry_mode = False

            st.rerun()

# =========================================
# COUNTDOWN TIMER
# =========================================

def get_remaining_seconds():
    """Calculate remaining quiz time."""

    elapsed = (
        datetime.now(timezone.utc)
        - st.session_state.quiz_started_at
    ).total_seconds()

    return max(
        0,
        math.ceil(
            QUIZ_DURATION_MINUTES * 60 - elapsed
        )
    )


def finish_quiz(reason="time_expired"):
    """Finish quiz without deleting saved answers."""

    if st.session_state.quiz_finished:
        return

    finished_at = datetime.now(timezone.utc)

    if reason == "time_expired":
        deadline = (
            st.session_state.quiz_started_at.timestamp()
            + QUIZ_DURATION_MINUTES * 60
        )

        finished_at = datetime.fromtimestamp(
            deadline,
            tz=timezone.utc
        )


    if not st.session_state.get("quiz_retry_mode"):

        updated = finish_attempt(
            st.session_state.quiz_attempt_id,
            st.session_state.browser_id,
            "quiz",
            st.session_state.quiz_answers,
            (
                "expired"
                if reason == "time_expired"
                else "submitted"
            ),
        )

        if not updated:
            raise RuntimeError(
                "Unable to finalize the saved quiz."
            )

    st.session_state.quiz_finished_at = finished_at
    st.session_state.quiz_finished = True
    st.session_state.quiz_finish_reason = reason
    st.session_state.quiz_show_completion_dialog = False



@st.fragment(run_every="1s")
def show_live_timer():
    """Update the timer every second."""

    if st.session_state.quiz_finished:
        return

    # Disable timer during Retry Failed Questions
    if st.session_state.quiz_retry_mode:
        return

    remaining = get_remaining_seconds()

    minutes, seconds = divmod(
        remaining,
        60
    )


    if remaining == 0:
        finish_quiz("time_expired")
        st.rerun(scope="app")

    elif remaining <= 300:
        st.error(
            f"⏱ Time Remaining: "
            f"{minutes:02d}:{seconds:02d}"
        )

    else:
        st.info(
            f"⏱ Time Remaining: "
            f"{minutes:02d}:{seconds:02d}"
        )


# =========================================
# ANSWERS AND NAVIGATION
# =========================================

def select_answer(question_id, answer):
    """Save answer and automatically move forward."""

    if st.session_state.quiz_finished:
        return

    if (
        not st.session_state.quiz_retry_mode
        and get_remaining_seconds() == 0
    ):
        finish_quiz("time_expired")
        st.rerun()

    answers = st.session_state.quiz_answers

    was_complete = (
        len(answers) == active_question_count()
    )

    # Save using the real PostgreSQL question ID.
    answers[question_id] = answer

    # Open completion modal after final answer.
    if (
        len(answers) == active_question_count()
        and not was_complete
        and not st.session_state.quiz_completion_prompt_shown
    ):

        st.session_state.quiz_completion_prompt_shown = True
        st.session_state.quiz_show_completion_dialog = True

    else:

        current = st.session_state.quiz_question_index

        if current < active_question_count() - 1:
            st.session_state.quiz_question_index = (
                current + 1
            )

    persist_quiz_progress()
    st.rerun()


def go_to_question(index):
    """Navigate between questions."""

    if st.session_state.quiz_finished:
        return

    
    if (
        not st.session_state.quiz_retry_mode
        and get_remaining_seconds() == 0
    ):
        finish_quiz("time_expired")
        st.rerun()


    if 0 <= index < active_question_count():
        st.session_state.quiz_question_index = index
        persist_quiz_progress()
        st.rerun()


# =========================================
# QUESTION PAGINATION
# =========================================

def show_pagination():
    """Display questions in one scrollable row."""

    current = st.session_state.quiz_question_index
    answers = st.session_state.quiz_answers
    questions = st.session_state.quiz_questions

    with st.container(
        key="quiz_pagination_scroll",
        horizontal=True,
        horizontal_alignment="left",
        gap="small",
        width="stretch",
    ):

        for index in range(
            active_question_count()
        ):

            number = index + 1
            question_id = questions[index]["id"]

            if index == current:
                status = "current"

            elif question_id in answers:
                status = "answered"

            else:
                status = "unanswered"

            with st.container(
                key=f"pagination_{status}_{number}"
            ):

                if st.button(
                    str(number),
                    key=f"pagination_button_{number}",
                    width=75,
                ):
                    go_to_question(index)


# =========================================
# QUESTION IMAGE HELPER
# =========================================

def get_question_image(image_path):
    """Find an image safely inside the project folder."""

    if not image_path:
        return None

    relative_path = str(
        image_path
    ).lstrip("/\\")

    image_file = (
        PROJECT_FOLDER / relative_path
    ).resolve()

    if not image_file.is_relative_to(
        PROJECT_FOLDER
    ):
        return None

    if image_file.is_file():
        return image_file

    return None


# =========================================
# QUESTION CARD WITH TRANSLATION
# =========================================


# =========================================
# MAIN QUIZ PAGE
# =========================================

@st.fragment(run_every="1s")
def wait_for_quiz_browser_identity():
    """
    Wait for browser identity automatically.
    Do not create a new quiz while waiting.
    """

    browser_id = get_browser_id()

    if browser_id:
        st.session_state.browser_id = browser_id
        st.rerun(scope="app")

    st.info("Restoring your saved quiz...")


def show_quiz():
    """
    Display Translate Mode and restore the
    existing PostgreSQL quiz attempt.
    """

    # =====================================
    # BROWSER IDENTITY
    # =====================================

    browser_id = get_browser_id()

    if not browser_id:
        wait_for_quiz_browser_identity()
        return

    st.session_state.browser_id = browser_id

    # =====================================
    # INITIALIZE OR RESTORE QUIZ
    # =====================================

    try:
        initialize_quiz()

    except Exception as exc:
        st.error(
            "Unable to load quiz questions from PostgreSQL."
        )
        st.caption(f"Database error: {exc}")
        return

    # =====================================
    # CHECK QUIZ TIMER
    # =====================================

    if (
        not st.session_state.quiz_finished
        and not st.session_state.quiz_retry_mode
        and get_remaining_seconds() == 0
    ):
        finish_quiz("time_expired")

    # =====================================
    # FINISHED QUIZ
    # =====================================

    if st.session_state.quiz_finished:
        show_results()
        return

    # Show completion modal.
    if st.session_state.quiz_show_completion_dialog:
        show_completion_dialog()

    # =====================================
    # CURRENT QUESTION
    # =====================================

    index = st.session_state.quiz_question_index
    question_number = index + 1

    question = st.session_state.quiz_questions[index]
    question_id = question["id"]

    # =====================================
    # LIVE TIMER
    # =====================================

    show_live_timer()

    # =====================================
    # PROGRESS
    # =====================================

    answered = len(st.session_state.quiz_answers)

    st.write(
        f"Question {question_number} "
        f"of {active_question_count()}"
    )

    st.progress(
        answered / active_question_count()
    )

    st.caption(
        f"{answered} of "
        f"{active_question_count()} "
        "questions answered"
    )
  # =====================================
    # QUESTION PAGINATION
    # =====================================

    show_pagination()
    
    # =====================================
    # QUESTION CARD
    # =====================================

    show_question_card(
        question,
        question_number,
    )

    # =====================================
    # RESPONSIVE ANSWER BUTTONS
    # =====================================

    st.markdown("""
    <style>
    [class*="st-key-quiz_controls_row"] [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: 0.5rem !important;
    }

    [class*="st-key-quiz_controls_row"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        width: 100% !important;
        min-width: 0 !important;
        flex: none !important;
    }

    @media (max-width: 640px) {
        [class*="st-key-quiz_controls_row"] [data-testid="stHorizontalBlock"] {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }

        [class*="st-key-quiz_controls_row"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(1) {
            order: 3;
        }

        [class*="st-key-quiz_controls_row"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) {
            order: 1;
        }

        [class*="st-key-quiz_controls_row"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3) {
            order: 2;
        }

        [class*="st-key-quiz_controls_row"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4) {
            order: 4;
        }

        [class*="st-key-quiz_controls_row"] .stButton button {
            width: 100% !important;
            min-height: 48px !important;
            padding: 0.5rem 0.25rem !important;
            box-sizing: border-box !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    selected = st.session_state.quiz_answers.get(
        question_id
    )

    with st.container(key="quiz_controls_row"):

        previous_col, vero_col, falso_col, next_col = (
            st.columns(
                [1, 1, 1, 1],
                gap="small",
            )
        )

        # =================================
        # PREVIOUS BUTTON
        # =================================

        with previous_col:
            with st.container(key="quiz_previous"):

                if st.button(
                    "← Previous",
                    disabled=index == 0,
                    use_container_width=True,
                ):
                    go_to_question(index - 1)

        # =================================
        # VERO BUTTON
        # =================================

        with vero_col:
            with st.container(key="quiz_vero"):

                label = (
                    "✓ VERO"
                    if selected is True
                    else "VERO"
                )

                if st.button(
                    label,
                    key=f"vero_{question_id}",
                    use_container_width=True,
                ):
                    select_answer(
                        question_id,
                        True,
                    )

        # =================================
        # FALSO BUTTON
        # =================================

        with falso_col:
            with st.container(key="quiz_falso"):

                label = (
                    "✕ FALSO"
                    if selected is False
                    else "FALSO"
                )

                if st.button(
                    label,
                    key=f"falso_{question_id}",
                    use_container_width=True,
                ):
                    select_answer(
                        question_id,
                        False,
                    )

        # =================================
        # NEXT BUTTON
        # =================================

        with next_col:
            with st.container(key="quiz_next"):

                if st.button(
                    "Next →",
                    disabled=(
                        index == active_question_count() - 1
                    ),
                    use_container_width=True,
                ):
                    go_to_question(index + 1)

  

    # =====================================
    # SUBMIT QUIZ
    # =====================================

    if answered == active_question_count():

        st.success(
            f"All {active_question_count()} "
            "questions answered."
        )

        if st.button(
            "Submit Quiz",
            key="quiz_submit_again",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.quiz_show_completion_dialog = True
            st.rerun()


