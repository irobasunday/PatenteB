
import streamlit as st
from google import genai


def generate_question_explanation(
    italian_question,
    english_translation,
    correct_answer,
):
    """Generate an English explanation for a Patente B question."""

    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an Italian Patente B driving theory tutor.

Explain the following official driving-theory question
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
- Do not invent legal articles, fines or penalties.
- If the explanation cannot be verified from the
  supplied information, clearly state the uncertainty.
- Return only the explanation.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    explanation = (response.text or "").strip()

    if not explanation:
        raise RuntimeError("Gemini returned an empty explanation.")

    return explanation
