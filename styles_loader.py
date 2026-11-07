
import streamlit as st
from pathlib import Path


def load_css():
    """Load all shared CSS files into Streamlit."""

    # Find the folder containing this Python file
    project_folder = Path(__file__).resolve().parent

    # Locate our styles folder
    styles_folder = project_folder / "styles"

    # CSS files must load in this order
    
    css_files = [
    "variables.css",
    "base.css",
    "components.css",
    "layout.css"
]


    # Combine all CSS files
    combined_css = ""

    for filename in css_files:
        file_path = styles_folder / filename

        if file_path.exists():
            combined_css += file_path.read_text(
                encoding="utf-8"
            ) + "\n"
        else:
            st.warning(f"CSS file not found: {filename}")

    # Inject CSS into Streamlit
    if combined_css:
        st.html(f"<style>{combined_css}</style>")
