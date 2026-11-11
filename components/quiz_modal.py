
import streamlit as st


def select_translation():
    st.session_state.quiz_translation = True
    st.session_state.quiz_auto_correction = False


def select_auto_correction():
    st.session_state.quiz_auto_correction = True
    st.session_state.quiz_translation = False


@st.dialog("Choose Quiz Mode")
def show_quiz_modal():

    st.write("Select how you want to practice.")

    st.toggle(
        "Enable Translation",
        key="quiz_translation",
        on_change=select_translation,
        help="Practice 30 Italian questions with translation assistance.",
    )

    st.toggle(
        "Auto Correction",
        key="quiz_auto_correction",
        on_change=select_auto_correction,
        help="Practice 30 Italian questions with instant answer correction.",
    )

    st.divider()

    selected = (
        st.session_state.quiz_translation
        or st.session_state.quiz_auto_correction
    )

    if st.button(
        "OK",
        disabled=not selected,
        use_container_width=True,
        type="primary",
    ):

        if st.session_state.quiz_auto_correction:
            st.session_state.page = "instant_correction"
            st.session_state.quiz_mode = "instant_correction"

        elif st.session_state.quiz_translation:
            st.session_state.page = "quiz"
            st.session_state.quiz_mode = "translation"

        st.session_state.open_quiz_modal = False
        st.rerun()
