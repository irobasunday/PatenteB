
"""Patente B — Learning Page."""

from pathlib import Path

import streamlit as st

from learning.learning_questions import get_learning_questions
from learning.learning_translation import get_or_create_translation
from learning.learning_audio import show_learning_audio


# ==========================================
# PROJECT PATHS
# ==========================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
IMAGE_DIR = PROJECT_DIR / "img_sign"


# ==========================================
# LOAD LEARNING CSS
# ==========================================

def load_learning_css():
    """Load the existing Learning Page CSS."""

    css_path = Path(__file__).parent / "learning.css"

    if css_path.is_file():
        css = css_path.read_text(encoding="utf-8")
        st.html(f"<style>{css}</style>")


# ==========================================
# FIND QUESTION IMAGE
# ==========================================

def get_question_image(image_path):
    """Find an existing image inside img_sign."""

    if not image_path:
        return None

    relative_path = str(image_path).strip().replace("\\", "/")

    if not relative_path:
        return None

    relative_path = relative_path.lstrip("/")

    if relative_path.startswith("img_sign/"):
        relative_path = relative_path[len("img_sign/"):]

    image_root = IMAGE_DIR.resolve()
    image_file = (image_root / relative_path).resolve()

    if not image_file.is_relative_to(image_root):
        return None

    if not image_file.is_file():
        return None

    if image_file.suffix.lower() not in {
        ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"
    }:
        return None

    return image_file


# ==========================================
# DISPLAY INDIVIDUAL QUESTION
# ==========================================


# ==========================================
# DISPLAY INDIVIDUAL QUESTION
# ==========================================

def show_question(question, number, answer_type, key_prefix="learning"):
    """Display image, Italian question and translation."""

    question_id = question["id"]
    italian_text = str(question["question"])

    translation_key = f"{key_prefix}_translation_{question_id}"
    expanded_key = f"{key_prefix}_expanded_{question_id}"

    with st.container(
        key=f"{key_prefix}_question_{question_id}",
        border=True,
    ):
        if answer_type == "VERO":
            st.markdown(f"**🟢 VERO — {number}**")
        else:
            st.markdown(f"**🔴 FALSO — {number}**")

        image_file = get_question_image(
            question.get("image_path")
        )

        if image_file is not None:
            left, center, right = st.columns([1, 2, 1])

            with center:
                st.image(
                    str(image_file),
                    use_container_width=True,
                )

        st.write(italian_text)

        show_learning_audio(
            question_text=italian_text,
            question_id=question_id,
        )

        expanded = st.session_state.get(
            expanded_key,
            False,
        )

        arrow = "⌄" if expanded else "›"

        if st.button(
            f"{arrow}  🌐 English Translation",
            key=f"{key_prefix}_toggle_{question_id}",
            use_container_width=True,
        ):
            expanded = not expanded
            st.session_state[expanded_key] = expanded

        if expanded:
            if translation_key not in st.session_state:
                with st.spinner("Loading translation..."):
                    try:
                        translation = get_or_create_translation(
                            question_id,
                            italian_text,
                        )

                        if translation:
                            st.session_state[translation_key] = translation
                        else:
                            st.warning(
                                "English translation is unavailable."
                            )

                    except Exception:
                        st.warning(
                            "Unable to load English translation."
                        )

            if translation_key in st.session_state:
                st.write(
                    st.session_state[translation_key]
                )


# ==========================================
# FAILED QUIZ QUESTION MODAL
# ==========================================

@st.dialog("📖 Study Failed Question", width="large")
def show_failed_question_modal(question, number, answer_type):
    """Display only the linked failed quiz question."""

    st.caption("Quiz Translate Mode — Question Review")

    show_question(
        question,
        number,
        answer_type,
        key_prefix="failed_modal",
    )

    st.divider()

    if st.button(
        "Close",
        key="close_failed_question_modal",
        use_container_width=True,
        type="primary",
    ):
        st.session_state.argomenti_question_id = None

        st.query_params.pop("question", None)

        st.session_state._last_url_signature = (
            "argomenti",
            st.session_state.get("argomenti_category_id"),
            st.session_state.get("argomenti_subtopic_id"),
            None,
        )

        st.rerun()


# ==========================================
# MAIN LEARNING PAGE
# ==========================================

def show_learning_page(subtopic_id, subtopic_name):
    """Display learning questions or the subtopic quiz."""

    load_learning_css()

    active_key = f"subtopic_quiz_{subtopic_id}_active"
    
    target_question_id = st.session_state.get(
        "argomenti_question_id"
    )


    # ======================================
    # DISPLAY ACTIVE SUBTOPIC QUIZ
    # ======================================

    
    if (
        target_question_id is None
        and st.session_state.get(active_key, False)
    ):

        from learning.learning_quiz import show_subtopic_quiz

        show_subtopic_quiz(
            subtopic_id,
            subtopic_name,
        )
        return

    # ======================================
    # FETCH QUESTIONS FROM POSTGRESQL
    # ======================================

    try:
        vero_questions, falso_questions = (
            get_learning_questions(subtopic_id)
        )

    except Exception as error:
        st.error("Unable to load learning questions.")
        st.exception(error)
        return
    
    # ======================================
    # FIND THE EXACT FAILED QUESTION
    # ======================================

    linked_question = None

    if target_question_id is not None:

        for answer_type, questions in (
            ("VERO", vero_questions),
            ("FALSO", falso_questions),
        ):
            for number, question in enumerate(
                questions,
                start=1,
            ):
                if int(question["id"]) == int(target_question_id):

                    linked_question = (
                        question,
                        number,
                        answer_type,
                    )
                    break

            if linked_question is not None:
                break


    total_questions = (
        len(vero_questions) + len(falso_questions)
    )

    if total_questions == 0:
        st.info(
            "No questions available for this subtopic."
        )
        return

    # ======================================
    # VERO QUESTIONS
    # ======================================

    st.markdown(
        f"### 🟢 Domande VERO ({len(vero_questions)})"
    )

    for number, question in enumerate(
        vero_questions,
        start=1,
    ):
        show_question(
            question,
            number,
            "VERO",
        )

    # ======================================
    # FALSO QUESTIONS
    # ======================================

    st.markdown(
        f"### 🔴 Domande FALSO ({len(falso_questions)})"
    )

    for number, question in enumerate(
        falso_questions,
        start=1,
    ):
        show_question(
            question,
            number,
            "FALSO",
        )

    # ======================================
    # TAKE QUIZ BUTTON
    # ======================================

    st.divider()

    st.markdown(
        f"**Total questions: {total_questions}**"
    )

    if st.button(
        "📝 Take Quiz",
        key=f"learning_take_quiz_{subtopic_id}",
        use_container_width=True,
        type="primary",
    ):
        from learning.learning_quiz import start_subtopic_quiz

        try:
            started = start_subtopic_quiz(subtopic_id)

            if started:
                st.rerun()
            else:
                st.warning(
                    "No quiz questions are available."
                )

        except Exception as error:
            st.error("Unable to start subtopic quiz.")
            st.exception(error)

    
    # ======================================
    # OPEN FAILED QUESTION MODAL
    # ======================================

    if target_question_id is not None:

        if linked_question is None:
            st.warning(
                "The linked question was not found "
                "in this subtopic."
            )

        else:
            question, number, answer_type = linked_question

            show_failed_question_modal(
                question,
                number,
                answer_type,
            )


   