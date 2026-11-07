
import streamlit as st
from pathlib import Path
import base64


# Project folder and logo
PROJECT_FOLDER = Path(__file__).resolve().parent.parent
LOGO_PATH = PROJECT_FOLDER / "assets" / "logo.png"


def navigate(page):
    """Navigate to another application page."""
    st.session_state.page = page
    st.rerun()


def open_quiz():
    """Open the quiz selection modal."""
    st.session_state.open_quiz_modal = True
    st.rerun()


def get_logo_data():
    """Convert the local logo into an embedded image."""
    if not LOGO_PATH.exists():
        return None

    image_bytes = LOGO_PATH.read_bytes()
    return base64.b64encode(image_bytes).decode("utf-8")


def show_brand(mobile=False):
    """Show a large logo and the app name side by side."""

    logo_data = get_logo_data()
    brand_key = "pb_brand_mobile" if mobile else "pb_brand_desktop"

    if logo_data:
        logo_html = (
            f'<img src="data:image/png;base64,{logo_data}" '
            'alt="Patente B logo">'
        )
    else:
        logo_html = '<span class="pb-brand-fallback">🚗</span>'

    with st.container(key=brand_key):
        st.html(
            f"""
            <div class="pb-brand">
                <div class="pb-brand-logo">
                    {logo_html}
                </div>
                <span class="pb-brand-name">Patente B</span>
            </div>
            """
        )


def show_header():
    """Reusable responsive Patente B header."""

    with st.container(key="pb_header"):

        # DESKTOP HEADER
        with st.container(key="pb_desktop_header"):

            brand, navigation, language, profile = st.columns(
                [3.5, 3.5, 1.5, 0.7],
                vertical_alignment="center"
            )

            with brand:
                show_brand()

            with navigation:
                home, quiz, results = st.columns(3)

                with home:
                    if st.button("Home", key="header_home"):
                        navigate("dashboard")

                with quiz:
                    if st.button("Quiz", key="header_quiz"):
                        open_quiz()

                with results:
                    if st.button("Results", key="header_results"):
                        navigate("results")

            with language:
                st.selectbox(
                    "Language",
                    ["🇮🇹 IT", "🇬🇧 EN"],
                    key="desktop_language",
                    label_visibility="collapsed"
                )

            with profile:
                st.markdown("👤")

        # MOBILE HEADER
        with st.container(key="pb_mobile_header"):

            brand, language, profile, menu = st.columns(
                [3, 2, 0.6, 1],
                vertical_alignment="center",
                gap="small"
            )

            with brand:
                show_brand(mobile=True)

            with language:
                st.selectbox(
                    "Language",
                    ["🇮🇹 IT", "🇬🇧 EN"],
                    key="mobile_language",
                    label_visibility="collapsed"
                )

            with profile:
                st.markdown("👤")

            with menu:
                with st.popover("☰"):
                    st.markdown("**Navigation**")

                    if st.button(
                        "🏠 Home",
                        key="mobile_home",
                        use_container_width=True
                    ):
                        navigate("dashboard")

                    if st.button(
                        "📖 Quiz",
                        key="mobile_quiz",
                        use_container_width=True
                    ):
                        open_quiz()

                    if st.button(
                        "📊 Results",
                        key="mobile_results",
                        use_container_width=True
                    ):
                        navigate("results")

                    if st.button(
                        "⚙ Settings",
                        key="mobile_settings",
                        use_container_width=True
                    ):
                        navigate("settings")
