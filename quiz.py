
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
def show_live_timer():
    """Update the timer every second."""

    if st.session_state.quiz_finished:
        return

    remaining = get_remaining_seconds()
    minutes, seconds = divmod(remaining, 60)

    if remaining == 0:
        finish_quiz("time_expired")
        st.rerun(scope="app")

    elif remaining <= 300:
        st.error(
            f"⏱ Time Remaining: {minutes:02d}:{seconds:02d}"
        )

    else:
        st.info(
            f"⏱ Time Remaining: {minutes:02d}:{seconds:02d}"
        )


# =========================================
# ANSWERS AND NAVIGATION
# =========================================

def select_answer(question_id, answer):
    """Save an answer and automatically move forward."""

    if st.session_state.quiz_finished:
        return

    if get_remaining_seconds() == 0:
        finish_quiz("time_expired")
        st.rerun()

    answers = st.session_state.quiz_answers
    was_complete = len(answers) == TOTAL_QUESTIONS

    # Save using the real PostgreSQL question ID
    answers[question_id] = answer

    # Open completion modal after final answer
    if (
        len(answers) == TOTAL_QUESTIONS
        and not was_complete
        and not st.session_state.quiz_completion_prompt_shown
    ):
        st.session_state.quiz_completion_prompt_shown = True
        st.session_state.quiz_show_completion_dialog = True

    else:
        current = st.session_state.quiz_question_index

        if current < TOTAL_QUESTIONS - 1:
            st.session_state.quiz_question_index = current + 1

    st.rerun()


def go_to_question(index):
    """Navigate between questions."""

    if st.session_state.quiz_finished:
        return

    if get_remaining_seconds() == 0:
        finish_quiz("time_expired")
        st.rerun()

    if 0 <= index < TOTAL_QUESTIONS:
        st.session_state.quiz_question_index = index
        st.rerun()


# =========================================
# VERO / FALSO BUTTONS
# =========================================

def show_answer_buttons(question_id):
    """Display VERO and FALSO answer buttons."""

    selected = st.session_state.quiz_answers.get(question_id)

    col1, col2 = st.columns(2, gap="small")

    with col1:
        with st.container(key="quiz_vero"):

            label = "✓ VERO" if selected is True else "VERO"

            if st.button(
                label,
                key=f"vero_{question_id}",
                use_container_width=True,
            ):
                select_answer(question_id, True)

    with col2:
        with st.container(key="quiz_falso"):

            label = "✕ FALSO" if selected is False else "FALSO"

            if st.button(
                label,
                key=f"falso_{question_id}",
                use_container_width=True,
            ):
                select_answer(question_id, False)


# =========================================
# QUESTION PAGINATION
# =========================================

def show_pagination():
    """Display all 30 questions in one scrollable row."""

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
        for index in range(TOTAL_QUESTIONS):
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

    relative_path = str(image_path).lstrip("/\\")

    image_file = (
        PROJECT_FOLDER / relative_path
    ).resolve()

    if not image_file.is_relative_to(PROJECT_FOLDER):
        return None

    if image_file.is_file():
        return image_file

    return None


# =========================================
# QUESTION CARD WITH TRANSLATION
# =========================================

def show_question_card(question, question_number):
    """
    Display Italian question, image and English translation.

    Desktop:
        Small image left, question text right.

    Mobile:
        Image above question text.

    No image:
        Full-width question text.
    """

    question_id = question["id"]
    italian_text = str(question["question"])

    # Escape HTML for safe display
    safe_text = html.escape(italian_text)

    image_file = get_question_image(
        question.get("image_path")
    )

    def display_question_text():
        """Display Italian text, audio and translation."""

        # Original Italian question
        st.markdown(
            f'<div class="quiz-question-text">{safe_text}</div>',
            unsafe_allow_html=True
        )

        # Italian-only audio player
        show_italian_audio(
            question_text=italian_text,
            question_id=question_id
        )

        translations_visible = (
            st.session_state.quiz_translations_visible
        )

        is_visible = translations_visible.get(
            question_id,
            False
        )

        button_label = (
            "Hide Translation"
            if is_visible
            else "Translate"
        )

        if st.button(
            button_label,
            key=f"translate_{question_id}",
        ):
            translations_visible[question_id] = not is_visible
            st.rerun()

        # Show translation only when requested
        if translations_visible.get(question_id, False):

            try:
                with st.spinner("Translating into English..."):

                    english_text = translate_to_english(
                        italian_text
                    )

                if english_text:

                    st.markdown("**English Translation**")

                    st.info(english_text)

                else:

                    st.warning(
                        "No translation was returned."
                    )

            except Exception as e:

                st.error("Translation failed.")

                st.code(
                    f"{type(e).__name__}: {e}"
                )

    with st.container(border=True):

        st.markdown(f"### DOMANDA {question_number}")

        if image_file:

            image_col, text_col = st.columns(
                [1, 3],
                gap="medium",
                vertical_alignment="center"
            )

            # LEFT - QUESTION IMAGE
            with image_col:

                with st.container(key="quiz_question_image"):

                    st.image(
                        str(image_file),
                        width=150
                    )

            # RIGHT - QUESTION AND TRANSLATION
            with text_col:

                display_question_text()

        else:

            # No image - full-width question
            display_question_text()


# =========================================
# SUBMIT / REVIEW MODAL
# =========================================

@st.dialog("Quiz Completed!")
def show_completion_dialog():
    """Show the Submit / Review modal."""

    if get_remaining_seconds() == 0:
        finish_quiz("time_expired")
        st.rerun()

    st.success("All 30 questions have been answered.")

    st.write(
        "Would you like to submit your answers "
        "or review them before submitting?"
    )

    review_col, submit_col = st.columns(
        2,
        gap="small"
    )

    with review_col:

        if st.button(
            "Review",
            key="completion_review",
            use_container_width=True,
        ):
            st.session_state.quiz_show_completion_dialog = False
            st.rerun()

    with submit_col:

        if st.button(
            "Submit Quiz",
            key="completion_submit",
            type="primary",
            use_container_width=True,
        ):

            if get_remaining_seconds() == 0:
                finish_quiz("time_expired")

            else:
                st.session_state.quiz_submit_pending = True
                finish_quiz("submitted")

            st.rerun()


# =========================================
# MAIN QUIZ PAGE
# =========================================

def show_quiz():
    """Display the Translate Mode quiz page."""

    try:
        initialize_quiz()

    except Exception as exc:

        st.error(
            "Unable to load quiz questions from PostgreSQL."
        )

        st.caption(f"Database error: {exc}")
        return

    # Check time expiration
    if (
        not st.session_state.quiz_finished
        and get_remaining_seconds() == 0
    ):
        finish_quiz("time_expired")

    # =====================================
    # FINISHED QUIZ
    # =====================================

    if st.session_state.quiz_finished:

        answered = len(st.session_state.quiz_answers)

        if st.session_state.quiz_finish_reason == "submitted":

            st.success(
                "Quiz submitted. Your answers have "
                "been saved for this session."
            )

        else:

            st.error(
                "Time has expired. Your quiz has ended."
            )

        st.write(
            f"You answered {answered} of "
            f"{TOTAL_QUESTIONS} questions."
        )

        st.info(
            "Database grading and results "
            "will be connected in the next step."
        )

        return

    # Show completion modal
    if st.session_state.quiz_show_completion_dialog:
        show_completion_dialog()

    # Current question
    index = st.session_state.quiz_question_index
    question_number = index + 1

    question = st.session_state.quiz_questions[index]
    question_id = question["id"]

    # Live timer
    show_live_timer()

    # =====================================
    # PROGRESS
    # =====================================

    answered = len(st.session_state.quiz_answers)

    st.write(
        f"Question {question_number} of {TOTAL_QUESTIONS}"
    )

    st.progress(
        answered / TOTAL_QUESTIONS
    )

    st.caption(
        f"{answered} of {TOTAL_QUESTIONS} questions answered"
    )

    # =====================================
    # QUESTION CARD
    # =====================================

    show_question_card(
        question,
        question_number
    )

    # =====================================
    # RESPONSIVE ANSWER / NAVIGATION BUTTONS
    # =====================================

    # Existing button styling remains controlled by the original CSS.
    # Desktop: Previous | VERO | FALSO | Next
    # Mobile:  VERO | FALSO, then Previous | Next
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
        [class*="st-key-quiz_controls_row"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(1) { order: 3; }
        [class*="st-key-quiz_controls_row"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) { order: 1; }
        [class*="st-key-quiz_controls_row"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(3) { order: 2; }
        [class*="st-key-quiz_controls_row"] [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(4) { order: 4; }
            [class*="st-key-quiz_controls_row"] .stButton button {
        width: 100% !important;
        min-height: 48px !important;
        padding: 0.5rem 0.25rem !important;
        box-sizing: border-box !important;
    }
    }
    
    </style>
    """, unsafe_allow_html=True)

    selected = st.session_state.quiz_answers.get(question_id)

    with st.container(key="quiz_controls_row"):
        previous_col, vero_col, falso_col, next_col = st.columns(
    [1, 1, 1, 1],
    gap="small"
)

        with previous_col:
            with st.container(key="quiz_previous"):
                if st.button(
                    "← Previous",
                    disabled=index == 0,
                    use_container_width=True,
                ):
                    go_to_question(index - 1)

        with vero_col:
            with st.container(key="quiz_vero"):
                label = "✓ VERO" if selected is True else "VERO"
                if st.button(
                    label,
                    key=f"vero_{question_id}",
                    use_container_width=True,
                ):
                    select_answer(question_id, True)

        with falso_col:
            with st.container(key="quiz_falso"):
                label = "✕ FALSO" if selected is False else "FALSO"
                if st.button(
                    label,
                    key=f"falso_{question_id}",
                    use_container_width=True,
                ):
                    select_answer(question_id, False)

        with next_col:
            with st.container(key="quiz_next"):
                if st.button(
                    "Next →",
                    disabled=index == TOTAL_QUESTIONS - 1,
                    use_container_width=True,
                ):
                    go_to_question(index + 1)

    # Existing pagination remains unchanged.
    show_pagination()

    # =====================================
    # SUBMIT QUIZ
    # =====================================

    if answered == TOTAL_QUESTIONS:

        st.success("All 30 questions answered.")

        if st.button(
            "Submit Quiz",
            key="quiz_submit_again",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.quiz_show_completion_dialog = True
            st.rerun()
