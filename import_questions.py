import json

with open("quizPatenteB2023.json", "r", encoding="utf-8") as file:
    data = json.load(file)

print("JSON file loaded successfully!")
print("Total categories:", len(data))
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("DATABASE_URL")

with psycopg.connect(database_url) as conn:
    print("Successfully connected to Neon!")
    
    
with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cur.fetchall()

        for table in tables:
            print(table[0])
            
total_subtopics = 0
total_questions = 0

for category_name, subtopics in data.items():
    total_subtopics += len(subtopics)

    for subtopic_name, questions in subtopics.items():
        total_questions += len(questions)

print("Total subtopics:", total_subtopics)
print("Total questions:", total_questions)

with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:
        for category_slug in data:
            category_name = category_slug.replace("-", " ").title()

            cur.execute(
                """
                INSERT INTO categories (name, slug)
                VALUES (%s, %s)
                ON CONFLICT (slug) DO NOTHING;
                """,
                (category_name, category_slug)
            )

    conn.commit()

print("Categories imported successfully!")

with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:
        for category_slug, subtopics in data.items():

            cur.execute(
                "SELECT id FROM categories WHERE slug = %s",
                (category_slug,)
            )

            category_id = cur.fetchone()[0]

            for subtopic_slug in subtopics:
                subtopic_name = subtopic_slug.replace("-", " ").title()

                cur.execute(
                    """
                    INSERT INTO subtopics (category_id, name, slug)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (category_id, slug) DO NOTHING;
                    """,
                    (category_id, subtopic_name, subtopic_slug)
                )

    conn.commit()

print("Subtopics imported successfully!")

with psycopg.connect(database_url) as conn:
    with conn.cursor() as cur:

        for category_slug, subtopics in data.items():

            for subtopic_slug, questions in subtopics.items():

                cur.execute(
                    """
                    SELECT s.id
                    FROM subtopics s
                    JOIN categories c ON s.category_id = c.id
                    WHERE c.slug = %s AND s.slug = %s
                    """,
                    (category_slug, subtopic_slug)
                )

                result = cur.fetchone()

                if result is None:
                    raise ValueError(f"Subtopic not found: {subtopic_slug}")

                subtopic_id = result[0]

                for index, question in enumerate(questions):

                    cur.execute(
                        """
                        INSERT INTO questions
                        (question, correct_answer, category,
                         image_path, subtopic_id, source_index)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (subtopic_id, source_index)
                        DO NOTHING
                        """,
                        (
                            question["q"],
                            question["a"],
                            category_slug,
                            question.get("img"),
                            subtopic_id,
                            index
                        )
                    )

    conn.commit()

print("Questions imported successfully!")