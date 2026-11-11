
import math
from datetime import datetime, timedelta, timezone

import streamlit as st

from database import fetch_quiz_questions


# =========================================
# SETTINGS
# =========================================

TOTAL_QUESTIONS = 30
QUIZ_DURATION_MINUTES = 20


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
        st.session_state.instant_started_at = (
            datetime.now(timezone.utc)
        )


# =========================================
# NORMALIZE ANSWERS
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
# TIMER HELPERS
# =========================================

def get_instant_remaining_seconds():

    elapsed = (
        datetime.now(timezone.utc)
        - st.session_state.instant_started_at
    ).total_seconds()

    return max(
        0,
        math.ceil(QUIZ_DURATION_MINUTES * 60 - elapsed),
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

    # Previously answered questions are locked.
    if question_id in answers:

        st.toast(
            "You cannot change your answer.",
            icon="⚠️",
            duration="short",
        )
        return

    questions = st.session_state.instant_questions

    # Locate the original question.
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

    # Validate the answer stored in PostgreSQL.
    normalize_instant_answer(
        question["correct_answer"]
    )

    # Save the selected answer.
    answers[question_id] = answer

    # Finish immediately if all 30 are answered.
    if len(answers) == len(questions):
        finish_instant_quiz("all_answered")
        st.rerun()

    # First continue forward.
    next_index = None

    for index in range(current_index + 1, len(questions)):

        if questions[index]["id"] not in answers:
            next_index = index
            break

    # After reaching the end, return to earlier
    # unanswered questions, starting from Question 1.
    if next_index is None:

        for index in range(current_index):

            if questions[index]["id"] not in answers:
                next_index = index
                break

    if next_index is not None:
        st.session_state.instant_question_index = next_index

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
        st.rerun()


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
           MOBILE PAGINATION SCROLLING
           ================================= */

        .st-key-instant_pagination_scroll {
            width: 100% !important;
            max-width: 100% !important;
            overflow-x: auto !important;
            overflow-y: hidden !important;
            -webkit-overflow-scrolling: touch;
            overscroll-behavior-x: contain;
            scrollbar-width: thin;
            scrollbar-color: #64748b transparent;
            padding: 8px 0 12px !important;
        }

        /*
           Streamlit's horizontal container
           must not wrap question numbers.
        */

        .st-key-instant_pagination_scroll
        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            width: max-content !important;
            min-width: 100%;
            gap: 8px !important;
        }

        /*
           Some Streamlit versions use
           vertical blocks inside horizontal
           containers. Keep the direct
           children on one row.
        */

        .st-key-instant_pagination_scroll
        > div[data-testid="stVerticalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            width: max-content !important;
            min-width: 100%;
            gap: 8px !important;
        }

        .st-key-instant_pagination_scroll
        [data-testid="stHorizontalBlock"] > div {
            flex: 0 0 60px !important;
            width: 60px !important;
            min-width: 60px !important;
            max-width: 60px !important;
        }

        /*
           Prevent each numbered button
           from shrinking or wrapping.
        */

        .st-key-instant_pagination_scroll
        [class*="st-key-instant_"] {
            flex-shrink: 0 !important;
        }

        .st-key-instant_pagination_scroll button {
            width: 55px !important;
            min-width: 55px !important;
            height: 46px !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            white-space: nowrap !important;
        }

        /* =================================
           PAGINATION COLORS
           ================================= */

        [class*="st-key-instant_correct_"] button {
            background-color: #15803d !important;
            color: white !important;
            border-color: #22c55e !important;
        }

        [class*="st-key-instant_wrong_"] button {
            background-color: #b91c1c !important;
            color: white !important;
            border-color: #ef4444 !important;
        }

        [class*="st-key-instant_unanswered_"] button {
            background-color: #1e293b !important;
            color: white !important;
            border-color: #475569 !important;
        }

        /* =================================
           COMPACT RESULTS BADGES
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
# PAGINATION
# ONLY ONE PAGINATION FUNCTION
# =========================================

# =========================================
# INSTANT CORRECTION PAGINATION
# Same working structure as Translate Mode
# =========================================

def show_instant_pagination():
    """Display all 30 question numbers in one horizontal row."""

    questions = st.session_state.instant_questions
    answers = st.session_state.instant_answers

    st.markdown(
        """
        <style>
        /* Correct answers: green */
        [class*="st-key-instant_correct_"] button {
            background-color: #15803d !important;
            color: white !important;
            border-color: #22c55e !important;
        }

        /* Incorrect answers: red */
        [class*="st-key-instant_wrong_"] button {
            background-color: #b91c1c !important;
            color: white !important;
            border-color: #ef4444 !important;
        }

        /* Unanswered questions: dark */
        [class*="st-key-instant_unanswered_"] button {
            background-color: #1e293b !important;
            color: white !important;
            border-color: #475569 !important;
        }

        /* Consistent numbered buttons */
        [class*="st-key-instant_page_"] button {
            border-radius: 10px !important;
            font-weight: 600 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Same horizontal container used in quiz.py.
    with st.container(
        key="instant_pagination_scroll",
        horizontal=True,
        horizontal_alignment="left",
        gap="small",
        width="stretch",
    ):

        for index in range(len(questions)):

            number = index + 1
            question = questions[index]
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
                key=f"instant_{status}_{number}"
            ):

                if st.button(
                    str(number),
                    key=f"instant_page_{number}",
                    width=75,
                ):
                    go_to_instant_question(index)


    questions = st.session_state.instant_questions
    answers = st.session_state.instant_answers

    # Only one scroll container is created.
    with st.container(
        key="instant_pagination_scroll",
        horizontal=True,
        horizontal_alignment="left",
        gap="small",
        width="stretch",
    ):

        for index, question in enumerate(questions):

            question_id = question["id"]

            # Determine the question status.
            if question_id not in answers:

                status = "unanswered"

            else:

                expected = normalize_instant_answer(
                    question["correct_answer"]
                )

                status = (
                    "correct"
                    if answers[question_id] == expected
                    else "wrong"
                )

            # Each question gets a unique key.
            with st.container(
                key=f"instant_{status}_{index + 1}"
            ):

                if st.button(
                    str(index + 1),
                    key=f"instant_page_{index + 1}",
                    width=60,
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

        from quiz import get_question_image
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
    # ONLY ONE PAIR
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
    # PREVIOUS / NEXT BUTTONS
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
    # COMPACT RESULT BADGES
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

    # Display result badges only once.
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


# =========================================
# MAIN INSTANT CORRECTION PAGE
# =========================================

def show_instant_correction():

    initialize_instant_quiz()

    # Load Instant Correction styling.
    load_instant_styles()

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

    # Live countdown.
    show_instant_timer()

    # Question, answers, and pagination.
    show_instant_question()
