"""Load existing Patente B questions by saved IDs, preserving order."""
from database import get_connection


def fetch_questions_by_ids(question_ids):
    ids = [int(value) for value in question_ids]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Saved question IDs must be unique and nonempty")
    query = """
        SELECT q.id, q.question, q.correct_answer, q.image_path,
               q.subtopic_id, s.category_id AS chapter_id,
               c.name AS chapter_name
        FROM questions q
        JOIN subtopics s ON q.subtopic_id = s.id
        JOIN categories c ON s.category_id = c.id
        WHERE q.id = ANY(%s)
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (ids,))
            columns = [col.name for col in cur.description]
            records = [dict(zip(columns, row)) for row in cur.fetchall()]
    lookup = {record["id"]: record for record in records}
    if len(lookup) != len(ids):
        raise ValueError("Some saved quiz questions no longer exist")
    return [lookup[question_id] for question_id in ids]
