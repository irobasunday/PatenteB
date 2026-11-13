
"""
Patente B — Argomenti browser storage.

Save and restore the selected chapter and
subtopic without changing the browser URL.
"""

import json

import streamlit as st
from streamlit_local_storage import LocalStorage


# =========================================
# STORAGE SETTINGS
# =========================================

STORAGE_KEY = "patenteb_argomenti_location"

ALLOWED_PAGES = {
    "welcome",
    "dashboard",
    "argomenti",
    "coming_soon",
}


# =========================================
# SHARED LOCAL STORAGE
# =========================================

def get_argomenti_storage():
    """
    Share the LocalStorage instance with
    browser_identity.py.
    """

    if "browser_local_storage" not in st.session_state:

        st.session_state.browser_local_storage = (
            LocalStorage()
        )

    return st.session_state.browser_local_storage


# =========================================
# VALIDATE DATABASE IDS
# =========================================

def validate_saved_id(value):
    """
    Accept positive integer IDs or None.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        return None

    try:
        number = int(value)

    except (TypeError, ValueError):
        return None

    if number <= 0:
        return None

    return number


# =========================================
# NORMALIZE LOCATION
# =========================================

def normalize_location(location):
    """
    Validate a location before saving
    or restoring it.
    """

    if not isinstance(location, dict):
        return None

    page = location.get("page")

    if page not in ALLOWED_PAGES:
        return None

    if page != "argomenti":
        return {"page": page}

    category_id = validate_saved_id(
        location.get("category_id")
    )

    subtopic_id = validate_saved_id(
        location.get("subtopic_id")
    )

    if category_id is None:
        subtopic_id = None

    return {
        "page": "argomenti",
        "category_id": category_id,
        "subtopic_id": subtopic_id,
    }


# =========================================
# SAVE LOCATION
# =========================================

def save_location(location):
    """
    Write a valid location to localStorage.
    """

    location = normalize_location(location)

    if location is None:
        return

    storage = get_argomenti_storage()

    storage.setItem(
        STORAGE_KEY,
        json.dumps(location),
    )


# =========================================
# SAVE ARGOMENTI
# =========================================

def save_argomenti_location(
    category_id=None,
    subtopic_id=None,
):
    """
    Save chapter and subtopic selection.
    """

    save_location({
        "page": "argomenti",
        "category_id": category_id,
        "subtopic_id": subtopic_id,
    })


# =========================================
# SAVE OTHER PAGE
# =========================================

def save_other_page(page):
    """
    Save the selected non-quiz page.
    """

    if page not in ALLOWED_PAGES:
        return

    save_location({
        "page": page,
    })


# =========================================
# READ SAVED LOCATION
# =========================================

def read_saved_location():
    """
    Read the browser's saved location.

    Returns None while the storage value
    is unavailable or invalid.
    """

    storage = get_argomenti_storage()

    value = storage.getItem(STORAGE_KEY)

    if value is None:
        return None

    if isinstance(value, dict):

        location = value

    elif isinstance(value, str):

        try:
            location = json.loads(value)

        except (ValueError, TypeError):
            return None

    else:

        return None

    return normalize_location(location)


# =========================================
# RESTORE LOCATION
# =========================================

def restore_argomenti_location(location):
    """
    Restore a saved page into Streamlit
    session state.
    """

    location = normalize_location(location)

    if location is None:
        return False

    page = location["page"]

    st.session_state.page = page

    if page == "argomenti":

        st.session_state.argomenti_category_id = (
            location["category_id"]
        )

        st.session_state.argomenti_subtopic_id = (
            location["subtopic_id"]
        )

    else:

        st.session_state.argomenti_category_id = None
        st.session_state.argomenti_subtopic_id = None

    return True
