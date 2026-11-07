
import streamlit as st


def show_footer():
    """Display reusable footer navigation."""

    with st.container(key="pb_footer"):
        home, quiz, results, settings = st.columns(4)

        with home:
            if st.button("⌂ Home", key="footer_home"):
                st.session_state.page = "dashboard"
                st.rerun()

        with quiz:
            if st.button("📖 Quiz", key="footer_quiz"):
                st.session_state.open_quiz_modal = True
                st.rerun()

        with results:
            if st.button("📊 Results", key="footer_results"):
                st.session_state.page = "results"
                st.rerun()

        with settings:
            if st.button("⚙ Settings", key="footer_settings"):
                st.session_state.page = "settings"
                st.rerun()
