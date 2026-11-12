
import streamlit as st

from quiz_attempt_storage import ensure_quiz_attempts_table

st.title("Patente B — Quiz Storage Test")

if st.button("Initialize Quiz Storage"):
    try:
        ensure_quiz_attempts_table()
        st.success(
            "Success! The quiz_attempts table is ready in PostgreSQL."
        )
    except Exception as error:
        st.error(f"Database error: {error}")
