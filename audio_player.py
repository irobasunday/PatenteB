
"""Italian question speech player for the Patente B Streamlit app."""

import json
import streamlit.components.v1 as components


def show_italian_audio(question_text, question_id):
    """Read only the Italian question, using the browser's available voices."""
    text_json = json.dumps(str(question_text), ensure_ascii=False).replace("<", "\\u003c")

    html_code = r"""
<div class="audio-player">
  <div class="audio-heading">🔊 Ascolta in italiano</div>
  <div class="audio-controls">
    <button id="playButton" type="button">▶ Play</button>
    <label for="speedSelect">Speed</label>
    <select id="speedSelect">
      <option value="0.75">0.75×</option>
      <option value="0.9" selected>0.9× Clear</option>
      <option value="1">1× Normal</option>
      <option value="1.25">1.25×</option>
      <option value="1.5">1.5×</option>
    </select>
  </div>
  <p id="audioStatus" aria-live="polite">Tap Play to hear the Italian question.</p>
</div>
<style>
  body { margin: 0; font-family: system-ui, sans-serif; color: #e5e7eb; }
  .audio-player { background: #151c2d; border: 1px solid #35425b;
    border-radius: 12px; padding: 12px; box-sizing: border-box; }
  .audio-heading { font-size: 14px; font-weight: 650; margin-bottom: 9px; }
  .audio-controls { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  button, select { font: inherit; border-radius: 8px; padding: 8px 12px; }
  button { background: #2563eb; color: white; border: 0; cursor: pointer; }
  button:disabled { opacity: .5; cursor: not-allowed; }
  select { background: #27344a; color: white; border: 1px solid #52627c; }
  label { font-size: 13px; }
  #audioStatus { font-size: 12px; color: #b9c5d6; margin: 9px 0 0; }
</style>
<script>
(() => {
  const questionText = __QUESTION_TEXT__;
  const playButton = document.getElementById('playButton');
  const speedSelect = document.getElementById('speedSelect');
  const statusText = document.getElementById('audioStatus');
  const supported = ('speechSynthesis' in window) &&
                    ('SpeechSynthesisUtterance' in window);
  const synth = supported ? window.speechSynthesis : null;
  let playing = false;
  let currentUtterance = null;
  let playToken = 0;

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
    playButton.textContent = '▶ Play';
  }

  function stop() {
    playToken += 1;
    if (synth) synth.cancel();
    currentUtterance = null;
    resetButton();
    statusText.textContent = 'Playback stopped.';
  }

  function play() {
    if (!supported) return;
    // Start directly in the tap/click handler: mobile browsers require a gesture.
    synth.cancel();
    const token = ++playToken;
    const utterance = new SpeechSynthesisUtterance(questionText);
    const voice = chooseVoice();
    if (voice) utterance.voice = voice;
    utterance.lang = 'it-IT';
    utterance.rate = Number(speedSelect.value);
    utterance.pitch = 1;
    utterance.volume = 1;
    currentUtterance = utterance;
    utterance.onend = () => {
      if (token !== playToken) return;
      resetButton();
      statusText.textContent = 'Playback finished.';
    };
    utterance.onerror = event => {
      if (token !== playToken) return;
      resetButton();
      if (event.error !== 'canceled' && event.error !== 'interrupted') {
        statusText.textContent = 'Speech unavailable. Check your phone’s Italian text-to-speech settings.';
      }
    };
    synth.speak(utterance);
    playing = true;
    playButton.textContent = '■ Stop';
    statusText.textContent = voice
      ? 'Playing: ' + voice.name
      : 'Playing with the device’s Italian speech engine (if available).';
  }

  if (!supported) {
    playButton.disabled = true;
    statusText.textContent = 'This browser does not support speech playback.';
  } else {
    playButton.addEventListener('click', () => playing ? stop() : play());
    speedSelect.addEventListener('change', () => {
      if (playing) play();
    });
    window.addEventListener('pagehide', () => {
      if (playing) stop();
    });
  }
})();
</script>
"""
    html_code = html_code.replace("__QUESTION_TEXT__", text_json)
    components.html(html_code, height=120, scrolling=False)
