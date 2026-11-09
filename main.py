
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


# =========================================
# INITIALIZE SESSION STATE
# =========================================

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


# =========================================
# HEADER
# =========================================

if st.session_state.page == "quiz":

    # Compact quiz header
    with st.container(key="quiz_compact_header"):

        back_col, title_col, mode_col = st.columns(
            [1, 2, 4],
            vertical_alignment="center",
            gap="small"
        )

        with back_col:
            if st.button(
                "←",
                key="quiz_back_dashboard",
                help="Back to Dashboard",
            ):
                st.session_state.page = "dashboard"
                st.rerun()

        with title_col:
            st.markdown("**Quiz**")

        with mode_col:
            st.markdown(
                "<div style='text-align:right; "
                "white-space:nowrap; font-size:14px;'>"
                "<strong>Practice Mode</strong>"
                "</div>",
                unsafe_allow_html=True
            )

else:
    # Normal shared header on all other pages
    show_header()


# =========================================
# PAGE NAVIGATION
# =========================================

if st.session_state.page == "welcome":

    st.title("Welcome to Patente B")
    st.write("Prepare for your Italian driving theory exam.")

    if st.button("OK"):
        st.session_state.page = "dashboard"
        st.rerun()


elif st.session_state.page == "dashboard":

    show_dashboard()


elif st.session_state.page == "quiz":

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


# =========================================
# SHARED FOOTER
# =========================================

show_footer()


# =========================================
# QUIZ MODAL
# =========================================

if st.session_state.open_quiz_modal:

    st.session_state.open_quiz_modal = False

    show_quiz_modal()
