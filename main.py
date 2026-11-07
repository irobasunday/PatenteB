
import streamlit as st

from dashboard import show_dashboard
from styles_loader import load_css
from components.header import show_header
from components.footer import show_footer


st.set_page_config(
    page_title="Patente B",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a Bug": None,
        "About": None
    }
)


load_css()

if "page" not in st.session_state:
    st.session_state.page = "welcome"

if "open_quiz_modal" not in st.session_state:
    st.session_state.open_quiz_modal = False


# Shared header on every page
show_header()

# Main page content
if st.session_state.page == "welcome":

    st.title("Welcome to Patente B")
    st.write("Prepare for your Italian driving theory exam.")

    if st.button("OK"):
        st.session_state.page = "dashboard"
        st.rerun()

elif st.session_state.page == "dashboard":
    show_dashboard()

elif st.session_state.page == "results":
    st.title("My Results")
    st.info("Results page coming soon.")

elif st.session_state.page == "settings":
    st.title("Settings")
    st.info("Settings page coming soon.")


# Shared footer on every page
show_footer()
