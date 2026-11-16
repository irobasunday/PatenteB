
"""
Patente B - Anonymous student identity.

PostgreSQL creates and owns student IDs.
Browser Local Storage remembers the ID.

Existing students recover their saved progress.
New students are registered automatically.
Unknown saved IDs require confirmation before
starting a new student account.
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
# UUID VALIDATION
# =========================================
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


# =========================================
# BROWSER STORAGE
# =========================================
def get_browser_storage():
    """Create the browser storage component once."""

    if "browser_local_storage" not in st.session_state:
        st.session_state.browser_local_storage = (
            LocalStorage(key=STORAGE_KEY)
        )

    return st.session_state.browser_local_storage


# =========================================
# CURRENT STUDENT ID
# =========================================
def get_browser_id():
    """Return the resolved student ID."""

    if not st.session_state.get("identity_resolved"):
        return None

    return validate_browser_id(
        st.session_state.get("browser_id")
    )


# =========================================
# STUDENT IDENTITY INITIALIZATION
# =========================================
def initialize_browser_identity():
    """
    Recover an existing student or register a new one.

    Never create a student before browser storage
    has finished loading.

    PostgreSQL generates all new UUIDs.
    """

    # Return an already resolved identity.
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

        # Wait until browser storage is ready.
        if not isinstance(stored_items, dict):
            logging.info(
                "Waiting for browser storage: %s",
                type(stored_items).__name__
            )
            return None

        # Read the browser's saved student ID.
        stored_value = storage.getItem(
            BROWSER_ID_KEY
        )

        stored_id = validate_browser_id(
            stored_value
        )

        # Fallback for initial storage data.
        if not stored_id:
            initial_items = st.session_state.get(
                STORAGE_KEY
            )

            if isinstance(initial_items, dict):
                stored_id = validate_browser_id(
                    initial_items.get(BROWSER_ID_KEY)
                )

        # =====================================
        # EXISTING STUDENT
        # =====================================
        if stored_id:

            selected_id, created_new = resolve_student(
                [stored_id],
                allow_create=False
            )

            if not selected_id:
                logging.warning(
                    "Student ID not verified: %s",
                    stored_id
                )

                # Do not overwrite a saved identity.
                # The user must explicitly choose
                # whether to start a new account.
                st.session_state.identity_recovery_needed = (
                    True
                )

                return None

            st.session_state.identity_recovery_needed = (
                False
            )

        # =====================================
        # NEW STUDENT
        # =====================================
        else:

            # Reuse a student already created
            # during this Streamlit session.
            selected_id = validate_browser_id(
                st.session_state.get(
                    "pending_student_id"
                )
            )

            if not selected_id:

                selected_id, created_new = (
                    resolve_student(
                        [],
                        allow_create=True
                    )
                )

                if not selected_id:
                    logging.error(
                        "New student registration failed"
                    )
                    return None

                # Prevent duplicate creation
                # during retries in this session.
                st.session_state.pending_student_id = (
                    selected_id
                )

        # =====================================
        # SAVE STUDENT ID
        # =====================================
        storage.setItem(
            BROWSER_ID_KEY,
            selected_id
        )

        # Keep the identity in session state.
        st.session_state.browser_id = selected_id
        st.session_state.identity_resolved = True

        st.session_state.identity_recovery_needed = (
            False
        )

        st.session_state.pop(
            "pending_student_id",
            None
        )

        return selected_id

    except Exception:
        logging.exception(
            "Unable to initialize student identity"
        )
        return None


# =========================================
# START NEW STUDENT AFTER CONFIRMATION
# =========================================
def start_new_student():
    """
    Create a new PostgreSQL student only after
    the user explicitly requests a fresh account.

    Never delete an existing student record.
    """

    try:
        storage = get_browser_storage()

        stored_items = getattr(
            storage,
            "storedItems",
            None
        )

        if not isinstance(stored_items, dict):
            return None

        selected_id = validate_browser_id(
            st.session_state.get(
                "pending_student_id"
            )
        )

        if not selected_id:

            selected_id, created_new = (
                resolve_student(
                    [],
                    allow_create=True
                )
            )

            if not selected_id:
                return None

            st.session_state.pending_student_id = (
                selected_id
            )

        storage.setItem(
            BROWSER_ID_KEY,
            selected_id
        )

        st.session_state.browser_id = selected_id
        st.session_state.identity_resolved = True

        st.session_state.identity_recovery_needed = (
            False
        )

        st.session_state.pop(
            "pending_student_id",
            None
        )

        return selected_id

    except Exception:
        logging.exception(
            "Unable to register a fresh student"
        )
        return None


# =========================================
# COMPATIBILITY FUNCTIONS
# =========================================
def create_browser_id():
    return initialize_browser_identity()


def ensure_session_browser_id():
    return get_browser_id()
