
import streamlit as st

from dashboard import show_dashboard
from styles_loader import load_css
from components.header import show_header
from components.footer import show_footer
from components.quiz_modal import show_quiz_modal

from quiz import show_quiz
from instant_correction import show_instant_correction
from argomenti import show_argomenti
from browser_identity import get_browser_id


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
# BROWSER RECOVERY
# =========================================

@st.fragment(run_every="1s")
def wait_for_browser_recovery():
    """
    Automatically wait for the browser ID
    before loading either quiz mode.
    """

    browser_id = get_browser_id()

    if browser_id:
        st.session_state.browser_id = browser_id
        st.rerun(scope="app")

    st.info("Restoring your saved quiz...")


# =========================================
# VALID APP PAGES
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
# BROWSER URL MANAGEMENT
# =========================================

def get_page_from_url():
    """
    Recover the active page from the URL.
    """

    saved_page = st.query_params.get(
        "page",
        "welcome",
    )

    if saved_page in VALID_PAGES:
        return saved_page

    return "welcome"


def sync_page_to_url(page):
    """
    Preserve quiz page URLs for refresh.
    """

    if page in QUIZ_PAGES:

        if st.query_params.get("page") != page:
            st.query_params["page"] = page

    else:

        if "page" in st.query_params:
            del st.query_params["page"]


# =========================================
# INITIAL PAGE RECOVERY
# =========================================

if "page" not in st.session_state:
    st.session_state.page = get_page_from_url()


# =========================================
# SESSION DEFAULTS
# =========================================

if "open_quiz_modal" not in st.session_state:
    st.session_state.open_quiz_modal = False

if "quiz_translation" not in st.session_state:
    st.session_state.quiz_translation = False

if "quiz_auto_correction" not in st.session_state:
    st.session_state.quiz_auto_correction = False

if "quiz_mode" not in st.session_state:
    st.session_state.quiz_mode = None

if "recovery_handled" not in st.session_state:
    st.session_state.recovery_handled = False


# =========================================
# PAGE NAVIGATION
# =========================================

def navigate_to(page):
    """
    Navigate while preserving quiz URLs.
    """

    if page not in VALID_PAGES:
        page = "welcome"

    if page == "dashboard":
        st.session_state.recovery_handled = False

    if page == "quiz":
        st.session_state.quiz_mode = "translate"

    elif page == "instant_correction":
        st.session_state.quiz_mode = "instant_correction"

    st.session_state.page = page

    sync_page_to_url(page)

    st.rerun()


# =========================================
# SYNCHRONIZE PAGE CHANGES
# =========================================

current_page = st.session_state.page

if current_page not in VALID_PAGES:
    current_page = "welcome"
    st.session_state.page = current_page

sync_page_to_url(current_page)


# =========================================
# WELCOME PAGE
# =========================================

def show_welcome():

    st.title("Welcome to Patente B")

    st.write(
        "Prepare for your Italian driving theory exam."
    )

    if st.button(
        "OK — Go to Dashboard",
        key="welcome_main_ok",
    ):
        navigate_to("dashboard")


# =========================================
# SHARED HEADER
# =========================================

if st.session_state.page not in (
    "quiz",
    "instant_correction",
    "argomenti",
):
    show_header()


# =========================================
# PAGE ROUTING
# =========================================

if st.session_state.page == "welcome":

    show_welcome()


elif st.session_state.page == "dashboard":

    show_dashboard()


elif st.session_state.page == "argomenti":

    show_argomenti()


# =========================================
# TRANSLATE MODE
# =========================================

elif st.session_state.page == "quiz":

    st.session_state.quiz_mode = "translate"

    if st.button(
        "‹‹ Quiz Translate Mode",
        key="quiz_back",
    ):
        navigate_to("dashboard")

    browser_id = get_browser_id()

    if not browser_id:

        wait_for_browser_recovery()

    else:

        st.session_state.browser_id = browser_id

        show_quiz()


# =========================================
# INSTANT CORRECTION MODE
# =========================================

elif st.session_state.page == "instant_correction":

    st.session_state.quiz_mode = "instant_correction"

    if st.button(
        "‹‹ Instant Correction Mode",
        key="instant_quiz_back",
    ):
        navigate_to("dashboard")

    browser_id = get_browser_id()

    if not browser_id:

        wait_for_browser_recovery()

    else:

        st.session_state.browser_id = browser_id

        show_instant_correction()


# =========================================
# COMING SOON
# =========================================

elif st.session_state.page == "coming_soon":

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
