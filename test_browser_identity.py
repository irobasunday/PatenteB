
import streamlit as st

from browser_identity import (
    get_browser_id,
    create_browser_id,
)

st.set_page_config(
    page_title="Patente B Identity Test"
)

st.title("Patente B — Unique Browser Identity")

saved_id = get_browser_id()

if saved_id:
    st.success("Browser identifier recovered!")
    st.code(saved_id)

else:
    st.warning(
        "No saved identifier was retrieved."
    )

    if st.button("Create Browser Identifier"):
        new_id = create_browser_id()
        st.write("Identifier submitted for saving:")
        st.code(new_id)

st.info(
    "After creating an identifier, "
    "refresh the browser and check "
    "whether the same ID is recovered."
)
