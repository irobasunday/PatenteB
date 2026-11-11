
import os
import html
import base64
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
    """Load categories from the existing database."""

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
    """Load subtopics for the selected category."""

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
    Placeholder for future PostgreSQL progress tracking.
    """
    return 0


def get_subtopic_completed(subtopic_id):
    """
    Placeholder for future lesson completion tracking.
    """
    return False


# ==========================================
# DEFINITION PREVIEWS
# ==========================================

def short_description(definition):
    """Show 30 characters followed by ... if longer."""

    if not definition:
        return ""

    definition = str(definition).strip()

    if len(definition) > 30:
        return definition[:30].rstrip() + "..."

    return definition


def get_definition_preview(subtopic):
    """
    Definitions are not connected yet.
    """
    return short_description(
        subtopic.get("definition", "")
    )


# ==========================================
# HELPERS
# ==========================================

def safe_text(value):
    """Escape database text before inserting into HTML."""
    return html.escape(str(value or ""), quote=True)


def load_argomenti_css():
    """Load the existing Argomenti stylesheet."""

    css_path = os.path.join(
        os.path.dirname(__file__),
        "styles",
        "argomenti.css",
    )

    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as file:
            st.html(f"<style>{file.read()}</style>")

    # Number styling is scoped to subtopic cards.
    # It does not modify the existing category cards.
    st.html(
        """
        <style>
        .argomenti-card-content
        .argomenti-subtopic-number {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;

            flex: 0 0 auto !important;
            width: auto !important;
            min-width: 48px !important;
            height: 34px !important;
            padding: 0 8px !important;

            border: 1px solid #52647d !important;
            border-radius: 10px !important;

            background: #253650 !important;
            color: #ffffff !important;

            font-size: 14px !important;
            font-weight: 700 !important;
            line-height: 1 !important;
            white-space: nowrap !important;

            box-sizing: border-box !important;
            visibility: visible !important;
            opacity: 1 !important;
        }

        .argomenti-card-content
        .argomenti-subtopic-number.completed {
            border-color: #3e9c76 !important;
            background: #204638 !important;
            color: #ffffff !important;
        }
        </style>
        """
    )


# ==========================================
# MANUAL ROAD SIGN IMAGE MAPPING
# ==========================================
#
# Left: PostgreSQL category ID
# Right: Exact SVG filename inside assets/road_signs/
#
# You can change the filenames whenever you want.
# If a file is missing, the default icon will appear.
#
# Example:
# 4: "segnale_obbligo.svg",
#
# ==========================================

CATEGORY_IMAGES = {
    1: "chapter_1.svg",
    2: "chapter_2.svg",
    3: "divieto_di_accesso.svg",
}


# ==========================================
# DEFAULT CATEGORY ICONS
# ==========================================

def get_category_icon(category_id):
    """Return the default icon when no SVG image exists."""

    icons = {
        1: "ℹ",
        2: "⚠",
        3: "⊘",
        4: "➜",
    }

    return icons.get(category_id, "📘")


# ==========================================
# GET MANUALLY ASSIGNED SVG IMAGE
# ==========================================

def get_category_image(category_id):
    """Return the SVG image assigned to a chapter."""

    filename = CATEGORY_IMAGES.get(category_id)

    if not filename:
        return None

    image_path = os.path.join(
        os.path.dirname(__file__),
        "assets",
        "road_signs",
        filename,
    )

    if os.path.isfile(image_path):
        return image_path

    return None


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
    """Show back button and title on the same line."""

    with st.container(key="argomenti_page_heading"):
        with st.container(
            horizontal=True,
            vertical_alignment="center",
        ):

            if st.button(
                "❮",
                key="argomenti_page_back",
                help="Back to previous page",
            ):
                back_action()

            st.markdown(
                f'<div class="argomenti-heading-title">'
                f'{safe_text(title)}</div>',
                unsafe_allow_html=True,
            )


# ==========================================
# CATEGORY CARD
# ==========================================

def show_category_card(category):
    """
    Display a category using the existing Flexbox card.

    Show the manually assigned SVG image when available.
    Otherwise, show the original category icon.
    """

    category_id = category["id"]
    category_name = category["name"]

    progress = get_category_progress(category_id)
    progress = max(0, min(100, int(progress)))

    # Get the original fallback icon.
    icon = get_category_icon(category_id)

    # Look for a manually assigned SVG image.
    image_path = get_category_image(category_id)

    if image_path:
        # Load and encode the SVG for HTML display.
        with open(image_path, "rb") as file:
            svg_bytes = file.read()

        encoded_svg = base64.b64encode(
            svg_bytes
        ).decode("ascii")

        icon_html = (
    '<img '
    f'src="data:image/svg+xml;base64,{encoded_svg}" '
    f'alt="{safe_text(category_name)}" '
    'width="44" height="44" '
    'style="display:block;object-fit:contain;">'
)

    else:
        # No SVG assigned, or the image file is missing.
        # Keep the original icon.
        icon_html = safe_text(icon)

    # Preserve the existing category card HTML.
    card_html = f"""
    <div class="argomenti-card-content">

        <div class="argomenti-category-icon">
            {icon_html}
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

        <div
            class="argomenti-card-arrow"
            aria-hidden="true"
        >
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
            "›",
            key=f"open_category_{category_id}",
            help=f"Open {category_name}",
        ):
            open_category(category_id)


# ==========================================
# SUBTOPIC CARD - HIERARCHICAL NUMBERING
# ==========================================

def show_subtopic_card(subtopic, number, category_number):
    """
    Display a subtopic with hierarchical numbering.

    Examples:
        Category 1: 1.1, 1.2, 1.3
        Category 2: 2.1, 2.2, 2.3

    Preserve the existing card design and navigation.
    """

    subtopic_id = subtopic["id"]
    subtopic_name = subtopic["name"]

    completed = get_subtopic_completed(subtopic_id)
    preview = get_definition_preview(subtopic)

    # Hierarchical number, e.g. 1.1 or 2.3
    status_symbol = f"{category_number}.{number}"

    # Use a dedicated class instead of argomenti-status.
    # The old class was designed for an empty circle.
    number_class = (
        "argomenti-subtopic-number completed"
        if completed
        else "argomenti-subtopic-number"
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

        <div
            class="{number_class}"
            aria-label="Subtopic {status_symbol}"
        >
            {status_symbol}
        </div>

        <div class="argomenti-card-details">

            <div class="argomenti-subtopic-name">
                {safe_text(subtopic_name)}
            </div>

            {preview_html}

        </div>

        <div
            class="argomenti-card-arrow"
            aria-hidden="true"
        >
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
            "›",
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
    
        # TEST ROAD SIGN FILE
    image_path = os.path.join(
        os.path.dirname(__file__),
        "assets",
        "road_signs",
        "divieto_di_accesso.svg",
    )

    st.write("Image exists:", os.path.isfile(image_path))
    st.write("Image size:", os.path.getsize(image_path) if os.path.isfile(image_path) else "Not found")

    if os.path.isfile(image_path):
        with open(image_path, "r", encoding="utf-8") as file:
            st.code(file.read()[:500], language="xml")

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

    # Show category number in the heading.
    show_page_heading(
        f'{category_id}. {category["name"]}',
        back_to_categories,
    )

    # Number subtopics before filtering.
    # Searching must not change their original numbers.
    numbered_subtopics = list(
        enumerate(subtopics, start=1)
    )

    search = st.text_input(
        "Cerca il sottoargomento",
        placeholder="⌕  Cerca l'argomento",
        key=f"argomenti_subtopic_search_{category_id}",
        label_visibility="collapsed",
    )

    if search:
        numbered_subtopics = [
            (number, subtopic)
            for number, subtopic in numbered_subtopics
            if search.casefold()
            in subtopic["name"].casefold()
        ]

    if not numbered_subtopics:
        st.info("Nessun sottoargomento trovato.")
        return

    # Example: category 1, subtopic 3 = 1.3
    for number, subtopic in numbered_subtopics:
        show_subtopic_card(
            subtopic,
            number,
            category_id,
        )


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
load_argomenti_css()
image_path = get_category_image(3)

if image_path:
    st.success("Chapter 3 SVG image found on server!")
    st.write("Image location:", image_path)
else:
    st.error("divieto_di_accesso.svg NOT FOUND on server!")