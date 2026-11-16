
"""
Patente B - Recover existing anonymous student identity.

PostgreSQL owns student IDs.
Chrome stores the student ID reference.

RECOVERY TEST:
New student creation is temporarily disabled.
"""

import json
import logging
import uuid

import streamlit as st
from streamlit_local_storage import LocalStorage

from student_tracking import resolve_student


BROWSER_ID_KEY = "patenteb_browser_id"

# Use the same component key as the original app.
STORAGE_KEY = "storage_init"


def validate_browser_id(value):
    """Read UUIDs from strings or JSON objects."""

    if isinstance(value, dict):
        value = value.get(BROWSER_ID_KEY)

    if isinstance(value, str):
        try:
            decoded = json.loads(value)

            if isinstance(decoded, dict):
                value = decoded.get(BROWSER_ID_KEY)
            elif isinstance(decoded, str):
                value = decoded

        except (ValueError, TypeError):
            pass

    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        return None


def get_browser_storage():
    """
    Construct the browser-storage component once.
    """

    if "browser_local_storage" not in st.session_state:
        st.session_state.browser_local_storage = LocalStorage(
            key=STORAGE_KEY
        )

    return st.session_state.browser_local_storage


def get_browser_id():
    """Return the resolved session student ID."""

    if not st.session_state.get("identity_resolved"):
        return None

    return validate_browser_id(
        st.session_state.get("browser_id")
    )


def initialize_browser_identity():
    """
    Recover the saved Chrome identity from PostgreSQL.

    Do not create any new database records during
    this recovery test.
    """

    existing = get_browser_id()

    if existing:
        return existing

    try:
        storage = get_browser_storage()

        # The storage component's Python cache.
        stored_items = getattr(
            storage,
            "storedItems",
            None
        )

        if not isinstance(stored_items, dict):
            return None

        # Read the specific browser storage key.
        stored_value = storage.getItem(
            BROWSER_ID_KEY
        )

        stored_id = validate_browser_id(
            stored_value
        )

        # Some versions expose the initial data
        # through Streamlit session state.
        if not stored_id:
            initial_items = st.session_state.get(
                STORAGE_KEY
            )

            if isinstance(initial_items, dict):
                stored_id = validate_browser_id(
                    initial_items.get(BROWSER_ID_KEY)
                )

        # Do not create a new ID if the browser
        # has not returned a recognizable ID.
        if not stored_id:
            logging.warning(
                "Chrome student ID not recovered"
            )
            return None

        # Check that this ID exists in PostgreSQL.
        selected_id, created_new = resolve_student(
            [stored_id],
            allow_create=False
        )

        if not selected_id:
            logging.warning(
                "Chrome ID not found in PostgreSQL: %s",
                stored_id
            )
            return None

        # Keep the recovered identity in this session.
        st.session_state.browser_id = selected_id
        st.session_state.identity_resolved = True

        return selected_id

    except Exception:
        logging.exception(
            "Unable to recover Chrome student identity"
        )
        return None


def create_browser_id():
    return initialize_browser_identity()


def ensure_session_browser_id():
    return get_browser_id()
