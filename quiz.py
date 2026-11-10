
import math
import html
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from database import fetch_quiz_questions, get_or_create_translation
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
    """Load questions once and initialize quiz state."""

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
        "quiz_translation_cache": {},
        "quiz_results_view": "summary",
        "quiz_retry_mode": False,
        "quiz_finished_at": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "quiz_started_at" not in st.session_state:
        st.session_state.quiz_started_at = datetime.now(timezone.utc)


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

def show_results():
    """Display results and failed-question review options."""

    result = grade_quiz()

    if st.session_state.quiz_finish_reason == "time_expired":
        st.warning(
            "Time expired. Your quiz was graded automatically."
        )

    # Style only the results dashboard.
    # Leave quiz controls and shared CSS intact.
    st.markdown("""
    <style>
    [class*="st-key-results_dashboard"] {
        background: #0f192b;
        border: 1px solid #334155;
        border-radius: 18px;
        padding: clamp(14px, 3vw, 28px);
        margin-bottom: 16px;
    }

    [class*="st-key-results_dashboard"] h2 {
        margin-top: 0;
    }

    [class*="st-key-result_answered"],
    [class*="st-key-result_unanswered"],
    [class*="st-key-result_correct"],
    [class*="st-key-result_errors"],
    [class*="st-key-result_duration"] {
        background: #17253a;
        border: 2px solid #475569;
        border-radius: 14px;
        padding: 14px 18px;
        min-width: 0;
    }

    [class*="st-key-result_correct"] {
        border-color: #22c55e;
        background: #10271f;
    }

    [class*="st-key-result_errors"] {
        border-color: #ef4444;
        background: #301b25;
    }

    [class*="st-key-result_correct"] [data-testid="stMetricValue"] {
        color: #4ade80;
    }

    [class*="st-key-result_errors"] [data-testid="stMetricValue"] {
        color: #f87171;
    }

    [class*="st-key-result_duration"] {
        border-color: #3b82f6;
    }

    [class*="st-key-result_status_pass"] {
        background: #123326;
        border: 1px solid #22c55e;
        border-radius: 12px;
        padding: 14px 18px;
    }

    [class*="st-key-result_status_fail"] {
        background: #381e29;
        border: 1px solid #ef4444;
        border-radius: 12px;
        padding: 14px 18px;
    }

    [class*="st-key-result_status_pass"] p,
    [class*="st-key-result_status_fail"] p {
        font-size: 1.1rem;
        font-weight: 700;
    }

    @media (max-width: 640px) {
        [class*="st-key-results_dashboard"] {
            padding: 12px;
        }

        [class*="st-key-result_answered"],
        [class*="st-key-result_unanswered"],
        [class*="st-key-result_correct"],
        [class*="st-key-result_errors"] {
            padding: 10px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # =====================================
    # CALCULATE COMPLETION TIME
    # =====================================

    finish_time = st.session_state.quiz_finished_at

    if finish_time is None:
        finish_time = datetime.now(timezone.utc)
        st.session_state.quiz_finished_at = finish_time

    elapsed_seconds = max(
        0,
        int(
            (
                finish_time
                - st.session_state.quiz_started_at
            ).total_seconds()
        )
    )

    if st.session_state.quiz_finish_reason == "time_expired":
        elapsed_seconds = min(
            elapsed_seconds,
            QUIZ_DURATION_MINUTES * 60
        )

    minutes, seconds = divmod(elapsed_seconds, 60)

    # =====================================
    # RESULTS DASHBOARD
    # =====================================

    with st.container(key="results_dashboard"):

        heading = "Quiz Results"

        if st.session_state.quiz_retry_mode:
            heading += " — Retry"

        st.subheader(heading)
        st.caption("PATENTE B · TRANSLATE MODE")

        top_left, top_right = st.columns(2, gap="small")

        with top_left:
            with st.container(key="result_answered"):
                st.metric(
                    "Answered",
                    result["answered"]
                )

        with top_right:
            with st.container(key="result_unanswered"):
                st.metric(
                    "Unanswered",
                    result["unanswered"]
                )

        bottom_left, bottom_right = st.columns(
            2,
            gap="small"
        )

        with bottom_left:
            with st.container(key="result_correct"):
                st.metric(
                    "Correct",
                    result["correct"]
                )

        with bottom_right:
            with st.container(key="result_errors"):
                st.metric(
                    "Errors",
                    result["errors"]
                )

        with st.container(key="result_duration"):
            st.metric(
                "⏱ Time Taken",
                f"{minutes}m {seconds:02d}s"
            )

       
        # Normal exam only: show PASS or FAIL.
        # Retry mode is practice, so it has no PASS/FAIL card.
        if not st.session_state.quiz_retry_mode:
            if result["errors"] <= 3:
                with st.container(key="result_status_pass"):
                    st.markdown(
                        "🎉 **PASSED — Congratulations!**"
                    )
            else:
                with st.container(key="result_status_fail"):
                    st.markdown(
                        "😢 **FAILED — Keep Practicing!**"
                    )
                    st.caption(
                        "Maximum allowed: 3 errors"
                    )



        

        st.caption(
            "Unanswered questions count as errors."
        )

    # =====================================
    # REVIEW FAILED QUESTIONS
    # =====================================

    if st.session_state.quiz_results_view == "failed":

        if st.button("← Back to Results"):
            st.session_state.quiz_results_view = "summary"
            st.rerun()

        for number, question in enumerate(
            result["failed"],
            1
        ):
            question_id = question["id"]

            selected = result["answers"].get(
                question_id
            )

            expected = normalize_correct_answer(
                question["correct_answer"]
            )

            with st.container(border=True):

                if selected is None:
                    st.error("Unanswered")
                else:
                    st.error("Incorrect")

                show_question_card(
                    question,
                    number
                )

                if selected is None:
                    selected_text = "Not answered"
                elif selected:
                    selected_text = "VERO"
                else:
                    selected_text = "FALSO"

                correct_text = (
                    "VERO" if expected else "FALSO"
                )

                st.write(
                    f"Your answer: **{selected_text}**"
                )

                st.write(
                    f"Correct answer: **{correct_text}**"
                )

                st.caption(
                    "Chapter: "
                    + str(
                        question.get(
                            "chapter_name",
                            "Unknown"
                        )
                    )
                )

    elif result["failed"]:

        if st.button(
            f"View Failed Questions ({result['errors']})",
            use_container_width=True,
        ):
            st.session_state.quiz_results_view = "failed"
            st.rerun()

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
                or len({q["id"] for q in questions})
                != TOTAL_QUESTIONS
                or len({q["chapter_id"] for q in questions})
                != 25
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
            reset_quiz(questions)

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

def show_question_card(question, question_number):
    """
    Display Italian question, image and translation.

    Desktop:
        Small image left, question text right.

    Mobile:
        Image above question text.

    No image:
        Full-width question text.
    """

    question_id = question["id"]

    italian_text = str(
        question["question"]
    )

    safe_text = html.escape(
        italian_text
    )

    image_file = get_question_image(
        question.get("image_path")
    )

    def display_question_text():
        """Display Italian text, audio and translation."""

        st.markdown(
            f'<div class="quiz-question-text">'
            f'{safe_text}</div>',
            unsafe_allow_html=True,
        )

        # Italian-only audio player.
        show_italian_audio(
            question_text=italian_text,
            question_id=question_id,
        )

        translations_visible = (
            st.session_state.quiz_translations_visible
        )

        is_visible = translations_visible.get(
            question_id,
            False,
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
            translations_visible[question_id] = (
                not is_visible
            )
            st.rerun()

        if translations_visible.get(
            question_id,
            False
        ):

            try:
                translation_cache = (
                    st.session_state.quiz_translation_cache
                )

                if question_id in translation_cache:
                    english_text = (
                        translation_cache[question_id]
                    )

                else:
                    with st.spinner(
                        "Translating into English..."
                    ):
                        english_text = (
                            get_or_create_translation(
                                question_id,
                                italian_text,
                            )
                        )

                    if english_text:
                        translation_cache[question_id] = (
                            english_text
                        )

                if english_text:
                    st.markdown(
                        "**English Translation**"
                    )
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

        st.markdown(
            f"### DOMANDA {question_number}"
        )

        if image_file:

            image_col, text_col = st.columns(
                [1, 3],
                gap="medium",
                vertical_alignment="center",
            )

            with image_col:

                with st.container(
                     key=f"quiz_question_image_{question_id}"
                ):
                    st.image(
                        str(image_file),
                        width=150,
                    )

            with text_col:
                display_question_text()

        else:
            display_question_text()


# =========================================
# SUBMIT / REVIEW MODAL
# =========================================

@st.dialog("Quiz Completed!")
def show_completion_dialog():
    """Show the Submit / Review modal."""

   
    if (
        not st.session_state.quiz_retry_mode
        and get_remaining_seconds() == 0
    ):
        finish_quiz("time_expired")
        st.rerun(scope="app")


    st.success(
        f"All {active_question_count()} "
        "questions have been answered."
    )

    st.write(
        "Would you like to submit your answers "
        "or review them before submitting?"
    )

    review_col, submit_col = st.columns(
        2,
        gap="small",
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

            
            if (
                not st.session_state.quiz_retry_mode
                and get_remaining_seconds() == 0
            ):
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
            "Unable to load quiz questions "
            "from PostgreSQL."
        )

        st.caption(
            f"Database error: {exc}"
        )
        return

    
    # Check time expiration for normal exams only.
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

    # Current question.
    index = st.session_state.quiz_question_index
    question_number = index + 1

    question = (
        st.session_state.quiz_questions[index]
    )

    question_id = question["id"]

    # Live timer.
    show_live_timer()

    # =====================================
    # PROGRESS
    # =====================================

    answered = len(
        st.session_state.quiz_answers
    )

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
    # QUESTION CARD
    # =====================================

    show_question_card(
        question,
        question_number,
    )

    # =====================================
    # RESPONSIVE ANSWER / NAVIGATION BUTTONS
    # =====================================

    # Desktop: Previous | VERO | FALSO | Next
    # Mobile: VERO | FALSO, then Previous | Next

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

    selected = (
        st.session_state.quiz_answers.get(
            question_id
        )
    )

    with st.container(
        key="quiz_controls_row"
    ):

        previous_col, vero_col, falso_col, next_col = (
            st.columns(
                [1, 1, 1, 1],
                gap="small",
            )
        )

        with previous_col:

            with st.container(
                key="quiz_previous"
            ):

                if st.button(
                    "← Previous",
                    disabled=index == 0,
                    use_container_width=True,
                ):
                    go_to_question(
                        index - 1
                    )

        with vero_col:

            with st.container(
                key="quiz_vero"
            ):

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
                        True
                    )

        with falso_col:

            with st.container(
                key="quiz_falso"
            ):

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
                        False
                    )

        with next_col:

            with st.container(
                key="quiz_next"
            ):

                if st.button(
                    "Next →",
                    disabled=(
                        index == active_question_count() - 1
                    ),
                    use_container_width=True,
                ):
                    go_to_question(
                        index + 1
                    )

    # Existing pagination remains unchanged.
    show_pagination()

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
