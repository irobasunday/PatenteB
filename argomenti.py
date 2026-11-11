
import os
import html
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
        with connection.cursor(row_factory=dict_row) as cursor:
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
        with connection.cursor(row_factory=dict_row) as cursor:
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
    Future PostgreSQL student progress integration.

    Return 0 until actual progress tracking exists.
    """
    return 0


def get_subtopic_completed(subtopic_id):
    """
    Future PostgreSQL lesson completion integration.
    """
    return False


# ==========================================
# DEFINITION PREVIEW
# ==========================================

def short_description(definition):
    """Return the first 30 characters plus ... if needed."""

    if not definition:
        return ""

    definition = str(definition).strip()

    if len(definition) > 30:
        return definition[:30].rstrip() + "..."

    return definition


def get_definition_preview(subtopic):
    """
    Definitions are not stored in the current
    confirmed subtopics schema.

    This will display previews once definitions
    are connected.
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
# PAGE STYLING
# ==========================================

def load_argomenti_css():
    """Load CSS only for the Argomenti interface."""

    css_path = os.path.join(
        os.path.dirname(__file__),
        "styles",
        "argomenti.css",
    )

    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as file:
            st.html(f"<style>{file.read()}</style>")


def safe_text(value):
    """Escape database text before inserting into HTML."""
    return html.escape(str(value or ""))


# ==========================================
# PAGE HEADER
# ==========================================

def show_page_heading(title, back_action):
    with st.container(key="argomenti_page_heading"):
        back_col, title_col = st.columns(
            [1, 11],
            vertical_alignment="center",
            gap="small",
        )

        with back_col:
            if st.button(
                "‹",
                key="argomenti_page_back",
                help="Go back",
            ):
                back_action()

        with title_col:
            st.markdown(
                f'<div class="argomenti-heading-title">'
                f'{safe_text(title)}</div>',
                unsafe_allow_html=True,
            )


# ==========================================
# CATEGORY ICONS
# ==========================================

def get_category_icon(category_id):
    """Simple icons until real category images are linked."""

    icons = {
        1: "ℹ",
        2: "⚠",
        3: "⊘",
        4: "➜",
    }

    return icons.get(category_id, "📘")


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
        placeholder="⌕  Cerca l'argomento",
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
            if search.casefold() in category["name"].casefold()
        ]

    if not categories:
        st.info("Nessun argomento trovato.")
        return

    for category in categories:
        category_id = category["id"]
        category_name = category["name"]
        progress = max(
            0,
            min(100, get_category_progress(category_id)),
        )

        with st.container(
            border=False,
            key=f"argomenti_category_{category_id}",
        ):
            icon_col, details_col, arrow_col = st.columns(
                [1.15, 8.2, 0.65],
                vertical_alignment="center",
                gap="small",
            )

            with icon_col:
                st.markdown(
                    '<div class="argomenti-category-icon">'
                    f'{safe_text(get_category_icon(category_id))}'
                    '</div>',
                    unsafe_allow_html=True,
                )

            with details_col:
                st.markdown(
                    '<div class="argomenti-category-name">'
                    f'{category_id} - {safe_text(category_name)}'
                    '</div>',
                    unsafe_allow_html=True,
                )

                progress_col, percentage_col = st.columns(
                    [9, 1],
                    vertical_alignment="center",
                    gap="small",
                )

                with progress_col:
                    st.progress(progress / 100)

                with percentage_col:
                    st.markdown(
                        '<span class="argomenti-progress-label">'
                        f'{progress}%</span>',
                        unsafe_allow_html=True,
                    )

            with arrow_col:
                if st.button(
                    "›",
                    key=f"open_category_{category_id}",
                    help=f"Open {category_name}",
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
        placeholder="⌕  Cerca l'argomento",
        key=f"argomenti_subtopic_search_{category_id}",
        label_visibility="collapsed",
    )

    if search:
        subtopics = [
            subtopic
            for subtopic in subtopics
            if search.casefold() in subtopic["name"].casefold()
        ]

    if not subtopics:
        st.info("Nessun sottoargomento trovato.")
        return

    for subtopic in subtopics:
        subtopic_id = subtopic["id"]
        completed = get_subtopic_completed(subtopic_id)
        preview = get_definition_preview(subtopic)

        with st.container(
            border=False,
            key=f"argomenti_subtopic_{subtopic_id}",
        ):
            status_col, details_col, arrow_col = st.columns(
                [0.8, 8.5, 0.7],
                vertical_alignment="center",
                gap="small",
            )

            with status_col:
                st.markdown(
                    '<div class="argomenti-status">'
                    + ("✓" if completed else "")
                    + "</div>",
                    unsafe_allow_html=True,
                )

            with details_col:
                st.markdown(
                    '<div class="argomenti-subtopic-name">'
                    f'{safe_text(subtopic["name"])}'
                    '</div>',
                    unsafe_allow_html=True,
                )

                if preview:
                    st.markdown(
                        '<div class="argomenti-preview">'
                        f'{safe_text(preview)}'
                        '</div>',
                        unsafe_allow_html=True,
                    )

            with arrow_col:
                if st.button(
                    "›",
                    key=f"open_subtopic_{subtopic_id}",
                    help=f'Open {subtopic["name"]}',
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
    load_argomenti_css()

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
