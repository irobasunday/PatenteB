
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
        # Quiz Practices Card
        with st.container(border=False, key="pb_quiz_card"):
            st.markdown(
                '<div class="pb-card-icon">📖</div>',
                unsafe_allow_html=True,
            )

            st.markdown("#### Quiz Practices")
            st.caption("Translate Mode & Instant Correction")

            if st.button(
                "Open Quiz ↗",
                key="dashboard_quiz",
                use_container_width=True,
            ):
                open_quiz()

    with col2:
        # Argomenti Card
        # Keep existing container key for CSS compatibility
        with st.container(border=False, key="pb_translate_card"):
            st.markdown(
                '<div class="pb-card-icon">📚</div>',
                unsafe_allow_html=True,
            )

            st.markdown("#### Argomenti")
            st.caption("Learn Italian driving theory in Italian and English")

            if st.button(
                "Open Argomenti ↗",
                key="dashboard_argomenti",
                use_container_width=True,
            ):
                navigate("argomenti")

    # Learning Progress - preserved
    with st.container(border=False, key="pb_progress_card"):
        st.markdown("#### Your Learning Progress")

        st.progress(0)

        st.caption(
            "Your progress will appear here "
            "once you begin practicing."
        )
