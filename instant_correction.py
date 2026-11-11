
import math
from datetime import datetime, timedelta, timezone
from textwrap import dedent

import streamlit as st

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

    if get_instant_remaining_seconds() == 0:
        finish_instant_quiz("time_expired")
        st.rerun()

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

    if len(answers) == len(questions):
        finish_instant_quiz("all_answered")

    st.rerun()


# =========================================
# INSTANT CORRECTION QUESTION INTERFACE
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

    st.progress(len(answers) / len(questions))

    with st.container(border=True):

        st.markdown(f"### DOMANDA {index + 1}")

        st.write(question["question"])

        # Show the original Italian question image.
        from quiz import get_question_image
        from audio_player import show_italian_audio

        image_file = get_question_image(
            question.get("image_path")
        )

        if image_file:
            st.image(str(image_file), width=150)

        show_italian_audio(
            question_text=str(question["question"]),
            question_id=question_id,
        )

    # Check whether this question has been answered.
    already_answered = question_id in answers

    if already_answered:

        selected = answers[question_id]

        correct_answer = normalize_instant_answer(
            question["correct_answer"]
        )

        if selected == correct_answer:
            st.success("✓ Correct answer!")
        else:
            st.error("✕ Incorrect answer!")
            st.markdown(
                "**Correct answer: "
                + ("VERO" if correct_answer else "FALSO")
                + "**"
            )

    # Keep buttons clickable so a locked answer
    # produces the warning toast.
    vero_col, falso_col = st.columns(2)

    with vero_col:
        if st.button(
            "VERO",
            key=f"instant_vero_{question_id}",
            use_container_width=True,
        ):
            select_instant_answer(question_id, True)

    with falso_col:
        if st.button(
            "FALSO",
            key=f"instant_falso_{question_id}",
            use_container_width=True,
        ):
            select_instant_answer(question_id, False)

    # =====================================
    # PREVIOUS / NEXT NAVIGATION
    # =====================================

    st.divider()

    previous_col, next_col = st.columns(2)

    with previous_col:
        if st.button(
            "← Previous",
            key="instant_previous",
            disabled=index == 0,
            use_container_width=True,
        ):
            go_to_instant_question(index - 1)

    with next_col:
        if st.button(
            "Next →",
            key="instant_next",
            disabled=index == len(questions) - 1,
            use_container_width=True,
        ):
            go_to_instant_question(index + 1)

    # Display green/red/default pagination.
    show_instant_pagination()


# =========================================
# INSTANT CORRECTION NAVIGATION
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
# INSTANT CORRECTION PAGINATION
# =========================================

def show_instant_pagination():

    questions = st.session_state.instant_questions
    answers = st.session_state.instant_answers

    st.markdown(
        """
        <style>
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

        [class*="st-key-instant_pagination_scroll"] {
            margin-top: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(
        key="instant_pagination_scroll",
        horizontal=True,
        horizontal_alignment="left",
        gap="small",
        width="stretch",
    ):

        for index, question in enumerate(questions):

            question_id = question["id"]

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

            with st.container(
                key=f"instant_{status}_{index + 1}"
            ):

                if st.button(
                    str(index + 1),
                    key=f"instant_page_{index + 1}",
                    width=65,
                ):
                    go_to_instant_question(index)


# =========================================
# INSTANT CORRECTION TIMER
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
# INSTANT CORRECTION RESULTS DASHBOARD
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
        int((finished_at - started_at).total_seconds())
    )

    minutes, seconds = divmod(elapsed_seconds, 60)

    if passed:
        st.success("✓ PASS — Congratulations!")
    else:
        st.error("✕ FAIL — Keep practicing!")

    if st.session_state.instant_finish_reason == "time_expired":
        st.warning(
            "Time expired. Your quiz was submitted automatically."
        )
    else:
        st.info("All 30 questions completed.")

    # =====================================
    # COMPACT ROUNDED RESULT BADGES
    # =====================================

    st.markdown(
        """
        <style>
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

    # Dedent prevents Streamlit from displaying
    # the HTML as a Markdown code block.
    results_html = f"""
    <div class="instant-results">
        <div class="instant-result-badge instant-result-correct">
            <span class="instant-result-label">Correct</span>
            <span class="instant-result-value">{correct}</span>
        </div>

        <div class="instant-result-badge instant-result-wrong">
            <span class="instant-result-label">Wrong</span>
            <span class="instant-result-value">{wrong}</span>
        </div>

        <div class="instant-result-badge">
            <span class="instant-result-label">Unanswered</span>
            <span class="instant-result-value">{unanswered}</span>
        </div>

        <div class="instant-result-badge instant-result-wrong">
            <span class="instant-result-label">Total Errors</span>
            <span class="instant-result-value">{total_errors}</span>
        </div>

        <div class="instant-result-badge">
            <span class="instant-result-label">Time Taken</span>
            <span class="instant-result-value">{minutes:02d}:{seconds:02d}</span>
        </div>
    </div>
    """

    st.markdown(
        dedent(results_html).strip(),
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### Review Your Answers")

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

            st.write(question["question"])

            if question_id in answers:
                st.write(
                    "Your answer:",
                    "VERO" if selected else "FALSO"
                )
            else:
                st.write("Your answer: Not answered")

            st.write(
                "Correct answer:",
                "VERO" if expected else "FALSO"
            )


# =========================================
# MAIN INSTANT CORRECTION PAGE
# =========================================

def show_instant_correction():

    # Initialize the 30 questions and session state.
    initialize_instant_quiz()

    # Automatically finish when time expires.
    if (
        not st.session_state.instant_finished
        and get_instant_remaining_seconds() == 0
    ):
        finish_instant_quiz("time_expired")

    # Show results when the quiz is finished.
    if st.session_state.instant_finished:
        show_instant_results()
        return

    # Display the live 20-minute countdown.
    show_instant_timer()

    # Display the current question and pagination.
    show_instant_question()
