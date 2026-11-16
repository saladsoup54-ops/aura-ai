# ukft_voice.py — AURA Voice (V5 I1 speech, V7 F7 speaker)
# ==================================================
# Offline speech, no LLM anywhere.  The WORDS path is unchanged
# since I1 and stays that way (F7 changes nothing said):
#
#   - The Voice lobe tails aura_output.txt (by content hash, so whole-
#     file rewrites are handled) and SPEAKS every new answer — the
#     ambient alerts and presence briefings ride the same channel.
#   - listen_once() runs one dictation pass and writes the recognised
#     text to ui_input.txt, the same file the Architect's keyboard uses
#     — spoken input becomes ordinary input.
#
# V7 F7 is the SPEAKER only: SAPI with a selected voice (AURA_VOICE),
# falling back to the system default voice on any failure — the tail,
# the hash, the text extraction and the dictation path are untouched.
#
# Honestly measured 16 Sept 2026, do not re-try blindly: the WinRT
# OneCore engine (Windows.Media.SpeechSynthesis) LISTS voices fine
# but its SynthesizeTextToStreamAsync never completes on this box
# (all 3 installed voices, MTA and STA) — a platform limitation, not
# a bug in the calling code.  Revisit only with a new voice file:
# a Windows Natural voice pack (Settings → Speech) or a Piper file
# slots into pick_voice()/speak() with no architecture change.
# Cloud neural (Edge read-aloud) was rejected on purpose: phoning
# home every sentence breaks the offline-sovereign story, and its
# websocket protocol + MP3 playback are fragile weight to own.
# ==================================================

import subprocess
import time

from aura_bus import read as bus_read, write as bus_write, append as bus_append
from aura_constants import AURA_VOICE, OUTPUT_FILE, UI_INPUT_FILE

MAX_SPEECH_CHARS = 400   # spoken answers are capped; the console is the full record
LISTEN_SECONDS   = 8     # one dictation pass

_TTS_PS = (
    "Add-Type -AssemblyName System.Speech; "
    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
    "$s.Rate = 1; "
    "$s.Speak([Console]::In.ReadToEnd())"
)

_TTS_PS_VOICE_TEMPLATE = (
    "Add-Type -AssemblyName System.Speech; "
    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
    "$s.Rate = 1; "
    "try {{ $s.SelectVoice('{voice}'); }} catch {{ }}; "
    "$s.Speak([Console]::In.ReadToEnd())"
)

_LISTEN_PS_TEMPLATE = (
    "Add-Type -AssemblyName System.Speech; "
    "$r = New-Object System.Speech.Recognition.SpeechRecognitionEngine; "
    "$r.SetInputToDefaultAudioDevice(); "
    "$g = New-Object System.Speech.Recognition.DictationGrammar; "
    "$r.LoadGrammar($g); "
    "$t = $r.Recognize([TimeSpan]::FromSeconds({seconds})); "
    "if ($t) {{ Write-Output $t.Text }}"
)


def _no_window_flags():
    try:
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    except AttributeError:
        return {}


def speech_text(response):
    """
    What is actually spoken for a response: banners and EXECUTE command
    blocks are stripped — speaking PowerShell to the Architect is noise.
    """
    lines = []
    for line in (response or "").splitlines():
        line = line.strip().replace("[AURA]:", "").strip()
        if not line or line.startswith("EXECUTE:") or line.startswith("---"):
            continue
        lines.append(line)
    text = " ".join(lines).strip()
    if len(text) > MAX_SPEECH_CHARS:
        text = text[:MAX_SPEECH_CHARS].rstrip() + "..."
    return text


def pick_voice(installed, preferred=AURA_VOICE):
    """
    Which SAPI voice speaks: the preferred one by exact name, else
    None (the caller falls back to the system default voice).
    Pure function — the seam a neural engine plugs into later.
    """
    try:
        names = [str(n) for n in (installed or [])]
    except Exception:
        return None
    want = str(preferred or "").strip()
    if want and want in names:
        return want
    return None


def _tts_command(voice=None):
    """PowerShell speech command, voice-selected or default."""
    if voice:
        safe = "".join(c for c in voice if c.isalnum() or c in " -")
        if safe.strip():
            return _TTS_PS_VOICE_TEMPLATE.format(voice=safe.strip())
    return _TTS_PS


def speak(text, timeout=60, voice=AURA_VOICE, runner=None):
    """
    Speak text aloud (offline; failure is silent).  V7 F7 selects
    the configured voice, falling back to the default voice and
    then to silence — the words never change, only the speaker.
    runner injects subprocess.run for tests so no suite makes sound.
    """
    text = (text or "").strip()
    if not text:
        return False
    run = runner or subprocess.run
    try:
        # The script itself falls back to the default voice when the
        # preferred one is missing — no listing round-trip per answer.
        run(
            ["powershell", "-NoProfile", "-Command",
             _tts_command(voice)],
            input=text, capture_output=True, text=True,
            timeout=timeout, **_no_window_flags(),
        )
        return True
    except Exception:
        pass
    try:
        run(
            ["powershell", "-NoProfile", "-Command", _TTS_PS],
            input=text, capture_output=True, text=True,
            timeout=timeout, **_no_window_flags(),
        )
        return True
    except Exception:
        return False


def _recognize_powershell(seconds):
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         _LISTEN_PS_TEMPLATE.format(seconds=int(seconds))],
        capture_output=True, text=True, timeout=seconds + 20,
        **_no_window_flags(),
    )
    return (out.stdout or "").strip()


def listen_once(seconds=LISTEN_SECONDS, recognizer=None):
    """
    One dictation pass; the recognised text is written to ui_input.txt
    so spoken input enters the exact same path as typed input.
    """
    try:
        heard = (recognizer or _recognize_powershell)(seconds)
    except Exception:
        heard = ""
    if heard and heard.strip():
        # Queued: dictation waits its turn behind typed messages instead
        # of overwriting them.
        bus_append(UI_INPUT_FILE, heard.strip())
        print(f"[VOICE] Heard: {heard.strip()}")
        return heard.strip()
    return None


class Voice:
    """Content-hash tail on aura_output.txt: speaks only NEW answers."""

    def __init__(self, output_file=OUTPUT_FILE, speak_fn=None):
        self.output_file = output_file
        self._speak = speak_fn or speak
        self._last = None

    def poll(self):
        content = bus_read(self.output_file)
        if not content.strip() or content == self._last:
            return None
        self._last = content
        text = speech_text(content)
        if text:
            self._speak(text)
            return text
        return None


def run_voice():
    print("--- AURA VOICE: OFFLINE SPEECH ACTIVE ---")
    voice = Voice()
    while True:
        try:
            spoken = voice.poll()
            if spoken:
                print(f"[Voice] Spoke {len(spoken)} chars.")
        except Exception as e:
            print(f"[Voice] Friction: {e}")
        time.sleep(1)


if __name__ == "__main__":
    run_voice()
