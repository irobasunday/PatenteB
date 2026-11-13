
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
    page = st.query_params.get("page", "welcome")

    if page not in VALID_PAGES:
        page = "welcome"

    category_id = None
    subtopic_id = None

    if page == "argomenti":
        category_id = valid_id(
            st.query_params.get("category")
        )

        if category_id is not None:
            subtopic_id = valid_id(
                st.query_params.get("subtopic")
            )

    return page, category_id, subtopic_id


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
                params["subtopic"] = str(subtopic_id)

    if dict(st.query_params) != params:
        st.query_params.clear()
        st.query_params.update(params)


# =========================================
# RESTORE LOCATION FROM URL
# =========================================

url_page, url_category, url_subtopic = (
    read_url_location()
)

current_url_signature = (
    url_page,
    url_category,
    url_subtopic,
)

previous_url_signature = st.session_state.get(
    "_last_url_signature"
)

if previous_url_signature != current_url_signature:
    st.session_state.page = url_page

    st.session_state.argomenti_category_id = (
        url_category
    )

    st.session_state.argomenti_subtopic_id = (
        url_subtopic
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
        st.session_state.quiz_mode = "translate"

    elif page == "instant_correction":
        st.session_state.quiz_mode = (
            "instant_correction"
        )

    st.session_state.argomenti_category_id = None
    st.session_state.argomenti_subtopic_id = None

    update_url(page)

    st.session_state._last_url_signature = (
        read_url_location()
    )

    st.rerun()


# =========================================
# QUIZ BROWSER ID RECOVERY
# =========================================

@st.fragment(run_every="1s")
def wait_for_browser_recovery():
    browser_id = get_browser_id()

    if browser_id:
        st.session_state.browser_id = browser_id
        st.rerun(scope="app")
        return

    st.info("Restoring your saved quiz...")


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
# PAGE ROUTING
# =========================================

current_page = st.session_state.page

if current_page not in VALID_PAGES:
    current_page = "welcome"
    st.session_state.page = current_page


# Shared header
if current_page not in (
    "quiz",
    "instant_correction",
    "argomenti",
):
    show_header()


if current_page == "welcome":
    show_welcome()


elif current_page == "dashboard":
    show_dashboard()


elif current_page == "argomenti":
    show_argomenti()


elif current_page == "quiz":
    st.session_state.quiz_mode = "translate"

    if st.button(
        "‹‹ Quiz Translate Mode",
        key="quiz_back",
    ):
        navigate_to("dashboard")

    browser_id = get_browser_id()

    if browser_id:
        st.session_state.browser_id = browser_id
        show_quiz()
    else:
        wait_for_browser_recovery()


elif current_page == "instant_correction":
    st.session_state.quiz_mode = (
        "instant_correction"
    )

    if st.button(
        "‹‹ Instant Correction Mode",
        key="instant_quiz_back",
    ):
        navigate_to("dashboard")

    browser_id = get_browser_id()

    if browser_id:
        st.session_state.browser_id = browser_id
        show_instant_correction()
    else:
        wait_for_browser_recovery()


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
