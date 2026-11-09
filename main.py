
import streamlit as st

from dashboard import show_dashboard
from styles_loader import load_css
from components.header import show_header
from components.footer import show_footer
from components.quiz_modal import show_quiz_modal
from quiz import show_quiz


st.set_page_config(
    page_title="Patente B",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None,
    }
)

load_css()


# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "welcome"

if "open_quiz_modal" not in st.session_state:
    st.session_state.open_quiz_modal = False

if "quiz_translation" not in st.session_state:
    st.session_state.quiz_translation = False

if "quiz_auto_correction" not in st.session_state:
    st.session_state.quiz_auto_correction = False

if "quiz_mode" not in st.session_state:
    st.session_state.quiz_mode = None


# Shared header - hidden on quiz page
if st.session_state.page != "quiz":
    show_header()


# Page navigation
if st.session_state.page == "welcome":

    st.title("Welcome to Patente B")
    st.write("Prepare for your Italian driving theory exam.")

    if st.button("OK"):
        st.session_state.page = "dashboard"
        st.rerun()


elif st.session_state.page == "dashboard":

    show_dashboard()


elif st.session_state.page == "quiz":

    # Single-line quiz header with back navigation
    if st.button("‹‹ Quiz Translate Mode", key="quiz_back"):
        st.session_state.page = "dashboard"
        st.rerun()

    show_quiz()


elif st.session_state.page == "coming_soon":

    st.title("🚧 Coming Soon")
    st.info("Auto Correction will be available in a future update.")

    if st.button("Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()


elif st.session_state.page == "results":

    st.title("My Results")
    st.info("Results page coming soon.")


elif st.session_state.page == "settings":

    st.title("Settings")
    st.info("Settings page coming soon.")


# Shared footer
show_footer()


# Quiz modal
if st.session_state.open_quiz_modal:

    st.session_state.open_quiz_modal = False

    show_quiz_modal()
