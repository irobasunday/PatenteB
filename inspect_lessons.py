
import streamlit as st
from argomenti import get_connection

st.title("Inspect Existing Lesson Database")

try:
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    table_name,
                    column_name,
                    data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
            """)

            rows = cur.fetchall()

    st.success("Database structure loaded successfully.")

    for row in rows:
        st.write(row)

except Exception as error:
    st.error("Unable to inspect database.")
    st.error(str(error))
