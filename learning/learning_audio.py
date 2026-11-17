
"""Italian question audio for the Patente B Learning Page."""

import json
import streamlit.components.v1 as components


def show_learning_audio(question_text, question_id):
    """Display a compact Italian Play/Pause audio button."""

    text_json = json.dumps(
        str(question_text),
        ensure_ascii=False
    ).replace("<", "\\u003c").replace(
        "\u2028", "\\u2028"
    ).replace(
        "\u2029", "\\u2029"
    )

    html_code = r"""
<div class="audio-controls">
  <button id="playButton" type="button">
    ▶ Ascolta in italiano
  </button>
</div>

<style>
  * {
    box-sizing: border-box;
  }

  html, body {
    margin: 0;
    padding: 0;
    background: transparent;
    font-family: system-ui, sans-serif;
  }

  .audio-controls {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    padding: 8px 0;
  }

  #playButton {
    background: #2563eb;
    color: white;
    border: 1px solid #60a5fa;
    border-radius: 12px;
    padding: 12px 22px;
    min-height: 48px;
    font-family: inherit;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s ease;
  }

  #playButton:hover {
    background: #1d4ed8;
  }

  #playButton:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>

<script>
(() => {

  const questionText = __QUESTION_TEXT__;

  const playButton =
    document.getElementById("playButton");

  const supported =
    "speechSynthesis" in window &&
    "SpeechSynthesisUtterance" in window;

  if (!supported) {
    playButton.disabled = true;
    playButton.textContent = "Audio unavailable";
    return;
  }

  const synth = window.speechSynthesis;

  let playing = false;
  let paused = false;
  let playToken = 0;
  let currentUtterance = null;

  function chooseVoice() {
    const voices = synth.getVoices();

    const italian = voices.filter(
      v => /^it([_-]|$)/i.test(v.lang)
    );

    return italian.find(
      v => /google italiano/i.test(v.name)
    ) ||
    italian.find(
      v => /google/i.test(v.name)
    ) ||
    italian.find(
      v => v.localService
    ) ||
    italian[0] ||
    null;
  }

  function resetButton() {
    playing = false;
    paused = false;
    currentUtterance = null;
    playButton.textContent = "▶ Ascolta in italiano";
  }

  function play() {

    if (paused && currentUtterance) {
      synth.resume();
      paused = false;
      playing = true;
      playButton.textContent = "⏸ Pause";
      return;
    }

    synth.cancel();

    const token = ++playToken;

    const utterance =
      new SpeechSynthesisUtterance(questionText);

    const voice = chooseVoice();

    if (voice) {
      utterance.voice = voice;
    }

    utterance.lang = "it-IT";

    // Fixed playback speed: 0.9x Clear
    utterance.rate = 0.9;

    utterance.pitch = 1;
    utterance.volume = 1;

    currentUtterance = utterance;

    utterance.onend = () => {
      if (token !== playToken) return;
      resetButton();
    };

    utterance.onerror = event => {
      if (token !== playToken) return;

      resetButton();

      if (
        event.error !== "canceled" &&
        event.error !== "interrupted"
      ) {
        playButton.textContent = "Audio unavailable";
      }
    };

    synth.speak(utterance);

    playing = true;
    paused = false;
    playButton.textContent = "⏸ Pause";
  }

  function pause() {
    if (!playing) return;

    synth.pause();

    playing = false;
    paused = true;

    playButton.textContent = "▶ Resume";
  }

  playButton.addEventListener("click", () => {

    if (playing) {
      pause();
    } else {
      play();
    }

  });

  // Preserve browser voice initialization.
  synth.getVoices();

  // Stop audio when leaving the page.
  window.addEventListener("pagehide", () => {
    playToken += 1;
    synth.cancel();
  });

})();
</script>
"""

    html_code = html_code.replace(
        "__QUESTION_TEXT__",
        text_json
    )

    components.html(
        html_code,
        height=75,
        scrolling=False
    )
