
import streamlit as st
from streamlit_local_storage import LocalStorage

st.set_page_config(page_title="Browser Storage Test")

st.title("Patente B — Storage Diagnostic")

storage = LocalStorage()

if st.button("Save Test Value"):
    storage.setItem("patenteb_test", "HELLO123")
    st.success("Save command sent.")

if st.button("Read Test Value"):
    value = storage.getItem("patenteb_test")
    st.write("Retrieved value:", value)

st.info("Check Chrome Developer Tools → Application → Local storage.")
