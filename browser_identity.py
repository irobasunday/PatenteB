
import time
import uuid

import streamlit as st
from streamlit_local_storage import LocalStorage


# =========================================
# BROWSER IDENTITY SETTINGS
# =========================================

BROWSER_ID_KEY = "patenteb_browser_id"

BROWSER_RECOVERY_WAIT_SECONDS = 3


# =========================================
# VALIDATE BROWSER ID
# =========================================

def validate_browser_id(value):
    """
    Accept only valid UUID strings.
    """

    if not isinstance(value, str):
        return None

    try:
        return str(uuid.UUID(value))

    except (ValueError, TypeError, AttributeError):
        return None


# =========================================
# SHARED BROWSER STORAGE
# =========================================

def get_browser_storage():
    """
    Reuse the LocalStorage instance shared
    with argomenti_storage.py.
    """

    if "browser_local_storage" not in st.session_state:

        st.session_state.browser_local_storage = (
            LocalStorage()
        )

    return st.session_state.browser_local_storage


# =========================================
# RECOVER BROWSER IDENTITY
# =========================================

def get_browser_id():
    """
    Recover the browser identity used for
    PostgreSQL quiz progress.

    An unconfirmed new ID must never be
    returned for quiz recovery.
    """

    storage = get_browser_storage()

    # -------------------------------------
    # 1. Check confirmed session identity
    # -------------------------------------

    existing_id = validate_browser_id(
        st.session_state.get("browser_id")
    )

    if existing_id:
        return existing_id

    # -------------------------------------
    # 2. Read saved browser identity
    # -------------------------------------

    saved_id = validate_browser_id(
        storage.getItem(BROWSER_ID_KEY)
    )

    if saved_id:

        st.session_state.browser_id = saved_id

        st.session_state.pop(
            "pending_browser_id",
            None,
        )

        st.session_state.pop(
            "browser_id_write_started",
            None,
        )

        st.session_state.pop(
            "browser_identity_check_started",
            None,
        )

        return saved_id

    # -------------------------------------
    # 3. Wait for browser storage
    # -------------------------------------

    if "browser_identity_check_started" not in st.session_state:

        st.session_state.browser_identity_check_started = (
            time.monotonic()
        )

    elapsed = (
        time.monotonic()
        - st.session_state.browser_identity_check_started
    )

    if elapsed < BROWSER_RECOVERY_WAIT_SECONDS:
        return None

    # -------------------------------------
    # 4. Prepare first-time browser identity
    # -------------------------------------

    pending_id = validate_browser_id(
        st.session_state.get("pending_browser_id")
    )

    if not pending_id:

        pending_id = str(uuid.uuid4())

        st.session_state.pending_browser_id = (
            pending_id
        )

    # -------------------------------------
    # 5. Save pending identity once
    # -------------------------------------

    if not st.session_state.get(
        "browser_id_write_started",
        False,
    ):

        st.session_state.browser_id_write_started = True

        storage.setItem(
            BROWSER_ID_KEY,
            pending_id,
        )

    # -------------------------------------
    # 6. Wait for storage confirmation
    # -------------------------------------

    return None


# =========================================
# COMPATIBILITY FUNCTION
# =========================================

def create_browser_id():
    """
    Preserve compatibility with existing
    modules that call create_browser_id().
    """

    return get_browser_id()
