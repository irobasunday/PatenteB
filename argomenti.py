
"""Patente B — Argomenti navigation and learning topics."""

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
    """Load chapters in their original database order."""

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
    """Load subtopics in their original database order."""

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
    """Placeholder for future PostgreSQL progress tracking."""
    return 0


def get_subtopic_completed(subtopic_id):
    """Placeholder for future lesson completion tracking."""
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
    """Definitions are not connected yet."""

    return short_description(
        subtopic.get("definition", "")
    )


# ==========================================
# HELPERS
# ==========================================

def safe_text(value):
    """Escape database text before inserting into HTML."""

    return html.escape(str(value or ""), quote=True)


def get_category_number(category_id, categories=None):
    """
    Return a chapter's display number.

    Chapter numbering is based on the original
    category order, not the database ID itself.
    """

    if categories is None:
        categories = get_categories()

    for number, category in enumerate(categories, start=1):
        if category["id"] == category_id:
            return number

    return None


def get_subtopic_number(subtopic_id, subtopics):
    """
    Return a subtopic's position within its chapter.

    Searching does not change the original number.
    """

    for number, subtopic in enumerate(subtopics, start=1):
        if subtopic["id"] == subtopic_id:
            return number

    return None


def get_numbered_subtopics(subtopics):
    """Keep the original numbering for all subtopics."""

    return list(enumerate(subtopics, start=1))


# ==========================================
# LOAD ARGOMENTI CSS
# ==========================================

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

    st.html(
        """
        <style>

        /* ==========================================
           SUBTOPIC NUMBER STYLING
           ========================================== */

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

CATEGORY_IMAGES = {
    1: "img_sign/562.png",
    2: "discesa_pericolosa.svg",
    3: "divieto_di_accesso.svg",
    4: "direzione_obbligatoria_a_destra.svg",
    5: "dare_precedenza.svg",
    6: "img_sign/517.png",
    7: "semaforo_verticale.svg",
    8: "rifornimento.svg",
    9: "img_sign/276.png",
    10: "estesa.svg",
    11: "limite_di_velocita_50.svg",
    12: "distanziamento_minimo_obbligatorio.svg",
    13: "img_sign/502.png",
    14: "chapter_14.png",
    15: "divieto_di_sorpasso.svg",
    16: "divieto_di_fermata.svg",
    17: "Inizio_autostrada.svg",
    18: "img_sign/696.png",
    19: "img_sign/707.png",
    20: "chapter_20.png",
    21: "incidente.svg",
    22: "dogana.svg",
    23: "chapter_23.png",
    24: "chapter_24.png",
    25: "chapter_25.png",
}


# ==========================================
# DEFAULT CATEGORY ICONS
# ==========================================

def get_category_icon(category_id):
    """Return the default icon when no image exists."""

    icons = {
        1: "ℹ",
        2: "⚠",
        3: "⊘",
        4: "➜",
    }

    return icons.get(category_id, "📘")


# ==========================================
# GET CATEGORY IMAGE
# ==========================================

def get_category_image(category_id):
    """Return the existing chapter image if available."""

    filename = CATEGORY_IMAGES.get(category_id)

    if not filename:
        return None

    base_dir = os.path.dirname(os.path.abspath(__file__))

    if filename.startswith("img_sign/"):
        image_path = os.path.join(
            base_dir,
            filename,
        )
    else:
        image_path = os.path.join(
            base_dir,
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

    page_key = (
        f"argomenti_page_heading_"
        f"{st.session_state.get('argomenti_category_id')}_"
        f"{st.session_state.get('argomenti_subtopic_id')}"
    )

    back_key = (
        f"argomenti_page_back_"
        f"{st.session_state.get('argomenti_category_id')}_"
        f"{st.session_state.get('argomenti_subtopic_id')}"
    )

    with st.container(key=page_key):
        with st.container(
            horizontal=True,
            vertical_alignment="center",
        ):

            if st.button(
                "❮",
                key=back_key,
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

def show_category_card(category, category_number):
    """
    Display a numbered chapter using the existing card.

    Example:
        1 - Definizioni Generali Doveri Strada
        2 - Next chapter

    The entire card remains clickable.
    """

    category_id = category["id"]
    category_name = category["name"]

    progress = get_category_progress(category_id)
    progress = max(0, min(100, int(progress)))

    icon = get_category_icon(category_id)
    image_path = get_category_image(category_id)

    if image_path:
        with open(image_path, "rb") as file:
            image_bytes = file.read()

        encoded_image = base64.b64encode(
            image_bytes
        ).decode("ascii")

        if image_path.lower().endswith(".png"):
            mime_type = "image/png"
        else:
            mime_type = "image/svg+xml"

        icon_html = (
            '<img '
            f'src="data:{mime_type};base64,{encoded_image}" '
            f'alt="{safe_text(category_name)}" '
            'width="44" height="44" '
            'style="display:block;object-fit:contain;">'
        )

    else:
        icon_html = safe_text(icon)

    card_html = f"""
    <div class="argomenti-card-content">

        <div class="argomenti-category-icon">
            {icon_html}
        </div>

        <div class="argomenti-card-details">

            <div class="argomenti-category-name">
                {category_number} - {safe_text(category_name)}
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
            "Open chapter",
            key=f"open_category_{category_id}",
            help=f"Open {category_name}",
            use_container_width=True,
        ):
            open_category(category_id)


# ==========================================
# SUBTOPIC CARD — HIERARCHICAL NUMBERING
# ==========================================

def show_subtopic_card(subtopic, number, category_number):
    """
    Display a subtopic with automatic numbering.

    Examples:
        Chapter 1: 1.1, 1.2, 1.3
        Chapter 2: 2.1, 2.2, 2.3

    The entire card remains clickable.
    """

    subtopic_id = subtopic["id"]
    subtopic_name = subtopic["name"]

    completed = get_subtopic_completed(subtopic_id)
    preview = get_definition_preview(subtopic)

    status_symbol = f"{category_number}.{number}"

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
            "Open subtopic",
            key=f"open_subtopic_{subtopic_id}",
            help=f"Open {subtopic_name}",
            use_container_width=True,
        ):
            open_subtopic(subtopic_id)


# ==========================================
# CATEGORIES SCREEN
# ==========================================

def show_categories():
    """Display all numbered chapters."""

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

    # Number all chapters before filtering.
    numbered_categories = list(
        enumerate(categories, start=1)
    )

    if search:
        numbered_categories = [
            (number, category)
            for number, category in numbered_categories
            if search.casefold()
            in category["name"].casefold()
        ]

    if not numbered_categories:
        st.info("Nessun argomento trovato.")
        return

    for category_number, category in numbered_categories:
        show_category_card(
            category,
            category_number,
        )


# ==========================================
# SUBTOPICS SCREEN
# ==========================================

def show_subtopics(category_id):
    """Display numbered subtopics for the selected chapter."""

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

    category_number = get_category_number(
        category_id,
        categories,
    )

    # Numbered chapter heading.
    show_page_heading(
        f'{category_number} - {category["name"]}',
        back_to_categories,
    )

    # Preserve original subtopic numbering.
    numbered_subtopics = get_numbered_subtopics(
        subtopics
    )

    search = st.text_input(
        "Cerca il sottoargomento",
        placeholder="⌕  Cerca l'argomento",
        key=f"argomenti_subtopic_search_{category_id}",
        label_visibility="collapsed",
    )

    # Filter without renumbering.
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

    for number, subtopic in numbered_subtopics:
        show_subtopic_card(
            subtopic,
            number,
            category_number,
        )


# ==========================================
# LEARNING PAGE
# ==========================================

def show_learning_page(category_id, subtopic_id):
    """
    Display the selected Learning Page with
    automatic hierarchical numbering.

    Examples:
        1.1 Carreggiata Doppio Senso
        1.2 Next subtopic
        2.1 First subtopic of Chapter 2
    """

    try:
        categories = get_categories()
        subtopics = get_subtopics(category_id)

    except Exception as error:
        st.error("Unable to load learning topic.")
        st.exception(error)
        return

    category_number = get_category_number(
        category_id,
        categories,
    )

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

    subtopic_number = get_subtopic_number(
        subtopic_id,
        subtopics,
    )

    # Build the same number shown on the subtopic card.
    heading_number = (
        f"{category_number}.{subtopic_number}"
    )

    # Display the numbered heading.
    show_page_heading(
        f'{heading_number} {subtopic["name"]}',
        back_to_subtopics,
    )

    # Keep the existing Learning Page integration.
    from learning.learning_page import (
        show_learning_page as render_learning_content
    )

    # Display real PostgreSQL questions, images,
    # English translations and Italian audio.
    render_learning_content(
        subtopic_id,
        subtopic["name"],
    )


# ==========================================
# MAIN ARGOMENTI ENTRY POINT
# ==========================================

def show_argomenti():
    """Main Argomenti navigation controller."""

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
        show_learning_page(
            category_id,
            subtopic_id,
        )
