
"""
Patente B - Automatic anonymous student identity.

PostgreSQL generates student IDs.
Browser Local Storage remembers the student ID.

No registration forms or buttons are required.
"""

import json
import logging
import uuid

import streamlit as st
from streamlit_local_storage import LocalStorage

from student_tracking import resolve_student


BROWSER_ID_KEY = "patenteb_browser_id"
STORAGE_KEY = "storage_init"


# =========================================
# VALIDATE STUDENT ID
# =========================================
def validate_browser_id(value):
    """Extract a valid UUID from stored browser data."""

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


# =========================================
# BROWSER STORAGE
# =========================================
def get_browser_storage():
    """Initialize browser storage once per session."""

    if "browser_local_storage" not in st.session_state:
        st.session_state.browser_local_storage = (
            LocalStorage(key=STORAGE_KEY)
        )

    return st.session_state.browser_local_storage


def get_browser_id():
    """Return the confirmed student identity."""

    if not st.session_state.get("identity_resolved"):
        return None

    return validate_browser_id(
        st.session_state.get("browser_id")
    )


def read_stored_browser_id(storage):
    """Read the browser's currently stored student ID."""

    stored_value = storage.getItem(BROWSER_ID_KEY)

    stored_id = validate_browser_id(stored_value)

    if not stored_id:
        initial_items = st.session_state.get(
            STORAGE_KEY
        )

        if isinstance(initial_items, dict):
            stored_id = validate_browser_id(
                initial_items.get(BROWSER_ID_KEY)
            )

    return stored_id


# =========================================
# AUTOMATIC STUDENT IDENTIFICATION
# =========================================
def initialize_browser_identity():
    """
    Automatically identify a student.

    Returning students recover their existing ID.
    New students receive a PostgreSQL-generated ID.

    Wait for browser storage to confirm new IDs
    before completing registration.
    """

    existing = get_browser_id()

    if existing:
        return existing

    try:
        storage = get_browser_storage()

        stored_items = getattr(
            storage,
            "storedItems",
            None
        )

        # Browser storage must finish initializing.
        if not isinstance(stored_items, dict):
            return None

        stored_id = read_stored_browser_id(storage)

        # =====================================
        # PENDING REGISTRATION
        # =====================================
        pending_id = validate_browser_id(
            st.session_state.get(
                "pending_student_id"
            )
        )

        if pending_id:

            # Browser has confirmed the new ID.
            if stored_id == pending_id:

                st.session_state.browser_id = pending_id
                st.session_state.identity_resolved = True

                st.session_state.pop(
                    "pending_student_id",
                    None
                )

                return pending_id

            # Do not create another student.
            # Retry saving the SAME pending ID.
            storage.setItem(
                BROWSER_ID_KEY,
                pending_id
            )

            return None

        # =====================================
        # RETURNING STUDENT
        # =====================================
        if stored_id:

            selected_id, created_new = resolve_student(
                [stored_id],
                allow_create=True
            )

            if not selected_id:
                logging.error(
                    "Unable to verify student identity"
                )
                return None

            if not created_new:

                st.session_state.browser_id = selected_id
                st.session_state.identity_resolved = True

                return selected_id

            # The stored ID was not found in
            # PostgreSQL. A replacement was created.
            # Confirm browser persistence first.
            st.session_state.pending_student_id = (
                selected_id
            )

            storage.setItem(
                BROWSER_ID_KEY,
                selected_id
            )

            return None

        # =====================================
        # GENUINELY NEW STUDENT
        # =====================================
        selected_id, created_new = resolve_student(
            [],
            allow_create=True
        )

        if not selected_id:
            logging.error(
                "Automatic student registration failed"
            )
            return None

        # Save the pending ID before attempting
        # browser storage, preventing duplicate
        # registration during session reruns.
        st.session_state.pending_student_id = (
            selected_id
        )

        storage.setItem(
            BROWSER_ID_KEY,
            selected_id
        )

        # Wait for the browser to return this ID
        # on a subsequent Streamlit execution.
        return None

    except Exception:
        logging.exception(
            "Unable to initialize student identity"
        )
        return None


# =========================================
# COMPATIBILITY FUNCTIONS
# =========================================
def create_browser_id():
    return initialize_browser_identity()


def ensure_session_browser_id():
    return get_browser_id()
