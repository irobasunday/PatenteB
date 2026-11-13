
"""Italian question audio for the Patente B Learning Page."""

import json
import streamlit.components.v1 as components


def show_learning_audio(question_text, question_id):
    """Display the Italian Play/Stop audio player."""

    text_json = json.dumps(
        str(question_text),
        ensure_ascii=False
    ).replace("<", "\\u003c").replace(
        "\u2028", "\\u2028"
    ).replace(
        "\u2029", "\\u2029"
    )

    html_code = r"""
<div class="audio-player">

  <div class="audio-heading">
    🔊 Ascolta in italiano
  </div>

  <div class="audio-controls">

    <button id="playButton" type="button">
      ▶ Play
    </button>

    <label for="speedSelect">Speed</label>

    <select id="speedSelect">
      <option value="0.75">0.75×</option>
      <option value="0.9" selected>0.9× Clear</option>
      <option value="1">1× Normal</option>
      <option value="1.25">1.25×</option>
      <option value="1.5">1.5×</option>
    </select>

  </div>

  <p id="audioStatus" aria-live="polite">
    Tap Play to hear the Italian question.
  </p>

</div>

<style>
  * {
    box-sizing: border-box;
  }

  body {
    margin: 0;
    background: transparent;
    font-family: system-ui, sans-serif;
    color: #e5e7eb;
  }

  .audio-player {
    background: #151c2d;
    border: 1px solid #35425b;
    border-radius: 12px;
    padding: 12px;
    width: 100%;
  }

  .audio-heading {
    font-size: 14px;
    font-weight: 650;
    margin-bottom: 9px;
  }

  .audio-controls {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  button {
    background: #2563eb;
    color: white;
    border: 0;
    border-radius: 8px;
    padding: 9px 15px;
    min-height: 40px;
    font: inherit;
    font-size: 14px;
    cursor: pointer;
  }

  button:hover {
    background: #1d4ed8;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  label {
    font-size: 13px;
  }

  select {
    background: #27344a;
    color: white;
    border: 1px solid #52627c;
    border-radius: 8px;
    padding: 9px 12px;
    min-height: 40px;
    font: inherit;
    font-size: 14px;
  }

  #audioStatus {
    font-size: 12px;
    color: #b9c5d6;
    margin: 9px 0 0;
  }
</style>

<script>
(() => {

  const questionText = __QUESTION_TEXT__;

  const playButton =
    document.getElementById("playButton");

  const speedSelect =
    document.getElementById("speedSelect");

  const statusText =
    document.getElementById("audioStatus");

  const supported =
    "speechSynthesis" in window &&
    "SpeechSynthesisUtterance" in window;

  const synth = supported
    ? window.speechSynthesis
    : null;

  let playing = false;
  let playToken = 0;
  let currentUtterance = null;

   function chooseVoice() {
      const voices = synth.getVoices();
      const italian = voices.filter(v => /^it([_-]|$)/i.test(v.lang));
      return italian.find(v => /google italiano/i.test(v.name)) ||
             italian.find(v => /google/i.test(v.name)) ||
             italian.find(v => v.localService) ||
             italian[0] || null;
    }

  function resetButton() {
    playing = false;
    playButton.textContent = "▶ Play";
  }

  function stop() {

    playToken += 1;

    synth.cancel();
    currentUtterance = null;

    resetButton();

    statusText.textContent =
      "Playback stopped.";
  }

  function play() {

    if (!supported) return;

    synth.cancel();

    const token = ++playToken;

    const utterance =
      new SpeechSynthesisUtterance(questionText);

    const voice = chooseVoice();

    if (voice) {
      utterance.voice = voice;
    }

    utterance.lang = "it-IT";
    utterance.rate = Number(speedSelect.value);
    utterance.pitch = 1;
    utterance.volume = 1;

    currentUtterance = utterance;

    utterance.onstart = () => {
      if (token !== playToken) return;

      statusText.textContent = voice
        ? "Playing: " + voice.name
        : "Playing Italian question...";
    };

    utterance.onend = () => {
      if (token !== playToken) return;

      currentUtterance = null;
      resetButton();

      statusText.textContent =
        "Playback finished.";
    };

    utterance.onerror = event => {
      if (token !== playToken) return;

      currentUtterance = null;
      resetButton();

      if (
        event.error !== "canceled" &&
        event.error !== "interrupted"
      ) {
        statusText.textContent =
          "Italian audio unavailable on this device.";
      }
    };

    synth.speak(utterance);

    playing = true;
    playButton.textContent = "■ Stop";

    statusText.textContent =
      "Starting Italian audio...";
  }

  if (!supported) {

    playButton.disabled = true;

    statusText.textContent =
      "Speech playback is not supported in this browser.";

  } else {

    synth.getVoices();

    playButton.addEventListener("click", () => {
      if (playing) {
        stop();
      } else {
        play();
      }
    });

    speedSelect.addEventListener("change", () => {
      if (playing) {
        play();
      }
    });

    window.addEventListener("pagehide", () => {
      if (playing) {
        stop();
      }
    });
  }

})();
</script>
"""

    html_code = html_code.replace(
        "__QUESTION_TEXT__",
        text_json
    )

    components.html(
        html_code,
        height=125,
        scrolling=False
    )
