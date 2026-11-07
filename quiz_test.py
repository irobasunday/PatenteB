
import streamlit as st
import psycopg
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

database_url = os.getenv("DATABASE_URL")

st.title("Patente B - Quiz Test")

# Retrieve a question from Neon
with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT question, correct_answer, image_path
            FROM questions
            WHERE image_path IS NOT NULL
            LIMIT 1;
        """)

        result = cur.fetchone()

if result:
    question = result[0]
    correct_answer = result[1]
    image_path = result[2]

    # Display the question
    st.write(question)

    # Display the image
    image_file = Path(__file__).parent / image_path.lstrip("/")

    if image_file.exists():
        st.image(str(image_file), width=350)
    else:
        st.error("Image not found")

    # Answer buttons
    st.subheader("Choose your answer")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Vero"):
            if correct_answer == True:
                st.success("Correct answer!")
            else:
                st.error("Wrong answer!")

    with col2:
        if st.button("Falso"):
            if correct_answer == False:
                st.success("Correct answer!")
            else:
                st.error("Wrong answer!")

else:
    st.warning("No questions found.")
