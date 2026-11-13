
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

    # Support both:
    # 123.png
    # img_sign/123.png

    relative_path = relative_path.lstrip("/")

    if relative_path.startswith("img_sign/"):
        relative_path = relative_path[len("img_sign/"):]

    image_root = IMAGE_DIR.resolve()
    image_file = (image_root / relative_path).resolve()

    # Prevent access outside the image folder.
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

def show_question(question, number, answer_type):
    """Display image, Italian question and translation."""

    question_id = question["id"]
    italian_text = str(question["question"])

    translation_key = f"learning_translation_{question_id}"
    expanded_key = f"learning_expanded_{question_id}"

    with st.container(
        key=f"learning_question_{question_id}",
        border=True,
    ):

        # VERO / FALSO label
        if answer_type == "VERO":
            st.markdown(f"**🟢 VERO — {number}**")
        else:
            st.markdown(f"**🔴 FALSO — {number}**")

        # ==================================
        # IMAGE ABOVE QUESTION
        # ==================================

        image_file = get_question_image(
            question.get("image_path")
        )
        if image_file is not None:
            left, center, right = st.columns([1, 2, 1])

            with center:
                st.image(
            str(image_file),
            use_container_width=True
        )

        

        # ==================================
        # ORIGINAL ITALIAN QUESTION
        # ==================================

        st.write(italian_text)
        show_learning_audio(
        question_text=italian_text,
        question_id=question_id,
        )

        # ==================================
        # ENGLISH TRANSLATION
        # ==================================

        expanded = st.session_state.get(
            expanded_key,
            False,
        )

        arrow = "⌄" if expanded else "›"

        if st.button(
            f"{arrow}  🌐 English Translation",
            key=f"learning_toggle_{question_id}",
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
# MAIN LEARNING PAGE
# ==========================================

def show_learning_page(subtopic_id, subtopic_name):
    """
    Display all questions belonging to a subtopic.

    VERO questions appear first.
    FALSO questions appear afterward.
    """

    load_learning_css()

    # ==================================
    # FETCH QUESTIONS FROM POSTGRESQL
    # ==================================

    try:
        vero_questions, falso_questions = (
            get_learning_questions(subtopic_id)
        )

    except Exception as error:
        st.error("Unable to load learning questions.")
        st.exception(error)
        return

    total_questions = (
        len(vero_questions) + len(falso_questions)
    )

    if total_questions == 0:
        st.info(
            "No questions available for this subtopic."
        )
        return

    # ==================================
    # VERO QUESTIONS
    # ==================================

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

    # ==================================
    # FALSO QUESTIONS
    # ==================================

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

    # ==================================
    # TAKE QUIZ BUTTON
    # ==================================

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
        st.info(
            "The subtopic quiz will be connected "
            "in the next development step."
        )
