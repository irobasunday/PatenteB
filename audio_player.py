
import json
import streamlit.components.v1 as components


def show_italian_audio(question_text, question_id):
    """Play Italian quiz questions using Google Italiano only."""

    text_json = json.dumps(
        str(question_text),
        ensure_ascii=False
    ).replace("<", "\\u003c")

    player_id = f"patente_audio_{question_id}"

    html_code = """
    <div class="audio-player">

        <div class="audio-heading">
            <span>🔊</span>
            <span>Ascolta in italiano</span>
        </div>

        <div class="audio-controls">

            <button id="playButton" type="button" disabled>
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
            Loading Google Italiano...
        </p>

    </div>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            background: transparent;
            color: #e5e7eb;
            font-family: Arial, sans-serif;
        }

        .audio-player {
            border: 1px solid #374151;
            border-radius: 12px;
            padding: 14px;
            background: #111827;
        }

        .audio-heading {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 14px;
            font-size: 14px;
            font-weight: 600;
        }

        .audio-controls {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }

        button {
            border: none;
            border-radius: 8px;
            background: #2563eb;
            color: white;
            font-size: 14px;
            font-weight: 600;
            padding: 10px 20px;
            cursor: pointer;
        }

        button:hover:not(:disabled) {
            background: #1d4ed8;
        }

        button:disabled {
            background: #4b5563;
            cursor: not-allowed;
        }

        label {
            color: #9ca3af;
            font-size: 13px;
        }

        select {
            background: #1f2937;
            color: white;
            border: 1px solid #4b5563;
            border-radius: 8px;
            padding: 9px;
            font-size: 13px;
            max-width: 100%;
        }

        #audioStatus {
            font-size: 12px;
            color: #9ca3af;
            margin: 10px 0 0;
            min-height: 16px;
        }
    </style>

    <script>
        const questionText = __QUESTION_TEXT__;
        const playerId = __PLAYER_ID__;

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

        let googleItalianVoice = null;
        let utterance = null;
        let isPlaying = false;
        let playbackId = 0;

        // Find Google Italiano exclusively
        function loadVoices() {

            if (!supported) {
                playButton.disabled = true;

                statusText.textContent =
                    "Speech is not supported by this browser.";

                return;
            }

            const voices = synth.getVoices();

            googleItalianVoice = voices.find(
                voice =>
                    voice.lang.toLowerCase().startsWith("it") &&
                    voice.name.toLowerCase().includes(
                        "google italiano"
                    )
            ) || null;

            if (googleItalianVoice) {

                playButton.disabled = false;

                if (!isPlaying) {
                    statusText.textContent =
                        "Google Italiano ready.";
                }

            } else {

                playButton.disabled = true;

                statusText.textContent =
                    "Google Italiano is not available in this browser.";
            }
        }

        function setStopped() {

            isPlaying = false;

            playButton.textContent = "▶ Play";

            statusText.textContent =
                googleItalianVoice
                    ? "Google Italiano ready."
                    : "Google Italiano unavailable.";
        }

        function stopAudio() {

            playbackId++;

            if (synth) {
                synth.cancel();
            }

            utterance = null;

            setStopped();
        }

        function startAudio() {

            if (!supported) {
                return;
            }

            // Do not use another voice
            if (!googleItalianVoice) {

                statusText.textContent =
                    "Google Italiano is not available.";

                return;
            }

            // Stop any previous playback
            stopAudio();

            const currentPlaybackId = playbackId;

            utterance = new SpeechSynthesisUtterance(
                questionText
            );

            // Google Italiano only
            utterance.voice = googleItalianVoice;

            utterance.lang = "it-IT";

            // Adjustable speaking speed
            utterance.rate = parseFloat(
                speedSelect.value
            );

            utterance.pitch = 1;
            utterance.volume = 1;

            utterance.onend = function() {

                if (currentPlaybackId === playbackId) {
                    setStopped();
                }
            };

            utterance.onerror = function(event) {

                if (currentPlaybackId !== playbackId) {
                    return;
                }

                setStopped();

                if (
                    event.error !== "canceled" &&
                    event.error !== "interrupted"
                ) {
                    statusText.textContent =
                        "Unable to play Google Italiano audio.";
                }
            };

            synth.speak(utterance);

            isPlaying = true;

            playButton.textContent = "■ Stop";

            statusText.textContent =
                "Playing with Google Italiano...";
        }

        // Single Play/Stop button
        playButton.addEventListener(
            "click",
            function() {

                if (isPlaying) {
                    stopAudio();
                } else {
                    startAudio();
                }
            }
        );

        // Restart speech when speed changes
        speedSelect.addEventListener(
            "change",
            function() {

                if (isPlaying) {
                    startAudio();
                }
            }
        );

        // Load available browser voices
        if (supported) {

            loadVoices();

            if ("onvoiceschanged" in synth) {

                synth.addEventListener(
                    "voiceschanged",
                    loadVoices
                );
            }

        } else {
            loadVoices();
        }

        // Stop audio when the page closes
        window.addEventListener(
            "pagehide",
            stopAudio
        );

    </script>
    """

    html_code = html_code.replace(
        "__QUESTION_TEXT__",
        text_json
    ).replace(
        "__PLAYER_ID__",
        json.dumps(player_id)
    )

    components.html(
        html_code,
        height=145,
        scrolling=False
    )
