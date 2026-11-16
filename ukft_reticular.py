# ukft_reticular.py — AURA Reticular Formation (Phase 2-E)
# ==========================================================
# The reticular formation is the arousal / attention gate.  It ranks
# every sensory record by SOURCE salience before the Thalamus is allowed
# to stimulate the field, so the Architect's voice always dominates
# background intake (Wikipedia, web feeds, PDF drip).
#
#   ARCHITECT  -> full gain, bypasses the D-resonance gate
#   FEEDBACK   -> internal system telemetry, near-full gain
#   PDF        -> deliberate spaced repetition, attenuated
#   WIKI / WEB -> ambient intake, most attenuated
#
# When the Architect speaks, a foreground window opens.  While it is
# open, background sources are attenuated by an extra factor so the
# Architect's concepts win the competition for activation.  The window
# is state, not a file — the Thalamus is the sole consumer of the
# sensory buffer, so the gate lives in that one thread.
# ==========================================================

import time

from aura_constants import (RETICULAR_ARCHITECT_GAIN,
                            RETICULAR_FEEDBACK_GAIN,
                            RETICULAR_PDF_GAIN,
                            RETICULAR_BACKGROUND_GAIN,
                            RETICULAR_FOREGROUND_ATTENUATION,
                            RETICULAR_FOREGROUND_WINDOW)

ARCHITECT = "ARCHITECT"
FEEDBACK  = "FEEDBACK"
PDF       = "PDF"
WIKI      = "WIKI"
WEB       = "WEB"
UNKNOWN   = "UNKNOWN"

SOURCE_GAINS = {
    ARCHITECT: RETICULAR_ARCHITECT_GAIN,
    FEEDBACK:  RETICULAR_FEEDBACK_GAIN,
    PDF:       RETICULAR_PDF_GAIN,
    WIKI:      RETICULAR_BACKGROUND_GAIN,
    WEB:       RETICULAR_BACKGROUND_GAIN,
    UNKNOWN:   RETICULAR_BACKGROUND_GAIN,
}

# Sources that never suffer foreground attenuation.
FOREGROUND_EXEMPT = (ARCHITECT, FEEDBACK)


def classify_source(record):
    """Map a raw sensory record onto its source label."""
    if "ARCHITECT_STIMULUS" in record:
        return ARCHITECT
    if "SYSTEM_FEEDBACK" in record:
        return FEEDBACK
    if "PDF_RESONANCE" in record:
        return PDF
    if "WIKI_RESONANCE" in record:
        return WIKI
    if "WEB_RESONANCE" in record:
        return WEB
    return UNKNOWN


class ReticularFormation:
    """
    Source-salience gate used by the Thalamus before field stimulation.
    `clock` is injectable so the foreground window is testable without
    sleeping.
    """

    def __init__(self, foreground_window=RETICULAR_FOREGROUND_WINDOW,
                 clock=time.time):
        self.foreground_window = foreground_window
        self._clock            = clock
        self._last_architect   = None

    def notify_architect(self, now=None):
        """Open (or extend) the Architect foreground window."""
        self._last_architect = self._clock() if now is None else now

    def in_foreground(self, now=None):
        """True while the Architect's recent input still holds priority."""
        if self._last_architect is None:
            return False
        now = self._clock() if now is None else now
        return (now - self._last_architect) < self.foreground_window

    def gain_for(self, source, now=None):
        """Stimulation multiplier for a source at this moment."""
        gain = SOURCE_GAINS.get(source, RETICULAR_BACKGROUND_GAIN)
        if source in FOREGROUND_EXEMPT:
            return gain
        if self.in_foreground(now):
            return gain * RETICULAR_FOREGROUND_ATTENUATION
        return gain

    def filter(self, records, now=None):
        """
        Classify a batch of raw records.
        Returns [(record, source, gain), ...] with blank records dropped.
        An Architect record opens the foreground window for the records
        that follow it in the same batch.
        """
        now = self._clock() if now is None else now
        gated = []
        for record in records:
            if not record.strip():
                continue
            source = classify_source(record)
            if source == ARCHITECT:
                self.notify_architect(now)
            gated.append((record, source, self.gain_for(source, now)))
        return gated
