
"""Patente B — Timed subtopic VERO/FALSO quiz."""

import random
import time
from database import get_or_create_translation
import streamlit as st
import requests
from browser_identity import (
    get_browser_id,
    validate_browser_id,
    ensure_session_browser_id,
)
from learning.learning_questions import get_learning_questions
from learning.learning_progress import save_quiz_progress
from learning.learning_audio import show_learning_audio
from learning.learning_page import get_question_image


QUIZ_DURATION_SECONDS = 20 * 60


# ==========================================
# SESSION STATE HELPERS
# ==========================================

def quiz_key(subtopic_id, name):
    return f"subtopic_quiz_{subtopic_id}_{name}"


def count_answered(questions, answers):
    """Count answers belonging to this quiz."""

    return sum(
        question["id"] in answers
        for question in questions
    )


def all_questions_answered(questions, answers):
    """Require an answer for every question."""

    return (
        bool(questions)
        and count_answered(questions, answers) == len(questions)
    )


# ==========================================
# QUIZ STYLING
# ==========================================

def load_quiz_css():
    st.html(
        """
        <style>

        /* Horizontally scrollable question navigation */

        [class*="st-key-subtopic_quiz_pagination_"] {
            width: 100% !important;
            max-width: 100% !important;
            min-width: 0 !important;
            overflow-x: auto !important;
            overflow-y: hidden !important;
            -webkit-overflow-scrolling: touch;
            touch-action: pan-x;
            overscroll-behavior-x: contain;
            scrollbar-width: thin;
            padding: 6px 0 12px;
        }

        [class*="st-key-subtopic_quiz_pagination_"]
        [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-wrap: nowrap !important;
            width: max-content !important;
            min-width: max-content !important;
            gap: 8px !important;
        }

        [class*="st-key-subtopic_quiz_pagination_"]
        [data-testid="stHorizontalBlock"]
        > [data-testid="stColumn"] {
            flex: 0 0 48px !important;
            width: 48px !important;
            min-width: 48px !important;
        }

        [class*="st-key-subtopic_quiz_page_"] button {
            width: 48px !important;
            min-width: 48px !important;
            height: 44px !important;
            padding: 0 !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
        }

        /* Answered pagination buttons */

        [class*="st-key-subtopic_quiz_page_answered_"]
        button,
        [class*="st-key-subtopic_quiz_page_active_answered_"]
        button {
            background: #166534 !important;
            border: 2px solid #22c55e !important;
            color: white !important;
        }

        /* Active question red border */

        [class*="st-key-subtopic_quiz_page_active_"]
        button {
            border: 3px solid #ef4444 !important;
        }

        /* VERO green */

        [class*="st-key-subtopic_quiz_vero_"] button {
            background: #166534 !important;
            border: 2px solid #22c55e !important;
            color: white !important;
            min-height: 54px !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
        }

        /* FALSO red */

        [class*="st-key-subtopic_quiz_falso_"] button {
            background: #991b1b !important;
            border: 2px solid #ef4444 !important;
            color: white !important;
            min-height: 54px !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
        }

        @media (max-width: 768px) {

            [data-testid="stAppViewContainer"] {
                overflow-y: auto !important;
                -webkit-overflow-scrolling: touch;
            }

            [data-testid="stMainBlockContainer"] {
                padding-bottom: 110px !important;
                min-width: 0 !important;
            }

            [class*="st-key-subtopic_quiz_pagination_"] {
                overflow-x: auto !important;
                max-width: 100% !important;
            }
        }

        </style>
        """
    )


# ==========================================
# START QUIZ
# ==========================================

def start_subtopic_quiz(subtopic_id):
    """Start a fresh timed quiz."""
    
    browser_id = ensure_session_browser_id()

    if not browser_id:
        st.error(
            "Unable to start the quiz because "
            "student identity is not ready."
        )
        return False


    vero, falso = get_learning_questions(subtopic_id)

    questions = [
        dict(question)
        for question in vero + falso
    ]

    random.shuffle(questions)

    if not questions:
        return False

    st.session_state[
        quiz_key(subtopic_id, "questions")
    ] = questions

    st.session_state[
        quiz_key(subtopic_id, "answers")
    ] = {}

    st.session_state[
        quiz_key(subtopic_id, "index")
    ] = 0

    st.session_state[
        quiz_key(subtopic_id, "submit_screen")
    ] = False

    st.session_state[
        quiz_key(subtopic_id, "result")
    ] = None

    st.session_state[
        quiz_key(subtopic_id, "active")
    ] = True

    st.session_state[
        quiz_key(subtopic_id, "deadline")
    ] = time.time() + QUIZ_DURATION_SECONDS

    return True


# ==========================================
# CLOSE QUIZ
# ==========================================

def close_subtopic_quiz(subtopic_id):
    """Return to the learning page."""

    st.session_state[
        quiz_key(subtopic_id, "active")
    ] = False

    st.rerun()


# ==========================================
# SAVE ANSWER AND ADVANCE
# ==========================================

def select_answer(
    subtopic_id,
    question_id,
    answer,
    total,
):
    """
    Save the selected answer.

    Advance to the next question.

    Only show the submission screen when
    every question has been answered.
    """

    answers_key = quiz_key(
        subtopic_id,
        "answers",
    )

    index_key = quiz_key(
        subtopic_id,
        "index",
    )

    submit_key = quiz_key(
        subtopic_id,
        "submit_screen",
    )

    questions = st.session_state.get(
        quiz_key(subtopic_id, "questions"),
        [],
    )

    answers = dict(
        st.session_state.get(
            answers_key,
            {},
        )
    )

    answers[question_id] = answer

    st.session_state[answers_key] = answers

    index = st.session_state.get(
        index_key,
        0,
    )

    # Move forward if this is not the
    # final question.

    if index < total - 1:

        st.session_state[index_key] = (
            index + 1
        )

        st.session_state[submit_key] = False

    else:

        # On the final question, check
        # whether all answers exist.

        if all_questions_answered(
            questions,
            answers,
        ):

            st.session_state[submit_key] = True

        else:

            st.session_state[submit_key] = False

            # Return to the first unanswered
            # question instead of showing Submit.

            for number, question in enumerate(
                questions
            ):

                if question["id"] not in answers:

                    st.session_state[index_key] = (
                        number
                    )

                    break

    st.rerun()


# ==========================================
# SAVE QUIZ TO POSTGRESQL
# ==========================================

def submit_quiz(subtopic_id, answers):
    """
    Save the completed quiz using the
    student's existing anonymous identity.

    Never create a replacement student ID
    during submission.
    """

    questions = st.session_state.get(
        quiz_key(subtopic_id, "questions"),
        [],
    )

    # Prevent incomplete submission.

    if not all_questions_answered(
        questions,
        answers,
    ):

        st.warning(
            "Please answer every question "
            "before submitting."
        )

        return False

    # Use the existing student identity.

    browser_id = validate_browser_id(
        st.session_state.get("browser_id")
    )

    if not browser_id:

        browser_id = validate_browser_id(
            get_browser_id()
        )

    if not browser_id:

        st.error(
            "Student identity is not ready. "
            "Your answers are still available "
            "in this quiz session, but have "
            "not been saved to PostgreSQL."
        )

        return False

    st.session_state.browser_id = browser_id

    try:

        result = save_quiz_progress(
            browser_id,
            subtopic_id,
            answers,
        )

    except Exception as error:

        st.error(
            "Unable to save quiz results."
        )

        st.exception(error)

        return False

    # Store result only after a successful
    # database operation.

    st.session_state[
        quiz_key(subtopic_id, "result")
    ] = result

    return True


# ==========================================
# TIMER
# ==========================================

@st.fragment(run_every="1s")
def show_quiz_timer(subtopic_id):
    """Display the remaining quiz time."""

    if st.session_state.get(
        quiz_key(subtopic_id, "result")
    ) is not None:
        return

    deadline = st.session_state.get(
        quiz_key(subtopic_id, "deadline"),
        time.time(),
    )

    remaining = max(
        0,
        int(deadline - time.time()),
    )

    minutes, seconds = divmod(
        remaining,
        60,
    )

    st.markdown(
        f"### ⏱️ {minutes:02d}:{seconds:02d}"
    )

    if remaining <= 0:
        st.rerun(scope="app")


# ==========================================
# QUESTION PAGINATION
# ==========================================

def show_question_pagination(
    subtopic_id,
    questions,
    answers,
    current_index,
):
    """Display numbered question buttons."""

    st.markdown("**Questions**")

    with st.container(
        key=f"subtopic_quiz_pagination_{subtopic_id}",
    ):

        columns = st.columns(
            len(questions),
            gap="small",
        )

        for number, (column, question) in enumerate(
            zip(columns, questions)
        ):

            answered = (
                question["id"] in answers
            )

            active = (
                number == current_index
            )

            if active:

                status = (
                    "active_answered"
                    if answered
                    else "active_unanswered"
                )

            elif answered:

                status = "answered"

            else:

                status = "unanswered"

            with column:

                with st.container(
                    key=(
                        f"subtopic_quiz_page_{status}_"
                        f"{subtopic_id}_{number}"
                    )
                ):

                    if st.button(
                        str(number + 1),
                        key=quiz_key(
                            subtopic_id,
                            f"jump_{number}",
                        ),
                    ):

                        st.session_state[
                            quiz_key(
                                subtopic_id,
                                "index",
                            )
                        ] = number

                        st.rerun()


# ==========================================
# ANSWER BUTTONS
# ==========================================

def show_answer_buttons(
    subtopic_id,
    question_id,
    total,
):
    """Show VERO and FALSO answer buttons."""

    st.markdown("**Choose your answer**")

    vero_col, falso_col = st.columns(2)

    with vero_col:

        with st.container(
            key=(
                f"subtopic_quiz_vero_"
                f"{subtopic_id}_{question_id}"
            )
        ):

            if st.button(
                "✓ VERO",
                key=quiz_key(
                    subtopic_id,
                    f"vero_{question_id}",
                ),
                use_container_width=True,
            ):

                select_answer(
                    subtopic_id,
                    question_id,
                    True,
                    total,
                )

    with falso_col:

        with st.container(
            key=(
                f"subtopic_quiz_falso_"
                f"{subtopic_id}_{question_id}"
            )
        ):

            if st.button(
                "✕ FALSO",
                key=quiz_key(
                    subtopic_id,
                    f"falso_{question_id}",
                ),
                use_container_width=True,
            ):

                select_answer(
                    subtopic_id,
                    question_id,
                    False,
                    total,
                )

# ==========================================
# ITALIAN TO ENGLISH TRANSLATION
# ==========================================

@st.cache_data(show_spinner=False, ttl=86400)

def translate_learning_question(question_id, question_text):
    """
    Retrieve a saved translation from PostgreSQL.
    If missing, translate and save it using
    the existing database function.
    """
    return get_or_create_translation(
        question_id,
        question_text,
    )

    """Translate an Italian question into English."""

    try:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={
                "q": question_text,
                "langpair": "it|en",
            },
            timeout=12,
        )

        response.raise_for_status()
        data = response.json()

        if data.get("responseStatus") != 200:
            return None

        translated = data.get(
            "responseData", {}
        ).get("translatedText", "")

        if not isinstance(translated, str):
            return None

        translated = translated.strip()

        if not translated:
            return None

        return translated

    except (requests.RequestException, ValueError):
        return None



def show_question_translation(
    subtopic_id,
    question_id,
    question_text,
):
    """Show English translation when requested."""

    translation_key = quiz_key(
        subtopic_id,
        f"translation_visible_{question_id}",
    )

    if st.button(
        "🌐 Translate to English",
        key=f"argomenti_translate_button_{subtopic_id}_{question_id}",
    ):
        st.session_state[translation_key] = True

    if st.session_state.get(translation_key, False):
        with st.spinner("Translating..."):
            translation = translate_learning_question(
                question_id,
                question_text,
            )

        if translation:
            st.info(f"🇬🇧 {translation}")
        else:
            st.warning(
                "Translation is temporarily unavailable."
            )


# ==========================================
# MAIN QUIZ
# ==========================================

def show_subtopic_quiz(
    subtopic_id,
    subtopic_name,
):
    """Render the complete timed subtopic quiz."""

    load_quiz_css()

    st.subheader(
        f"📝 Quiz — {subtopic_name}"
    )

    if st.button(
        "← Back to Learning Page",
        key=quiz_key(
            subtopic_id,
            "back",
        ),
    ):

        close_subtopic_quiz(subtopic_id)

    questions = st.session_state.get(
        quiz_key(subtopic_id, "questions"),
        [],
    )

    if not questions:

        st.warning(
            "No quiz questions available."
        )

        return

    answers_key = quiz_key(
        subtopic_id,
        "answers",
    )

    index_key = quiz_key(
        subtopic_id,
        "index",
    )

    submit_key = quiz_key(
        subtopic_id,
        "submit_screen",
    )

    result_key = quiz_key(
        subtopic_id,
        "result",
    )

    answers = st.session_state.setdefault(
        answers_key,
        {},
    )

    total = len(questions)

    answered_count = count_answered(
        questions,
        answers,
    )

    all_answered = (
        answered_count == total
    )

    # ======================================
    # SUBMITTED RESULT
    # ======================================

    result = st.session_state.get(
        result_key
    )

    if result is not None:

        correct = result["correct"]
        result_total = result["total"]

        perfect_attempt = (
            result_total > 0
            and correct == result_total
        )

        if perfect_attempt:

            st.markdown(
                "## 🎉🏆 Congratulations!"
            )

            st.success(
                "You passed this lesson! "
                "Excellent work!"
            )

            st.markdown(
                f"### {correct} / {result_total}"
            )

            st.markdown(
                "**✅ All questions answered correctly!**"
            )

        else:

            st.markdown(
                "## 😢 Not Passed Yet"
            )

            st.markdown(
                f"### {correct} / {result_total}"
            )

            st.info(
                "Review this lesson and try again. "
                "You can do it!"
            )

        if st.button(
            (
                "📖 Back to Argomenti"
                if perfect_attempt
                else "📖 Repeat This Lesson"
            ),
            type="primary",
            use_container_width=True,
            key=quiz_key(
                subtopic_id,
                "result_back",
            ),
        ):

            close_subtopic_quiz(
                subtopic_id
            )

        if st.button(
            "🔄 Try Again",
            use_container_width=True,
            key=quiz_key(
                subtopic_id,
                "retry",
            ),
        ):

            try:

                if start_subtopic_quiz(
                    subtopic_id
                ):

                    st.rerun()

                else:

                    st.warning(
                        "No quiz questions available."
                    )

            except Exception as error:

                st.error(
                    "Unable to restart quiz."
                )

                st.exception(error)

        return

    # ======================================
    # TIMER
    # ======================================

    show_quiz_timer(subtopic_id)

    deadline = st.session_state.get(
        quiz_key(
            subtopic_id,
            "deadline",
        ),
        time.time(),
    )

    if time.time() >= deadline:

        st.warning(
            "Time is up!"
        )

        # Keep the requirement that every
        # question must be answered before
        # the student can submit.

        if all_answered:

            if submit_quiz(
                subtopic_id,
                answers,
            ):

                st.rerun()

        else:

            st.error(
                "The quiz time has expired "
                "before all questions were answered."
            )

            if st.button(
                "🔄 Try Again",
                key=quiz_key(
                    subtopic_id,
                    "timeout_retry",
                ),
                use_container_width=True,
            ):

                if start_subtopic_quiz(
                    subtopic_id
                ):

                    st.rerun()

        return

    # ======================================
    # SUBMIT SCREEN
    # ======================================

    if st.session_state.get(
        submit_key,
        False,
    ):

        if not all_answered:

            # Never allow an incomplete quiz
            # to remain on the submit screen.

            st.session_state[submit_key] = False

        else:

            st.markdown(
                "### Quiz completed"
            )

            st.write(
                f"You have answered "
                f"**{answered_count} of {total}** "
                f"questions."
            )

            if st.button(
                "✅ Submit Quiz",
                type="primary",
                use_container_width=True,
                key=quiz_key(
                    subtopic_id,
                    "submit",
                ),
            ):

                if submit_quiz(
                    subtopic_id,
                    answers,
                ):

                    st.rerun()

            if st.button(
                "← Back to Questions",
                use_container_width=True,
                key=quiz_key(
                    subtopic_id,
                    "back_to_questions",
                ),
            ):

                st.session_state[
                    submit_key
                ] = False

                st.rerun()

            return

    # ======================================
    # QUESTION SCREEN
    # ======================================

    index = st.session_state.get(
        index_key,
        0,
    )

    index = max(
        0,
        min(index, total - 1),
    )

    question = questions[index]

    question_id = question["id"]

    show_question_pagination(
        subtopic_id,
        questions,
        answers,
        index,
    )

    st.divider()

    st.write(
        f"**Question {index + 1} of {total}**"
    )

    st.progress(
        answered_count / total
    )

    st.caption(
        f"{answered_count} of {total} answered"
    )

    with st.container(border=True):

        image_file = get_question_image(
            question.get("image_path")
        )

        if image_file is not None:

            left, center, right = st.columns(
                [1, 2, 1]
            )

            with center:

                st.image(
                    str(image_file),
                    use_container_width=True,
                )

        st.write(
            question["question"]
        )

        
        show_learning_audio(
            question_text=str(
                question["question"]
            ),
            question_id=question_id,
        )
        show_question_translation(
    subtopic_id=subtopic_id,
    question_id=question_id,
    question_text=str(question["question"]),
)

        

        st.divider()


        show_answer_buttons(
            subtopic_id,
            question_id,
            total,
        )

    # ======================================
    # PREVIOUS / NEXT
    # ======================================

    previous_col, next_col = st.columns(2)

    with previous_col:

        if st.button(
            "← Previous",
            disabled=index == 0,
            use_container_width=True,
            key=quiz_key(
                subtopic_id,
                "previous",
            ),
        ):

            st.session_state[
                index_key
            ] = index - 1

            st.rerun()

    with next_col:

        if index < total - 1:

            if st.button(
                "Next →",
                use_container_width=True,
                key=quiz_key(
                    subtopic_id,
                    "next",
                ),
            ):

                st.session_state[
                    index_key
                ] = index + 1

                st.rerun()

        elif all_answered:

            # Submit is available only
            # when all questions are answered.

            if st.button(
                "Submit →",
                type="primary",
                use_container_width=True,
                key=quiz_key(
                    subtopic_id,
                    "finish",
                ),
            ):

                st.session_state[
                    submit_key
                ] = True

                st.rerun()

        else:

            st.info(
                f"Please answer all questions. "
                f"{answered_count} of {total} answered."
            )
