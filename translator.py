
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import streamlit as st


@st.cache_data(show_spinner=False, ttl=86400)
def translate_to_english(italian_text):
    """Translate Italian text into English using MyMemory."""

    if not italian_text or not italian_text.strip():
        return ""

    params = urlencode({
        "q": italian_text.strip(),
        "langpair": "it|en",
        "mt": "1",
    })

    url = (
        "https://api.mymemory.translated.net/get?"
        + params
    )

    request = Request(
        url,
        headers={
            "User-Agent": "PatenteBQuiz/1.0"
        }
    )

    try:
        with urlopen(request, timeout=15) as response:
            data = json.load(response)

    except HTTPError as error:
        raise RuntimeError(
            f"Translation service HTTP error: {error.code}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            f"Cannot connect to translation service: {error.reason}"
        ) from error

    status = data.get("responseStatus", 200)

    if int(status) != 200:
        raise RuntimeError(
            f"MyMemory: {data.get('responseDetails', 'Request failed')}"
        )

    translated_text = data.get(
        "responseData", {}
    ).get("translatedText", "")

    if not translated_text:
        raise RuntimeError(
            "MyMemory returned an empty translation."
        )

    return translated_text
