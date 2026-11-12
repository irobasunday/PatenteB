
import time
import uuid

import streamlit as st
from streamlit_local_storage import LocalStorage


BROWSER_ID_KEY = "patenteb_browser_id"


def validate_browser_id(value):
    if not isinstance(value, str):
        return None

    try:
        return str(uuid.UUID(value))
    except (ValueError, TypeError, AttributeError):
        return None


def get_browser_id():
    """
    Recover browser identity after refresh.

    Prefer the ID stored in the browser.
    Never use an unconfirmed pending ID
    for PostgreSQL quiz recovery.
    """

    if "browser_local_storage" not in st.session_state:
        st.session_state.browser_local_storage = LocalStorage()

    storage = st.session_state.browser_local_storage

    # First check the confirmed ID in this session.
    existing_id = validate_browser_id(
        st.session_state.get("browser_id")
    )

    if existing_id:
        return existing_id

    # Read the previously saved browser ID.
    saved_id = validate_browser_id(
        storage.getItem(BROWSER_ID_KEY)
    )

    if saved_id:
        st.session_state.browser_id = saved_id
        st.session_state.pop("pending_browser_id", None)
        st.session_state.pop("browser_id_write_started", None)
        return saved_id

    # Browser storage may still be loading.
    if "browser_identity_check_started" not in st.session_state:
        st.session_state.browser_identity_check_started = (
            time.monotonic()
        )

    elapsed = (
        time.monotonic()
        - st.session_state.browser_identity_check_started
    )

    # Allow time for an existing ID to arrive.
    if elapsed < 3:
        return None

    # First-time visitor: prepare a new ID.
    pending_id = validate_browser_id(
        st.session_state.get("pending_browser_id")
    )

    if not pending_id:
        pending_id = str(uuid.uuid4())
        st.session_state.pending_browser_id = pending_id

    if not st.session_state.get(
        "browser_id_write_started", False
    ):
        st.session_state.browser_id_write_started = True

        storage.setItem(
            BROWSER_ID_KEY,
            pending_id,
        )

    # Wait until browser storage confirms it.
    return None


def create_browser_id():
    return get_browser_id()
