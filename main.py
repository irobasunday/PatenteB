
import streamlit as st

from browser_identity import initialize_browser_identity
from student_tracking import register_student

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

QUIZ_PAGES = {"quiz", "instant_correction"}


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
    Resolve one student ID and confirm
    that it exists in PostgreSQL.
    """

    browser_id = initialize_browser_identity()

    if not browser_id:
        return None

    if st.session_state.get(
        "registered_student_id"
    ) != browser_id:

        if not register_student(browser_id):
            return None

        st.session_state.registered_student_id = (
            browser_id
        )

    st.session_state.browser_id = browser_id

    return browser_id


# Initialize the student once during app execution
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
# STUDENT IDENTITY RECOVERY
# =========================================

# =========================================
# STUDENT IDENTITY RECOVERY
# =========================================
@st.fragment(run_every="1s")
def wait_for_browser_recovery():
    """
    Diagnose student identity recovery
    on Streamlit Community Cloud.
    """

    browser_id = initialize_student()

    # Student successfully identified.
    if browser_id:
        st.rerun(scope="app")
        return

    st.warning(
        "Student identity not yet resolved."
    )

    # Check whether browser storage exists.
    storage = st.session_state.get(
        "browser_local_storage"
    )

    if storage is None:
        st.error(
            "DIAGNOSTIC: Browser storage "
            "has not been initialized."
        )

    else:
        stored_items = getattr(
            storage,
            "storedItems",
            None
        )

        st.write(
            "DIAGNOSTIC - Storage type:",
            type(stored_items).__name__
        )

        st.write(
            "DIAGNOSTIC - Storage ready:",
            isinstance(stored_items, dict)
        )

    # Check identity session state.
    st.write(
        "DIAGNOSTIC - Identity resolved:",
        st.session_state.get(
            "identity_resolved",
            False
        )
    )

    st.write(
        "DIAGNOSTIC - Pending student:",
        bool(
            st.session_state.get(
                "pending_student_id"
            )
        )
    )

    st.write(
        "DIAGNOSTIC - Student registered:",
        bool(
            st.session_state.get(
                "registered_student_id"
            )
        )
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
