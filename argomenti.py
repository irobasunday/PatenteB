
import os
import streamlit as st
import psycopg
from psycopg.rows import dict_row


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_connection():
    """Connect to the existing PostgreSQL database."""

    database_url = None

    try:
        database_url = st.secrets.get("DATABASE_URL")
    except Exception:
        pass

    if not database_url:
        database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing from Streamlit secrets "
            "or environment variables."
        )

    return psycopg.connect(database_url)


# ==========================================
# DATABASE QUERIES
# ==========================================

@st.cache_data(ttl=300)
def get_categories():
    """Retrieve all categories from PostgreSQL."""

    connection = get_connection()

    try:
        with connection.cursor(
            row_factory=dict_row
        ) as cursor:

            cursor.execute(
                """
                SELECT id, name, slug
                FROM categories
                ORDER BY id
                """
            )

            return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


@st.cache_data(ttl=300)
def get_subtopics(category_id):
    """Retrieve subtopics belonging to one category."""

    connection = get_connection()

    try:
        with connection.cursor(
            row_factory=dict_row
        ) as cursor:

            cursor.execute(
                """
                SELECT id, category_id, name, slug
                FROM subtopics
                WHERE category_id = %s
                ORDER BY id
                """,
                (category_id,),
            )

            return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# ==========================================
# FUTURE LEARNING PROGRESS
# ==========================================

def get_category_progress(category_id):
    """
    Placeholder for future student progress tracking.

    Later, this function will retrieve the actual
    student's completed lessons from PostgreSQL.
    """

    return 0


def get_subtopic_completed(subtopic_id):
    """
    Placeholder for future lesson completion tracking.
    """

    return False


# ==========================================
# DEFINITION PREVIEW
# ==========================================

def short_description(definition):
    """
    Display the first 30 characters of a definition.
    Add ... only when the definition is longer.
    """

    if not definition:
        return ""

    definition = str(definition).strip()

    if len(definition) > 30:
        return definition[:30].rstrip() + "..."

    return definition


def get_definition_preview(subtopic):
    """
    Definition storage is not yet connected.

    Return a blank preview rather than inventing
    a definition or displaying unrelated text.
    """

    return short_description(
        subtopic.get("definition", "")
    )


# ==========================================
# NAVIGATION
# ==========================================

def open_category(category_id):
    st.session_state.argomenti_category_id = category_id
    st.session_state.argomenti_subtopic_id = None
    st.rerun()


def open_subtopic(subtopic_id):
    st.session_state.argomenti_subtopic_id = subtopic_id
    st.rerun()


def back_to_categories():
    st.session_state.argomenti_category_id = None
    st.session_state.argomenti_subtopic_id = None
    st.rerun()


def back_to_subtopics():
    st.session_state.argomenti_subtopic_id = None
    st.rerun()


def back_to_dashboard():
    st.session_state.argomenti_category_id = None
    st.session_state.argomenti_subtopic_id = None
    st.session_state.page = "dashboard"
    st.rerun()


# ==========================================
# SHARED PAGE TITLE
# ==========================================

def show_page_heading(title, back_action):
    back_col, title_col = st.columns(
        [1, 12],
        vertical_alignment="center",
        gap="small",
    )

    with back_col:
        if st.button(
            "‹",
            key=f"argomenti_back_{title}",
            help="Go back",
        ):
            back_action()

    with title_col:
        st.markdown(f"### {title}")


# ==========================================
# CATEGORY SCREEN
# ==========================================

def show_categories():
    show_page_heading(
        "Argomenti Manuale",
        back_to_dashboard,
    )

    search = st.text_input(
        "Cerca l'argomento",
        placeholder="Cerca l'argomento",
        key="argomenti_category_search",
        label_visibility="collapsed",
    )

    try:
        categories = get_categories()

    except Exception as error:
        st.error("Unable to load categories from PostgreSQL.")
        st.exception(error)
        return

    if search:
        categories = [
            category
            for category in categories
            if search.lower() in category["name"].lower()
        ]

    if not categories:
        st.info("Nessun argomento trovato.")
        return

    for category in categories:
        category_id = category["id"]
        progress = get_category_progress(category_id)

        with st.container(
            border=True,
            key=f"argomenti_category_{category_id}",
        ):
            icon_col, content_col, arrow_col = st.columns(
                [1, 8, 1],
                vertical_alignment="center",
                gap="small",
            )

            with icon_col:
                st.markdown("📘")

            with content_col:
                st.markdown(
                    f"**{category_id} - {category['name']}**"
                )

                progress_col, percentage_col = st.columns(
                    [8, 1],
                    vertical_alignment="center",
                    gap="small",
                )

                with progress_col:
                    st.progress(progress / 100)

                with percentage_col:
                    st.caption(f"{progress}%")

            with arrow_col:
                if st.button(
                    "›",
                    key=f"open_category_{category_id}",
                    help=f"Open {category['name']}",
                ):
                    open_category(category_id)


# ==========================================
# SUBTOPIC SCREEN
# ==========================================

def show_subtopics(category_id):
    try:
        categories = get_categories()

        category = next(
            (
                item
                for item in categories
                if item["id"] == category_id
            ),
            None,
        )

        subtopics = get_subtopics(category_id)

    except Exception as error:
        st.error("Unable to load subtopics from PostgreSQL.")
        st.exception(error)
        return

    if category is None:
        st.warning("Category not found.")

        if st.button("Back to Argomenti"):
            back_to_categories()

        return

    show_page_heading(
        category["name"],
        back_to_categories,
    )

    search = st.text_input(
        "Cerca il sottoargomento",
        placeholder="Cerca l'argomento",
        key=f"argomenti_subtopic_search_{category_id}",
        label_visibility="collapsed",
    )

    if search:
        subtopics = [
            subtopic
            for subtopic in subtopics
            if search.lower() in subtopic["name"].lower()
        ]

    if not subtopics:
        st.info("Nessun sottoargomento trovato.")
        return

    for subtopic in subtopics:
        subtopic_id = subtopic["id"]
        completed = get_subtopic_completed(subtopic_id)
        preview = get_definition_preview(subtopic)

        with st.container(
            border=True,
            key=f"argomenti_subtopic_{subtopic_id}",
        ):
            status_col, content_col, arrow_col = st.columns(
                [1, 8, 1],
                vertical_alignment="center",
                gap="small",
            )

            with status_col:
                st.markdown("✅" if completed else "⚪")

            with content_col:
                st.markdown(f"**{subtopic['name']}**")

                if preview:
                    st.caption(preview)

            with arrow_col:
                if st.button(
                    "›",
                    key=f"open_subtopic_{subtopic_id}",
                    help=f"Open {subtopic['name']}",
                ):
                    open_subtopic(subtopic_id)


# ==========================================
# LEARNING PAGE PLACEHOLDER
# ==========================================

def show_learning_page(category_id, subtopic_id):
    try:
        subtopics = get_subtopics(category_id)

    except Exception as error:
        st.error("Unable to load learning topic.")
        st.exception(error)
        return

    subtopic = next(
        (
            item
            for item in subtopics
            if item["id"] == subtopic_id
        ),
        None,
    )

    if subtopic is None:
        st.warning("Subtopic not found.")
        return

    show_page_heading(
        subtopic["name"],
        back_to_subtopics,
    )

    st.info(
        "The Italian definition, English explanation, "
        "images, audio, and topic quiz will be "
        "connected here in the next development stage."
    )


# ==========================================
# MAIN ARGOMENTI ENTRY POINT
# ==========================================

def show_argomenti():
    if "argomenti_category_id" not in st.session_state:
        st.session_state.argomenti_category_id = None

    if "argomenti_subtopic_id" not in st.session_state:
        st.session_state.argomenti_subtopic_id = None

    category_id = st.session_state.argomenti_category_id
    subtopic_id = st.session_state.argomenti_subtopic_id

    if category_id is None:
        show_categories()

    elif subtopic_id is None:
        show_subtopics(category_id)

    else:
        show_learning_page(category_id, subtopic_id)
