
"""
Patente B — Argomenti navigation and learning topics.

Optimized:
- Shared PostgreSQL connection pool
- Cached chapters and subtopics
- Batch chapter progress queries
- Batch subtopic completion queries

Preserves:
- Existing dark design and CSS
- Chapter images and numbering
- Search and navigation
- Saved learning progress
- Learning page integration
"""
import time
import os
import html
import base64

import streamlit as st
from psycopg.rows import dict_row

from database import get_connection
from browser_identity import get_browser_id

from learning.learning_progress import (
    get_category_progress as db_category_progress,
    get_subtopic_completed as db_subtopic_completed,
    get_all_category_progress,
    get_all_subtopic_completed,
)


# ==========================================
# DATABASE QUERIES
# ==========================================

@st.cache_data(ttl=300)
def get_categories():
    """Load chapters using the existing connection pool."""

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT id, name, slug
                FROM categories
                ORDER BY id
                """
            )
            return [
                dict(row)
                for row in cursor.fetchall()
            ]


@st.cache_data(ttl=300)
def get_subtopics(category_id):
    """Load subtopics using the existing connection pool."""

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT id, category_id, name, slug
                FROM subtopics
                WHERE category_id = %s
                ORDER BY id
                """,
                (category_id,),
            )
            return [
                dict(row)
                for row in cursor.fetchall()
            ]


# ==========================================
# PERSISTENT ARGOMENTI PROGRESS
# ==========================================

def get_category_progress(category_id):
    """Compatibility helper for chapter progress."""

    browser_id = get_browser_id()

    if not browser_id:
        return 0

    return db_category_progress(
        browser_id,
        category_id,
    )


def get_subtopic_completed(subtopic_id):
    """Compatibility helper for subtopic completion."""

    browser_id = get_browser_id()

    if not browser_id:
        return False

    return db_subtopic_completed(
        browser_id,
        subtopic_id,
    )


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

    return html.escape(
        str(value or ""),
        quote=True,
    )


def get_category_number(category_id, categories=None):
    """Get the chapter display number."""

    if categories is None:
        categories = get_categories()

    for number, category in enumerate(categories, start=1):
        if category["id"] == category_id:
            return number

    return None


def get_subtopic_number(subtopic_id, subtopics):
    """Get the original subtopic number."""

    for number, subtopic in enumerate(subtopics, start=1):
        if subtopic["id"] == subtopic_id:
            return number

    return None


def get_numbered_subtopics(subtopics):
    """Keep original numbering when searching."""

    return list(enumerate(subtopics, start=1))


# ==========================================
# LOAD ARGOMENTI CSS
# ==========================================

@st.cache_data
def read_argomenti_css():
    """Read the existing stylesheet once."""

    css_path = os.path.join(
        os.path.dirname(__file__),
        "styles",
        "argomenti.css",
    )

    if os.path.exists(css_path):
        with open(
            css_path,
            "r",
            encoding="utf-8",
        ) as file:
            return file.read()

    return ""


def load_argomenti_css():
    """Load the existing Argomenti stylesheet."""

    css = read_argomenti_css()

    if css:
        st.html(f"<style>{css}</style>")

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
# CATEGORY ICONS
# ==========================================

def get_category_icon(category_id):
    """Return a fallback icon when no image exists."""

    icons = {
        1: "ℹ",
        2: "⚠",
        3: "⊘",
        4: "➜",
    }

    return icons.get(category_id, "📘")


# ==========================================
# CATEGORY IMAGES
# ==========================================

def get_category_image(category_id):
    """Return the existing chapter image path."""

    filename = CATEGORY_IMAGES.get(category_id)

    if not filename:
        return None

    base_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

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


@st.cache_data
def get_encoded_category_image(image_path):
    """
    Cache image encoding so images are not
    repeatedly read and converted on reruns.
    """

    if not image_path:
        return None

    with open(image_path, "rb") as file:
        image_bytes = file.read()

    encoded_image = base64.b64encode(
        image_bytes
    ).decode("ascii")

    mime_type = (
        "image/png"
        if image_path.lower().endswith(".png")
        else "image/svg+xml"
    )

    return mime_type, encoded_image


# ==========================================
# URL NAVIGATION
# ==========================================

def update_argomenti_url(
    category_id=None,
    subtopic_id=None,
):
    """Save the current Argomenti location in the URL."""

    params = {
        "page": "argomenti",
    }

    if category_id is not None:
        params["category"] = str(category_id)

        if subtopic_id is not None:
            params["subtopic"] = str(subtopic_id)

    if dict(st.query_params) != params:
        st.query_params.clear()
        st.query_params.update(params)

    st.session_state._last_url_signature = (
        "argomenti",
        category_id,
        subtopic_id,
    )


def open_category(category_id):
    """Open a chapter and update the URL."""

    st.session_state.argomenti_category_id = category_id
    st.session_state.argomenti_subtopic_id = None

    update_argomenti_url(
        category_id=category_id,
    )

    st.rerun()


def open_subtopic(subtopic_id):
    """Open a Learning Page and update the URL."""

    category_id = st.session_state.argomenti_category_id

    st.session_state.argomenti_subtopic_id = subtopic_id

    update_argomenti_url(
        category_id=category_id,
        subtopic_id=subtopic_id,
    )

    st.rerun()


def back_to_categories():
    """Return to the chapter list."""

    st.session_state.argomenti_category_id = None
    st.session_state.argomenti_subtopic_id = None

    update_argomenti_url()

    st.rerun()


def back_to_subtopics():
    """Return to the current chapter's subtopics."""

    category_id = st.session_state.argomenti_category_id

    st.session_state.argomenti_subtopic_id = None

    update_argomenti_url(
        category_id=category_id,
    )

    st.rerun()


def back_to_dashboard():
    """Leave Argomenti and return to Dashboard."""

    st.session_state.argomenti_category_id = None
    st.session_state.argomenti_subtopic_id = None

    st.session_state.page = "dashboard"
    st.session_state.recovery_handled = False

    st.query_params.clear()

    st.session_state._last_url_signature = (
        "dashboard",
        None,
        None,
    )

    st.rerun()


# ==========================================
# PAGE HEADER
# ==========================================

def show_page_heading(title, back_action):
    """Show the back button and title."""

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

def show_category_card(
    category,
    category_number,
    progress_by_category=None,
):
    """Display a numbered chapter card."""

    category_id = category["id"]
    category_name = category["name"]

    # Use batch progress instead of a separate
    # PostgreSQL query for every chapter.
    if progress_by_category is not None:
        progress = progress_by_category.get(
            category_id,
            0,
        )
    else:
        progress = get_category_progress(category_id)

    progress = max(
        0,
        min(100, int(progress)),
    )

    icon = get_category_icon(category_id)
    image_path = get_category_image(category_id)

    if image_path:
        image_data = get_encoded_category_image(
            image_path
        )

        if image_data:
            mime_type, encoded_image = image_data

            icon_html = (
                '<img '
                f'src="data:{mime_type};base64,{encoded_image}" '
                f'alt="{safe_text(category_name)}" '
                'width="44" height="44" '
                'style="display:block;object-fit:contain;">'
            )
        else:
            icon_html = safe_text(icon)
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
# SUBTOPIC CARD
# ==========================================

def show_subtopic_card(
    subtopic,
    number,
    category_number,
    completed_by_subtopic=None,
):
    """Display a numbered subtopic card."""

    subtopic_id = subtopic["id"]
    subtopic_name = subtopic["name"]

    # Use batch completion results.
    if completed_by_subtopic is not None:
        completed = completed_by_subtopic.get(
            subtopic_id,
            False,
        )
    else:
        completed = get_subtopic_completed(
            subtopic_id
        )

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
    """Display all numbered chapters with loading-time diagnostics."""

    total_start = time.perf_counter()

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
        # ==========================================
        # 1. MEASURE CHAPTER LOADING
        # ==========================================

        chapters_start = time.perf_counter()

        categories = get_categories()

        chapters_time = (
            time.perf_counter() - chapters_start
        )

        # ==========================================
        # 2. MEASURE BROWSER ID
        # ==========================================

        identity_start = time.perf_counter()

        browser_id = get_browser_id()

        identity_time = (
            time.perf_counter() - identity_start
        )

        # ==========================================
        # 3. MEASURE POSTGRESQL PROGRESS
        # ==========================================

        progress_start = time.perf_counter()

        progress_by_category = (
            get_all_category_progress(browser_id)
            if browser_id
            else {}
        )

        progress_time = (
            time.perf_counter() - progress_start
        )

    except Exception as error:
        st.error(
            "Unable to load categories or progress "
            "from PostgreSQL."
        )
        st.exception(error)
        return

    # ==========================================
    # FILTER CHAPTERS
    # ==========================================

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

    # ==========================================
    # 4. MEASURE CARD RENDERING
    # ==========================================

    rendering_start = time.perf_counter()

    for category_number, category in numbered_categories:
        show_category_card(
            category,
            category_number,
            progress_by_category,
        )

    rendering_time = (
        time.perf_counter() - rendering_start
    )

    # ==========================================
    # 5. TOTAL LOADING TIME
    # ==========================================

    total_time = (
        time.perf_counter() - total_start
    )

    # ==========================================
    # PERFORMANCE DIAGNOSTICS
    # ==========================================

    st.divider()

    st.markdown("#### ⚡ Argomenti Performance Test")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Chapters",
            f"{chapters_time:.2f}s",
        )

    with col2:
        st.metric(
            "Browser ID",
            f"{identity_time:.2f}s",
        )

    with col3:
        st.metric(
            "Progress",
            f"{progress_time:.2f}s",
        )

    with col4:
        st.metric(
            "Rendering",
            f"{rendering_time:.2f}s",
        )

    st.caption(
        f"Total Python execution: {total_time:.2f}s "
        f"| Chapters displayed: {len(numbered_categories)}"
    )


# ==========================================
# SUBTOPICS SCREEN
# ==========================================

def show_subtopics(category_id):
    """Display numbered subtopics for a chapter."""

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

        browser_id = get_browser_id()

        # One PostgreSQL query checks all
        # subtopics in the selected chapter.
        completed_by_subtopic = (
            get_all_subtopic_completed(
                browser_id,
                category_id,
            )
            if browser_id
            else {}
        )

    except Exception as error:
        st.error(
            "Unable to load subtopics or progress "
            "from PostgreSQL."
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

    show_page_heading(
        f'{category_number} - {category["name"]}',
        back_to_categories,
    )

    numbered_subtopics = get_numbered_subtopics(
        subtopics
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

    for number, subtopic in numbered_subtopics:
        show_subtopic_card(
            subtopic,
            number,
            category_number,
            completed_by_subtopic,
        )


# ==========================================
# LEARNING PAGE
# ==========================================

def show_learning_page(category_id, subtopic_id):
    """
    Display the selected Learning Page.

    Preserve original numbering, translations,
    images, audio, and PostgreSQL integration.
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

    heading_number = (
        f"{category_number}.{subtopic_number}"
    )

    show_page_heading(
        f'{heading_number} {subtopic["name"]}',
        back_to_subtopics,
    )

    # Preserve existing Learning Page integration.
    from learning.learning_page import (
        show_learning_page as render_learning_content
    )

    render_learning_content(
        subtopic_id,
        subtopic["name"],
    )


# ==========================================
# MAIN ARGOMENTI ENTRY POINT
# ==========================================

def show_argomenti():
    """Main Argomenti navigation controller."""

    

    if "argomenti_category_id" not in st.session_state:
        st.session_state.argomenti_category_id = None

    if "argomenti_subtopic_id" not in st.session_state:
        st.session_state.argomenti_subtopic_id = None

    category_id = (
        st.session_state.argomenti_category_id
    )

    subtopic_id = (
        st.session_state.argomenti_subtopic_id
    )

    if category_id is None:
        show_categories()

    elif subtopic_id is None:
        show_subtopics(category_id)

    else:
        show_learning_page(
            category_id,
            subtopic_id,
        )
