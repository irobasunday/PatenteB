
import streamlit as st

from browser_identity import get_browser_id

from quiz_attempt_storage import (
    load_latest_active_attempt,
    abandon_active_attempts,
)


# =========================================
# NAVIGATION
# =========================================

def navigate(page):
    if page == "dashboard":
        st.session_state.recovery_handled = False

    st.session_state.page = page
    st.rerun()


def open_quiz():
    st.session_state.quiz_translation = False
    st.session_state.quiz_auto_correction = False
    st.session_state.open_quiz_modal = True
    st.rerun()


# =========================================
# CLEAR SELECTED QUIZ SESSION
# =========================================

def clear_quiz_session(mode):

    if mode == "quiz":
        keys = (
            "quiz_questions",
            "quiz_attempt_id",
            "quiz_question_index",
            "quiz_answers",
            "quiz_started_at",
            "quiz_finished",
            "quiz_finished_at",
            "quiz_finish_reason",
            "quiz_retry_mode",
            "quiz_completion_prompt_shown",
            "quiz_show_completion_dialog",
            "quiz_submit_pending",
            "quiz_translations_visible",
            "quiz_translation_cache",
            "quiz_results_view",
        )

    else:
        keys = (
            "instant_questions",
            "instant_attempt_id",
            "instant_question_index",
            "instant_answers",
            "instant_started_at",
            "instant_finished",
            "instant_finish_reason",
            "instant_finished_at",
        )

    for key in keys:
        st.session_state.pop(key, None)


# =========================================
# RESUME UNFINISHED QUIZ
# =========================================

def resume_quiz(mode):

    clear_quiz_session(mode)

    st.session_state.recovery_handled = True

    if mode == "quiz":
        st.session_state.quiz_mode = "translate"
        st.session_state.page = "quiz"

    elif mode == "instant_correction":
        st.session_state.quiz_mode = "instant_correction"
        st.session_state.page = "instant_correction"

    st.rerun()


# =========================================
# ONE-TIME RECOVERY POPUP
# =========================================

@st.dialog(
    "Unfinished Quiz",
    dismissible=False,
)
def recovery_dialog(attempt):

    mode = attempt["mode"]
    attempt_id = attempt["id"]

    title = (
        "Translate Mode"
        if mode == "quiz"
        else "Instant Correction Mode"
    )

    question_ids = attempt.get("question_ids") or []
    answers = attempt.get("answers") or {}

    total = len(question_ids)
    answered = min(len(answers), total)

    completed = (
        answered / total
        if total > 0
        else 0
    )

    remaining = 1 - completed

    st.write(
        "You have an unfinished quiz. "
        "Would you like to continue?"
    )

    with st.container(border=True):

        st.markdown(f"#### {title}")

        st.progress(completed)

        st.caption(
            f"{answered} of {total} questions answered"
        )

        left, right = st.columns(2)

        with left:
            st.metric(
                "Completed",
                f"{completed * 100:.0f}%",
            )

        with right:
            st.metric(
                "Remaining",
                f"{remaining * 100:.0f}%",
            )

        if st.toggle(
            "Slide ON to continue",
            key=f"resume_attempt_{attempt_id}",
        ):
            resume_quiz(mode)

    st.caption(
        "Discarding this quiz permanently "
        "abandons its saved progress."
    )

    if st.button(
        "Discard Quiz",
        key=f"discard_attempt_{attempt_id}",
        use_container_width=True,
    ):

        browser_id = st.session_state.get(
            "browser_id"
        )

        if not browser_id:
            st.error(
                "Browser identification is unavailable."
            )
            return

        try:
            abandon_active_attempts(browser_id)

        except Exception as exc:
            st.error(
                f"Unable to discard quiz: {exc}"
            )
            return

        clear_quiz_session("quiz")
        clear_quiz_session("instant_correction")

        st.session_state.recovery_handled = True
        st.rerun()


# =========================================
# FAST RECOVERY CHECK
# =========================================

def check_recovery():

    if st.session_state.get(
        "recovery_handled", False
    ):
        return

    # Reuse the browser ID already identified
    # during this Streamlit session.
    browser_id = st.session_state.get(
        "browser_id"
    )

    if not browser_id:
        browser_id = get_browser_id()

    if not browser_id:
        return

    st.session_state.browser_id = browser_id

    try:
        attempt = load_latest_active_attempt(
            browser_id
        )

    except Exception as exc:
        st.error(
            f"Unable to check unfinished quiz: {exc}"
        )
        return

    if attempt is None:
        st.session_state.recovery_handled = True
        return

    recovery_dialog(attempt)


# =========================================
# ORIGINAL CLEAN DASHBOARD
# =========================================

def show_dashboard():

    st.markdown(
        '<div class="pb-dashboard-heading">'
        '<h2>Patente B Dashboard</h2>'
        '<p>Your driving theory preparation</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(
        2,
        gap="medium",
    )

    # =====================================
    # QUIZ PRACTICES
    # =====================================

    with col1:

        with st.container(
            border=False,
            key="pb_quiz_card",
        ):

            st.markdown(
                '<div class="pb-card-icon">📖</div>',
                unsafe_allow_html=True,
            )

            st.markdown("#### Quiz Practices")

            st.caption(
                "Translate Mode & Instant Correction"
            )

            if st.button(
                "Open Quiz ↗",
                key="dashboard_quiz",
                use_container_width=True,
            ):
                open_quiz()

    # =====================================
    # ARGOMENTI - UNCHANGED
    # =====================================

    with col2:

        with st.container(
            border=False,
            key="pb_translate_card",
        ):

            st.markdown(
                '<div class="pb-card-icon">📚</div>',
                unsafe_allow_html=True,
            )

            st.markdown("#### Argomenti")

            st.caption(
                "Learn Italian driving theory "
                "in Italian and English"
            )

            if st.button(
                "Open Argomenti ↗",
                key="dashboard_argomenti",
                use_container_width=True,
            ):
                navigate("argomenti")

    # =====================================
    # LEARNING PROGRESS - UNCHANGED
    # =====================================

    with st.container(
        border=False,
        key="pb_progress_card",
    ):

        st.markdown("#### Your Learning Progress")

        st.progress(0)

        st.caption(
            "Your progress will appear here "
            "once you begin practicing."
        )

    # Check once per Dashboard visit.
    check_recovery()
