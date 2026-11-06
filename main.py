
import streamlit as st
from dashboard import show_dashboard

# Remember which page the user is viewing
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# WELCOME PAGE
if st.session_state.page == "welcome":
    st.title("Welcome to Patente B")
    st.write("Prepare for your Italian driving theory exam.")

    if st.button("OK"):
        st.session_state.page = "dashboard"
        st.rerun()

# DASHBOARD PAGE
elif  st.session_state.page == "dashboard":
    show_dashboard()
