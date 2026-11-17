import mimetypes
import threading
from concurrent.futures import ThreadPoolExecutor

import streamlit as st
from google import genai
from google.genai import types


# Shared across Streamlit sessions.
# Limit concurrent Gemini requests.
_executor = ThreadPoolExecutor(max_workers=3)
_tasks = {}
_tasks_lock = threading.Lock()


def generate_question_explanation(
    italian_question,
    english_translation,
    correct_answer,
    api_key,
    image_bytes=None,
    image_mime_type=None,
):
    """
    Generate an English explanation.

    This function is safe to run in a background thread:
    it does not access Streamlit widgets, secrets,
    session state, or database connections.
    """

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    prompt = f"""
You are an Italian Patente B driving theory tutor.

Explain this official Italian driving-theory question
in clear, simple English.

Italian question:
{italian_question}

English translation:
{english_translation}

Official correct answer:
{correct_answer}

Requirements:
- Explain WHY the official answer is correct.
- Use simple English suitable for beginners.
- Keep the explanation between 50 and 100 words.
- Do not change the official correct answer.
- Do not invent legal articles, fines, or penalties.
- If an image is provided, examine it carefully.
- If the image or supplied information is insufficient,
  clearly state the uncertainty.
- Return only the explanation.
"""

    contents = [prompt]

    if image_bytes and image_mime_type:
        contents.append(
            types.Part.from_bytes(
                data=image_bytes,
                mime_type=image_mime_type,
            )
        )

    # Create and close the client inside the worker.
    with genai.Client(api_key=api_key) as client:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=350,
                http_options=types.HttpOptions(
                    timeout=12000,
                ),
            ),
        )

    explanation = (response.text or "").strip()

    if not explanation:
        raise RuntimeError(
            "Gemini returned an empty explanation."
        )

    return explanation


def start_explanation_task(
    question_id,
    italian_question,
    english_translation,
    correct_answer,
    image_file=None,
):
    """
    Start Gemini without blocking the Streamlit page.

    Return the Future representing the task.
    """

    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    image_bytes = None
    image_mime_type = None

    if image_file:
        image_mime_type, _ = mimetypes.guess_type(
            str(image_file)
        )

        if image_mime_type in (
            "image/png",
            "image/jpeg",
            "image/webp",
        ):
            image_bytes = image_file.read_bytes()
        else:
            raise ValueError(
                "Unsupported question image format."
            )

    # Prevent duplicate simultaneous requests
    # for the same question.
    task_key = int(question_id)

    with _tasks_lock:
        existing = _tasks.get(task_key)

        if existing is not None:
            return existing

        future = _executor.submit(
            generate_question_explanation,
            italian_question,
            english_translation,
            correct_answer,
            api_key,
            image_bytes,
            image_mime_type,
        )

        _tasks[task_key] = future

        return future