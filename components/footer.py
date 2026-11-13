
import streamlit as st


def show_footer():
    with st.container(key="pb_footer"):
        home, quiz, results, settings = st.columns(4)

        with home:
            if st.button(
                "⌂ Home",
                key="footer_home",
            ):
                st.session_state.page = "dashboard"
                st.session_state.recovery_handled = False

                st.session_state.argomenti_category_id = None
                st.session_state.argomenti_subtopic_id = None

                st.query_params.clear()

                st.session_state._last_url_signature = (
                    "dashboard",
                    None,
                    None,
                )

                st.rerun()

        with quiz:
            if st.button(
                "📖 Quiz",
                key="footer_quiz",
            ):
                st.session_state.open_quiz_modal = True
                st.rerun()

        with results:
            st.button(
                "📊 Results",
                key="footer_results",
                disabled=True,
                help="Results page coming soon",
            )

        with settings:
            st.button(
                "⚙ Settings",
                key="footer_settings",
                disabled=True,
                help="Settings page coming soon",
            )
