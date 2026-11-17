
"""
Patente B - Main Application

Includes:
- Automatic anonymous student identification
- Welcome page
- Dashboard
- Argomenti learning
- Quiz Translate Mode
- Instant Correction Mode
- Shared header and footer
- Quiz modal
- URL navigation
"""

import streamlit as st

from browser_identity import initialize_browser_identity

from dashboard import show_dashboard
from styles_loader import load_css
from components.header import show_header
from components.footer import show_footer
from components.quiz_modal import show_quiz_modal
from quiz import show_quiz
from instant_correction import show_instant_correction
from argomenti import show_argomenti


# =========================================
# STREAMLIT CONFIGURATION
# =========================================

st.set_page_config(
    page_title="Patente B",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None,
    },
)

load_css()


# =========================================
# PAGE CONFIGURATION
# =========================================

VALID_PAGES = {
    "welcome",
    "dashboard",
    "quiz",
    "instant_correction",
    "argomenti",
    "coming_soon",
}

QUIZ_PAGES = {
    "quiz",
    "instant_correction",
}


# =========================================
# SESSION DEFAULTS
# =========================================

defaults = {
    "open_quiz_modal": False,
    "quiz_translation": False,
    "quiz_auto_correction": False,
    "quiz_mode": None,
    "recovery_handled": False,
    "argomenti_category_id": None,
    "argomenti_subtopic_id": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================
# AUTOMATIC STUDENT IDENTIFICATION
# =========================================

def initialize_student():
    """
    Recover the browser identity and confirm
    its registration in PostgreSQL.

    The browser component handles UUID
    creation and persistence.

    No login or registration buttons.
    """

    browser_id = initialize_browser_identity()

    if not browser_id:
        return None

    st.session_state.browser_id = browser_id

    return browser_id


# Initialize identity once per full app run.
# The browser component triggers a rerun
# when its JavaScript result becomes ready.

student_browser_id = initialize_student()


# =========================================
# URL HELPERS
# =========================================

def valid_id(value):
    if value is None:
        return None

    try:
        number = int(value)

        if number > 0:
            return number

    except (TypeError, ValueError):
        pass

    return None



def read_url_location():

    page = st.query_params.get(
        "page",
        "welcome"
    )

    if page not in VALID_PAGES:
        page = "welcome"

    category_id = None
    subtopic_id = None
    question_id = None

    if page == "argomenti":

        category_id = valid_id(
            st.query_params.get("category")
        )

        if category_id is not None:

            subtopic_id = valid_id(
                st.query_params.get("subtopic")
            )

            if subtopic_id is not None:

                question_id = valid_id(
                    st.query_params.get("question")
                )

    return page, category_id, subtopic_id, question_id


def update_url(
    page,
    category_id=None,
    subtopic_id=None,
):

    params = {}

    if page != "dashboard":
        params["page"] = page

    if page == "argomenti":

        if category_id is not None:

            params["category"] = str(category_id)

            if subtopic_id is not None:
                params["subtopic"] = str(
                    subtopic_id
                )

    if dict(st.query_params) != params:

        st.query_params.clear()
        st.query_params.update(params)


# =========================================
# RESTORE LOCATION FROM URL
# =========================================


url_page, url_category, url_subtopic, url_question = (
    read_url_location()
)



current_url_signature = (
    url_page,
    url_category,
    url_subtopic,
    url_question,
)


previous_url_signature = (
    st.session_state.get(
        "_last_url_signature"
    )
)


if previous_url_signature != current_url_signature:

    st.session_state.page = url_page

    st.session_state.argomenti_category_id = (
        url_category
    )

    st.session_state.argomenti_subtopic_id = (
        url_subtopic
    )

    # Store the exact question ID from the URL
    st.session_state.argomenti_question_id = (
        url_question
    )

    st.session_state._last_url_signature = (
        current_url_signature
    )


# =========================================
# NAVIGATION
# =========================================


def navigate_to(page):

    if page not in VALID_PAGES:
        page = "welcome"

    st.session_state.page = page

    if page == "dashboard":
        st.session_state.recovery_handled = False

    if page == "quiz":

        st.session_state.quiz_mode = (
            "translate"
        )

    elif page == "instant_correction":

        st.session_state.quiz_mode = (
            "instant_correction"
        )

    # Clear previous Argomenti selections
    st.session_state.argomenti_category_id = None
    st.session_state.argomenti_subtopic_id = None
    st.session_state.argomenti_question_id = None

    update_url(page)

    st.session_state._last_url_signature = (
        read_url_location()
    )

    st.rerun()


# =========================================
# WELCOME PAGE
# =========================================

def show_welcome():

    st.title("Welcome to Patente B")

    st.write(
        "Prepare for your Italian driving "
        "theory exam."
    )

    if st.button(
        "OK — Go to Dashboard",
        key="welcome_main_ok",
    ):
        navigate_to("dashboard")


# =========================================
# AUTOMATIC STUDENT IDENTITY RECOVERY
# =========================================

@st.fragment(run_every="1s")
def wait_for_browser_recovery():
    """
    Display a waiting message while the
    browser identity is being resolved.

    The identity component is mounted in
    the main app, not duplicated here.

    Its response triggers a full app rerun.
    """

    st.info(
        "Preparing your student account..."
    )


# =========================================
# PAGE ROUTING
# =========================================

current_page = st.session_state.page

if current_page not in VALID_PAGES:

    current_page = "welcome"

    st.session_state.page = current_page


# =========================================
# SHARED HEADER
# =========================================

if current_page not in QUIZ_PAGES | {"argomenti"}:

    show_header()


# =========================================
# WELCOME
# =========================================

if current_page == "welcome":

    show_welcome()


# =========================================
# DASHBOARD
# =========================================

elif current_page == "dashboard":

    show_dashboard()


# =========================================
# ARGOMENTI
# =========================================

elif current_page == "argomenti":

    if student_browser_id:

        show_argomenti()

    else:

        wait_for_browser_recovery()


# =========================================
# QUIZ TRANSLATE MODE
# =========================================

elif current_page == "quiz":

    st.session_state.quiz_mode = "translate"

    if st.button(
        "‹‹ Quiz Translate Mode",
        key="quiz_back",
    ):
        navigate_to("dashboard")

    if student_browser_id:

        show_quiz()

    else:

        wait_for_browser_recovery()


# =========================================
# INSTANT CORRECTION
# =========================================

elif current_page == "instant_correction":

    st.session_state.quiz_mode = (
        "instant_correction"
    )

    if st.button(
        "‹‹ Instant Correction Mode",
        key="instant_quiz_back",
    ):
        navigate_to("dashboard")

    if student_browser_id:

        show_instant_correction()

    else:

        wait_for_browser_recovery()


# =========================================
# COMING SOON
# =========================================

elif current_page == "coming_soon":

    st.title("🚧 Coming Soon")

    st.info(
        "Auto Correction will be available "
        "in a future update."
    )

    if st.button(
        "Back to Dashboard",
        key="coming_soon_back",
    ):
        navigate_to("dashboard")


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
