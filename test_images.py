from pathlib import Path

image_folder = Path("img_sign")
image_file = image_folder / "550.png"

if image_file.exists():
    print("Success! Python found the image.")
else:
    print("Image not found.")
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:

        cur.execute("""
            SELECT question, correct_answer, image_path
            FROM questions
            WHERE image_path IS NOT NULL
            LIMIT 1;
        """)

        result = cur.fetchone()

        print("Question:", result[0])
        print("Correct answer:", result[1])
        print("Image path:", result[2])