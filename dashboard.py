
import streamlit as st


def navigate(page):
    """Navigate using the existing app session state."""
    st.session_state.page = page
    st.rerun()


def open_quiz():
    """Open the quiz modal with both options OFF by default."""

    # Reset quiz mode selections
    st.session_state.quiz_translation = False
    st.session_state.quiz_auto_correction = False

    # Open the quiz selection modal
    st.session_state.open_quiz_modal = True

    st.rerun()


def show_dashboard():
    """Display the Patente B dashboard."""

    st.markdown(
        """
        <div class="pb-dashboard-heading">
            <h2>Patente B Dashboard</h2>
            <p>Your driving theory preparation</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Dashboard cards
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        # Quiz Practice Card
        with st.container(border=False, key="pb_quiz_card"):
            st.markdown(
                '<div class="pb-card-icon">📖</div>',
                unsafe_allow_html=True,
            )
            st.markdown("#### Quiz Practices")
            st.caption("Exam Mode & Practice Mode")

            if st.button(
                "Open Quiz ↗",
                key="dashboard_quiz",
                use_container_width=True,
            ):
                open_quiz()

        # My Results Card
        with st.container(border=False, key="pb_results_card"):
            st.markdown(
                '<div class="pb-card-icon">📊</div>',
                unsafe_allow_html=True,
            )
            st.markdown("#### My Results")
            st.caption("Track your progress")

            if st.button(
                "View Results ↗",
                key="dashboard_results",
                use_container_width=True,
            ):
                navigate("results")

    with col2:
        # Translate Mode Card
        with st.container(border=False, key="pb_translate_card"):
            st.markdown(
                '<div class="pb-card-icon">🌐</div>',
                unsafe_allow_html=True,
            )
            st.markdown("#### Translate Mode")
            st.caption("Learn in English")

            if st.button(
                "Open Translate ↗",
                key="dashboard_translate",
                use_container_width=True,
            ):
                open_quiz()

        # Settings Card
        with st.container(border=False, key="pb_settings_card"):
            st.markdown(
                '<div class="pb-card-icon">⚙️</div>',
                unsafe_allow_html=True,
            )
            st.markdown("#### Settings")
            st.caption("Preferences")

            if st.button(
                "Open Settings ↗",
                key="dashboard_settings",
                use_container_width=True,
            ):
                navigate("settings")

    # Learning Progress
    with st.container(border=False, key="pb_progress_card"):
        st.markdown("#### Your Learning Progress")

        st.progress(0)

        st.caption(
            "Your progress will appear here "
            "once you begin practicing."
        )
