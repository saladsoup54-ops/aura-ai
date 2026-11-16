import os
import re
import time
from aura_constants import (D_INVARIANT as UKFT_CONSTANT, SENSORY_BUFFER,
                            CORTEX_INBOX, HYPO_SIGNAL_FILE, PFC_SIGNAL_FILE)
from aura_bus import (append as bus_append, drain as bus_drain,
                      read as bus_read)
from aura_field import FIELD
from ukft_reticular import ReticularFormation, ARCHITECT, FEEDBACK
from ukft_sleep import is_asleep

SYSTEM_NOISE = {
    "anchor", "data", "source", "wiki", "matty", "direct",
    "status", "locked", "pattern", "resonance", "tension",
    "judgement", "signal", "stable", "discordant", "cortex",
    "stimulus", "feedback", "architect", "system", "aura",
    "matty_direct", "wiki_resonance", "directed_wiki_resonance",
    "with", "from", "that", "this", "have", "been", "were",
    "they", "their", "which", "about", "into", "also", "other",
    "than", "more", "some", "such", "when", "where", "what"
}


def read_signal(filepath):
    return bus_read(filepath).strip()


def forward_to_cortex(raw_signals):
    """
    Phase 0.5: the Thalamus is the SOLE consumer of sensory_buffer.txt.
    Every record it consumes is forwarded verbatim to cortex_inbox.txt so
    the Cortex can assimilate it into the vault without racing this thread
    for the same buffer (the old read/truncate race destroyed input).
    Phase 5-A: both files flow through the message bus.
    """
    for signal in raw_signals:
        if signal.strip():
            bus_append(CORTEX_INBOX, signal.rstrip("\n"))


def extract_keywords(signal):
    words = []
    for word in signal.split():
        clean = word.strip().lower().rstrip(":|,.()?!")
        # Split hyphen/underscore compounds first: "dark-matter" used
        # to be dropped whole by isalpha instead of yielding its parts.
        for part in re.split(r"[-_]+", clean):
            if len(part) >= 5 and part not in SYSTEM_NOISE and part.isalpha():
                words.append(part)
    return words


def process_records(raw_signals, field=FIELD, rf=None):
    """
    Phase 2-E: the reticular formation classifies each record and scales
    its stimulation by source salience.  The Architect always passes at
    full gain and opens a foreground window; background intake (Wikipedia,
    web, PDF) is attenuated, and heavily attenuated while the Architect
    holds the foreground.  Returns the number of records stimulated.

    `field` and `rf` are injectable so the gate can be verified without
    booting the organism.
    """
    if rf is None:
        rf = ReticularFormation()

    stimulated = 0
    for signal, source, gain in rf.filter(raw_signals):
        is_architect = source == ARCHITECT
        is_feedback  = source == FEEDBACK

        clean_signal = signal
        if is_architect:
            try:
                clean_signal = signal.split("ARCHITECT_STIMULUS:")[1].split("|")[0].strip()
            except IndexError:
                clean_signal = signal
        elif is_feedback:
            try:
                clean_signal = signal.split("SYSTEM_FEEDBACK:")[1].strip()
            except IndexError:
                clean_signal = signal

        signal_weight = (len(signal) % 1000) / 10000
        discordance   = abs(UKFT_CONSTANT - signal_weight)

        # Architect and internal feedback bypass the D-resonance gate;
        # ambient sources must resonate with D to be admitted at all.
        if is_architect or is_feedback or discordance < 0.05:
            if is_architect:
                # Hearing is the moment of consumption, not the vault
                # crystallisation that happens ~30s later in the cortex.
                print(f"[AURA_HEARING]: Architect -> '{clean_signal}'")

            words = extract_keywords(clean_signal)

            for w in words:
                field.stimulate(w, strength=gain)
            for i in range(len(words) - 1):
                field.connect(words[i], words[i+1], weight=0.2 * gain)

            stimulated += 1
            print(f"[Thalamus] {source}: {words} (gain {gain:.2f})")

    return stimulated


def run_thalamus():
    print("--- AURA THALAMUS: SENSORY FILTER ACTIVE ---")
    rf = ReticularFormation()
    while True:
        if os.path.exists(SENSORY_BUFFER):
            try:
                raw_signals = bus_drain(SENSORY_BUFFER)

                # The cortex ALWAYS receives what arrived — judging is
                # not stimulation.  Parking the drain while inhibited
                # grew the buffer without bound and released it as one
                # burst; asleep or tense, records still digest.
                forward_to_cortex(raw_signals)

                # Stimulation is the gated part: none while asleep, and
                # none while homeostasis or the PFC say hold.
                if is_asleep():
                    time.sleep(1)
                    continue
                hypo = read_signal(HYPO_SIGNAL_FILE)
                pfc = read_signal(PFC_SIGNAL_FILE)
                if "INHIBIT" in hypo or "THROTTLE" in pfc:
                    time.sleep(1)
                    continue

                # Phase 2-E: reticular formation scales each record's
                # stimulation by source salience before it reaches the field.
                process_records(raw_signals, FIELD, rf)

            except Exception as e:
                print(f"[Thalamus Friction]: {e}")

        time.sleep(0.5)


if __name__ == "__main__":
    run_thalamus()
