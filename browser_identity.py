
"""
Patente B - Anonymous student identity.

PostgreSQL creates and owns student IDs.
Chrome Local Storage remembers the ID.
"""

import json
import logging
import uuid

import streamlit as st
from streamlit_local_storage import LocalStorage

from student_tracking import resolve_student


BROWSER_ID_KEY = "patenteb_browser_id"
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
    """Construct browser storage once per session."""

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
    Recover an existing student or register a new one.

    PostgreSQL generates student IDs.
    Chrome Local Storage remembers the student ID.

    Never create a new student while browser
    storage is still loading.
    """

    # 1. Return an identity already resolved
    # during this Streamlit session.
    existing = get_browser_id()

    if existing:
        return existing

    try:
        # 2. Initialize Chrome Local Storage.
        storage = get_browser_storage()

        stored_items = getattr(
            storage,
            "storedItems",
            None
        )

        # Wait until browser storage is loaded.
        if not isinstance(stored_items, dict):
            return None

        # 3. Read the existing student ID.
        stored_value = storage.getItem(
            BROWSER_ID_KEY
        )

        stored_id = validate_browser_id(
            stored_value
        )

        # Check the alternative storage location.
        if not stored_id:
            initial_items = st.session_state.get(
                STORAGE_KEY
            )

            if isinstance(initial_items, dict):
                stored_id = validate_browser_id(
                    initial_items.get(BROWSER_ID_KEY)
                )

        # 4. Recover an existing student.
        if stored_id:

            selected_id, created_new = resolve_student(
                [stored_id],
                allow_create=False
            )

            if not selected_id:
                logging.warning(
                    "Existing student ID could not "
                    "be verified in PostgreSQL: %s",
                    stored_id
                )
                return None

        # 5. Register a new student only if
        # Chrome has no existing student ID.
        else:

            # Reuse a student ID created earlier
            # in this Streamlit session.
            selected_id = validate_browser_id(
                st.session_state.get(
                    "pending_student_id"
                )
            )

            if not selected_id:

                # PostgreSQL creates the UUID.
                selected_id, created_new = (
                    resolve_student(
                        [],
                        allow_create=True
                    )
                )

                if not selected_id:
                    logging.error(
                        "Unable to register new student"
                    )
                    return None

                # Save immediately in session state
                # to avoid duplicate registration
                # during retries.
                st.session_state.pending_student_id = (
                    selected_id
                )

        # 6. Save the verified or newly created
        # student ID in Chrome Local Storage.
        storage.setItem(
            BROWSER_ID_KEY,
            selected_id
        )

        # 7. Mark the student as identified.
        st.session_state.browser_id = selected_id
        st.session_state.identity_resolved = True

        # Registration/recovery is complete.
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



def create_browser_id():
    return initialize_browser_identity()


def ensure_session_browser_id():
    return get_browser_id()
