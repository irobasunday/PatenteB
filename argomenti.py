
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
    """Load categories from the existing PostgreSQL database."""

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
    """Load subtopics belonging to the selected category."""

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
# FUTURE STUDENT PROGRESS
# ==========================================

def get_category_progress(category_id):
    """
    Future database integration.

    Return actual completed lesson percentage
    when student progress tracking is available.
    """
    return 0


def get_subtopic_completed(subtopic_id):
    """
    Future database integration for individual
    student lesson completion.
    """
    return False


# ==========================================
# DEFINITION PREVIEWS
# ==========================================

def short_description(definition):
    """First 30 characters, followed by ... when longer."""

    if not definition:
        return ""

    definition = str(definition).strip()

    if len(definition) > 30:
        return definition[:30].rstrip() + "..."

    return definition


def get_definition_preview(subtopic):
    """
    Definitions are not connected yet.

    Once the Italian definitions are stored,
    this function will show their previews.
    """
    return short_description(
        subtopic.get("definition", "")
    )


# ==========================================
# HELPERS
# ==========================================

def safe_text(value):
    """Escape text before inserting it into HTML."""
    return html.escape(str(value or ""), quote=True)


def load_argomenti_css():
    """Load the dedicated Argomenti stylesheet."""

    css_path = os.path.join(
        os.path.dirname(__file__),
        "styles",
        "argomenti.css",
    )

    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as file:
            st.html(f"<style>{file.read()}</style>")


def get_category_icon(category_id):
    """Category icons; real images can be connected later."""

    icons = {
        1: "ℹ",
        2: "⚠",
        3: "⊘",
        4: "➜",
    }

    return icons.get(category_id, "📘")


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
# PAGE HEADER
# ==========================================

def show_page_heading(title, back_action):
    """
    One compact header.

    The back button is a real Streamlit button.
    CSS positions it beside the heading.
    """

    with st.container(key="argomenti_page_heading"):

        st.html(
            '<div class="argomenti-heading-title">'
            f'{safe_text(title)}'
            '</div>'
        )

        if st.button(
            "‹",
            key="argomenti_page_back",
            help="Go back",
        ):
            back_action()


# ==========================================
# CATEGORY CARD
# ==========================================

def show_category_card(category):
    """
    Render a category using one HTML Flexbox layout.

    The invisible Streamlit button overlays the
    card, making the entire card clickable.

    No Streamlit columns are used.
    """

    category_id = category["id"]
    category_name = category["name"]

    progress = get_category_progress(category_id)
    progress = max(0, min(100, int(progress)))

    icon = get_category_icon(category_id)

    card_html = f"""
    <div class="argomenti-card-content">

        <div class="argomenti-category-icon">
            {safe_text(icon)}
        </div>

        <div class="argomenti-card-details">

            <div class="argomenti-category-name">
                {category_id} - {safe_text(category_name)}
            </div>

            <div class="argomenti-progress-row">

                <div
                    class="argomenti-progress-track"
                    role="progressbar"
                    aria-label="Learning progress"
                    aria-valuenow="{progress}"
                    aria-valuemin="0"
                    aria-valuemax="100"
                >
                    <div
                        class="argomenti-progress-fill"
                        style="width: {progress}%"
                    ></div>
                </div>

                <span class="argomenti-progress-label">
                    {progress}%
                </span>

            </div>

        </div>

        <div class="argomenti-card-arrow"
             aria-hidden="true">
            &#8250;
        </div>

    </div>
    """

    with st.container(
        border=False,
        key=f"argomenti_category_{category_id}",
    ):

        st.html(card_html)

        if st.button(
            f"Open {category_name}",
            key=f"open_category_{category_id}",
            help=f"Open {category_name}",
        ):
            open_category(category_id)


# ==========================================
# SUBTOPIC CARD
# ==========================================

def show_subtopic_card(subtopic):
    """
    Compact subtopic card.

    Uses the same responsive card system
    as categories.
    """

    subtopic_id = subtopic["id"]
    subtopic_name = subtopic["name"]

    completed = get_subtopic_completed(subtopic_id)
    preview = get_definition_preview(subtopic)

    status_symbol = "✓" if completed else ""
    status_class = (
        "argomenti-status completed"
        if completed
        else "argomenti-status"
    )

    preview_html = ""

    if preview:
        preview_html = (
            '<div class="argomenti-preview">'
            f'{safe_text(preview)}'
            '</div>'
        )

    card_html = f"""
    <div class="argomenti-card-content">

        <div class="{status_class}"
             aria-hidden="true">
            {status_symbol}
        </div>

        <div class="argomenti-card-details">

            <div class="argomenti-subtopic-name">
                {safe_text(subtopic_name)}
            </div>

            {preview_html}

        </div>

        <div class="argomenti-card-arrow"
             aria-hidden="true">
            &#8250;
        </div>

    </div>
    """

    with st.container(
        border=False,
        key=f"argomenti_subtopic_{subtopic_id}",
    ):

        st.html(card_html)

        if st.button(
            f"Open {subtopic_name}",
            key=f"open_subtopic_{subtopic_id}",
            help=f"Open {subtopic_name}",
        ):
            open_subtopic(subtopic_id)


# ==========================================
# CATEGORIES SCREEN
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
        st.error(
            "Unable to load categories from PostgreSQL."
        )
        st.exception(error)
        return

    if search:
        categories = [
            category
            for category in categories
            if search.casefold()
            in category["name"].casefold()
        ]

    if not categories:
        st.info("Nessun argomento trovato.")
        return

    for category in categories:
        show_category_card(category)


# ==========================================
# SUBTOPICS SCREEN
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
        st.error(
            "Unable to load subtopics from PostgreSQL."
        )
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
            if search.casefold()
            in subtopic["name"].casefold()
        ]

    if not subtopics:
        st.info("Nessun sottoargomento trovato.")
        return

    for subtopic in subtopics:
        show_subtopic_card(subtopic)


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
