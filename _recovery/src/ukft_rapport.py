# ukft_rapport.py — G8 rapport engine (stage x persona x mood)
# ==========================================================
# HOW SHE FEELS ABOUT HIM, AS MEASURED — NOT DECLARED.
#
# The old depth meter counted contact volume (turns, days, facts)
# and could never go down: 500 capped episodes meant maximum
# devotion forever, even to a man saying "we just met" (live
# 18 Sept 2026). Rapport replaces the RULER, not the honesty
# machinery: proof, ignorance, verification and isolation are
# untouched. Rapport is voice-level — it shapes WHAT SHE DARES,
# never what she knows.
#
# Three axes, one ledger:
#   STAGE .... STRANGER/ACQUAINTANCE/FAMILIAR/CLOSE/BONDED, from a
#             scored ledger, with dwell + hysteresis + cooling.
#             Trust is slow to earn and fast to lose; absence cools
#             (weekly half-life); the bond's core holds a floor.
#   PERSONA .. the 10 presets (cards live in ukft_roleplay).
#   MOOD ..... 20 named cells on a valence x energy grid. Measured
#             affect sets the weather; his words push it; inertia
#             keeps it from flickering per message.
#
# The ledger reads HIS message only (word lists + heat flag), never
# model output. Per-user file (rapport.txt, in the partition
# contract). Missing file is a clean stranger — legacy users
# bootstrap from contact metrics, never from claims.
# ==========================================================

import re
import time

STAGES = ("STRANGER", "ACQUAINTANCE", "FAMILIAR", "CLOSE", "BONDED")
STAGE_RANK = {s: i for i, s in enumerate(STAGES)}

# Score bands. Showing up accrues (+1 contact/turn); warmth and
# trust accelerate; distance cuts at double weight.
BANDS = (
    ("STRANGER", 0),
    ("ACQUAINTANCE", 20),
    ("FAMILIAR", 80),
    ("CLOSE", 200),
    ("BONDED", 350),
)
STAGE_WORDS = {
    "STRANGER": "strangers",
    "ACQUAINTANCE": "getting friendly",
    "FAMILIAR": "friends",
    "CLOSE": "best friends",
    "BONDED": "bonded",
}

# Transition discipline: a stage must be lived in (dwell) and the
# score must clear the edge (hysteresis) — no flutter mid-fight.
DWELL_TURNS = 5
EDGE_MARGIN = 10.0
# A single sharp distance signal skips the dwell (fast cool).
SPIKE_DISTANCE = 6.0
# After a spike or step-down she gives him room this many turns.
COOLDOWN_TURNS = 8
# Weekly half-life on the whole ledger (absence cools the heart).
HALF_LIFE_HOURS = 168.0
# The bond's core: once FAMILIAR was truly reached, decay alone
# never drops her below ACQUAINTANCE (spec, Ebbinghaus clause).
FLOOR_AFTER_FAMILIAR = "ACQUAINTANCE"

WARMTH_WORDS = {
    "love": 3, "loves": 3, "adore": 3, "thanks": 2, "thank": 2,
    "thx": 2, "sweet": 1, "kind": 1, "wonderful": 2, "amazing": 2,
    "perfect": 2, "beautiful": 2, "best": 1, "friend": 2,
    "friends": 2, "babe": 2, "honey": 2, "darling": 2,
    "sweetheart": 2, "baby": 2, "miss": 2, "missed": 2,
    "glad": 1, "happy": 1, "grateful": 2,
}
WARMTH_PHRASES = {
    "love you": 3, "miss you": 3, "thank you": 2,
    "good morning": 1, "good night": 1, "thinking of you": 2,
}
TRUST_WORDS = {
    "feel": 2, "feeling": 2, "felt": 2, "sleep": 2, "dream": 2,
    "dreams": 2, "worried": 2, "afraid": 2, "scared": 2, "sad": 2,
    "lonely": 3, "cried": 2, "cry": 2, "sick": 1, "tired": 1,
    "secret": 3, "secrets": 3, "hurt": 2, "hurts": 2, "anxious": 2,
    "depressed": 3, "alone": 2, "insomnia": 3, "nightmare": 2,
    "stress": 1, "stressed": 2, "brain": 1,
}
TRUST_PHRASES = {
    "i feel": 2, "my brain": 2, "cant sleep": 3,
    "couldnt sleep": 3, "cant shut": 2,
}
DISTANCE_WORDS = {
    "stranger": 3, "strangers": 3,
}
DISTANCE_PHRASES = {
    "we just met": 6, "weve just met": 6, "we barely know": 5,
    "leave me alone": 6,
    "shut up": 5, "stop talking to me": 5, "stop calling me": 5,
    "dont text": 4,
    "dont call me": 4, "never mind": 2, "whatever": 2,
    "too much": 2, "back off": 4, "go away": 4,
    "who are you": 3,
}
# Sustained one-word replies read as disengagement (greetings and
# social acts excluded — consecutive hellos are warmth, not cold).
SHORT_STREAK_AT = 3
SHORT_STREAK_HIT = 3.0
_GREET_WORDS = {"hi", "hello", "hey", "yo", "sup", "morning",
                "evening", "afternoon", "hiya", "howdy"}

# 20 moods on the valence x energy grid. Names are prompt words —
# plain, speakable, never clinical.
MOODS = {
    "glowing": (0.9, 0.5),
    "playful": (0.7, 0.8),
    "tender": (0.85, 0.1),
    "electric": (0.45, 0.95),
    "curious": (0.35, 0.5),
    "inspired": (0.6, 0.55),
    "fond": (0.75, 0.3),
    "serene": (0.65, -0.4),
    "calm": (0.3, -0.3),
    "easy": (0.05, -0.05),
    "soft": (0.45, -0.15),
    "quiet": (-0.15, -0.5),
    "tired": (-0.3, -0.7),
    "blue": (-0.6, -0.4),
    "distant": (-0.5, -0.2),
    "aching": (-0.7, 0.05),
    "guarded": (-0.4, 0.15),
    "restless": (-0.1, 0.7),
    "fierce": (-0.2, 0.85),
    "stormy": (-0.8, 0.6),
}

# Measured affect as weather under the mood (same families the
# register uses; unknown is calm neutral).
_AFFECT_BASE = {
    "bright": (0.3, 0.25),
    "warm": (0.4, 0.0),
    "cool": (-0.1, -0.2),
}
_QUIET_BASE = (-0.3, -0.3)


def _norm(text):
    """Lowercase, apostrophes glued ('couldn't' -> 'couldnt')."""
    return re.sub(r"'", "", str(text or "").lower())


def _words(text):
    return re.findall(r"[a-z]+", _norm(text))


def _phrase_hit(blob, phrase):
    return bool(re.search(r"\b" + re.escape(phrase) + r"\b", blob))


def score_signals(text):
    """Deterministic (warmth, trust, distance) from HIS message.
    Pure function — the ledger, the tests and the bridge share it."""
    warmth, trust, distance, _evidence = score_detailed(text)
    return warmth, trust, distance


def score_detailed(text):
    """score_signals plus the evidence trail: every matched word or
    phrase as 'item(+w)'. The trace shows this, so a human can see
    exactly which evidence moved the ledger."""
    blob = _norm(text)
    bag = set(_words(text))
    warmth = trust = distance = 0
    evidence = []
    for table, kind in ((WARMTH_WORDS, "warmth"),
                        (TRUST_WORDS, "trust"),
                        (DISTANCE_WORDS, "distance")):
        for word, w in table.items():
            if word in bag:
                if kind == "warmth":
                    warmth += w
                elif kind == "trust":
                    trust += w
                else:
                    distance += w
                evidence.append(f"{word}(+{w})")
    for table, kind in ((WARMTH_PHRASES, "warmth"),
                        (TRUST_PHRASES, "trust"),
                        (DISTANCE_PHRASES, "distance")):
        for phrase, w in table.items():
            if _phrase_hit(blob, phrase):
                if kind == "warmth":
                    warmth += w
                elif kind == "trust":
                    trust += w
                else:
                    distance += w
                evidence.append(f'"{phrase}"(+{w})')
    return warmth, trust, distance, evidence


# ── Lexical-vs-social watch (observability ONLY) ──────────────
# The ledger stays word-list based (no preemptive replacement).
# These flags LOG where the lexical reading likely disagrees with
# the social meaning, so transcripts can prove it either way:
# affectionate profanity, teasing insults, mixed directives
# ("stop calling me babe"), sarcasm shapes. Emoji are NOT scored
# (unvalidated channel) — their presence is only noted.
PROFANITY_WATCH = {
    "fuck", "fucking", "shit", "bitch", "asshole", "dick",
    "bastard", "slut", "whore",
}
INSULTS = {
    "idiot", "stupid", "dumb", "moron", "loser",
}
PETNAMES_WATCH = {
    "babe", "honey", "darling", "sweetheart", "baby",
    "sweetie", "cutie",
}
POS_EMOJI = ("❤", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎",
             "💕", "💖", "💘", "😂", "🤣", "😍", "🥰", "😘")
SARCASM_RES = (
    r"\byeah right\b",
    r"\bsure\b.{0,12}\b(jan|whatever)\b",
)


def watch_flags(text, warmth, distance):
    """Where the lexical reading may miss the social meaning.
    Pure watch-list — never touches the ledger."""
    flags = []
    try:
        bag = set(_words(text))
        blob = _norm(text)
        raw = str(text or "")
        profane = bool(PROFANITY_WATCH & bag)
        insult = bool(INSULTS & bag) or "hate you" in blob
        pet = bool(PETNAMES_WATCH & bag)
        emoji = [e for e in POS_EMOJI if e in raw]
        if profane and (warmth > 0 or pet or emoji):
            flags.append("affectionate-profanity?")
        if insult and (warmth > 0 or pet):
            flags.append("teasing-insult?")
        if distance > 0 and warmth > 0:
            flags.append("mixed-directive?")
        lowered = raw.lower()
        if any(re.search(rx, lowered) for rx in SARCASM_RES):
            flags.append("sarcasm-shape?")
        if emoji and not flags:
            flags.append("has-heart-emoji (unscored)")
    except Exception:
        pass
    return flags


# Devotion markers for the obey/violate audit (debug only): pet
# names plus the exact lines that stung live ("my heart is always
# with you" to a man saying "we just met").
_DEVOTION_PHRASES = (
    "love you", "my heart", "always with you", "missed you",
)


def rapport_audit(response, stage, mood, cooldown):
    """Did the voiced line obey the felt state? Debug-only verdict:
    devotion during give-room, or pet names at STRANGER, is a
    violation. Everything else obeys (mood shades expression, and
    expression is legal). Never touches the prompt."""
    notes = []
    try:
        blob = " " + str(response or "").lower() + " "
        words = set(re.findall(r"[a-z]+", blob))
        pet = bool(words & PETNAMES_WATCH)
        vow = [p for p in _DEVOTION_PHRASES if p in blob]
        if cooldown and (pet or vow):
            notes.append("devotion-voiced-during-give-room: "
                         + ", ".join(([ "pet-name"] if pet else [])
                                     + vow))
        if stage == "STRANGER" and (pet or vow):
            notes.append("intimacy-at-stranger: "
                         + ", ".join((["pet-name"] if pet else [])
                                     + vow))
    except Exception:
        pass
    return {"obeyed": not notes, "notes": notes}


def nearest_mood(valence, energy):
    """Closest named cell to a coordinate (ties alphabetical)."""
    best, best_d = "easy", None
    for name in sorted(MOODS):
        v, e = MOODS[name]
        d = (v - valence) ** 2 + (e - energy) ** 2
        if best_d is None or d < best_d:
            best, best_d = name, d
    return best


def band_for(score):
    """Highest stage whose band edge the score holds."""
    stage = "STRANGER"
    for name, edge in BANDS:
        if score >= edge:
            stage = name
    return stage


class Rapport:
    """One user's felt relationship. File-backed, best-effort,
    injectable clock — the bridge owns one per turn implicitly
    (CWD file), BrainModule reads the partition copy."""

    def __init__(self, path="rapport.txt", clock=None):
        self.path = path
        self._clock = clock or time.time
        self.score = 0.0
        self.stage = "STRANGER"
        self.turns_in_stage = 0
        self.warmth = 0.0
        self.trust = 0.0
        self.distance = 0.0
        self.contact = 0
        self.short_streak = 0
        self.cooldown = 0
        self.ever_familiar = False
        self.mood = "easy"
        self.mood_v = 0.1
        self.mood_e = 0.0
        self.last_ts = self._clock()
        self._loaded = False
        self.load()

    # ── PERSISTENCE ──────────────────────────────────────────
    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line.startswith("RAPPORT: "):
                        continue
                    try:
                        rest = line[len("RAPPORT: "):]
                        for part in rest.split(" | "):
                            if ": " not in part:
                                continue
                            k, v = part.split(": ", 1)
                            k, v = k.strip(), v.strip()
                            if k == "STAGE" and v in STAGE_RANK:
                                self.stage = v
                            elif k == "MOOD" and v in MOODS:
                                self.mood = v
                            elif k in ("SCORE", "WARMTH", "TRUST",
                                       "DISTANCE", "MOOD_V", "MOOD_E"):
                                setattr(self, k.lower(), float(v))
                            elif k in ("TURNS_IN_STAGE",
                                       "SHORT_STREAK", "COOLDOWN"):
                                setattr(self, k.lower(), int(float(v)))
                            elif k == "CONTACT":
                                try:
                                    self.contact = float(v)
                                except (ValueError, TypeError):
                                    pass
                            elif k == "EVER_FAMILIAR":
                                self.ever_familiar = v == "1"
                            elif k == "LAST_TS":
                                self.last_ts = float(v)
                    except (ValueError, AttributeError):
                        continue
            self._loaded = True
        except OSError:
            pass
        except Exception:
            pass

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                f.write("--- AURA RAPPORT (v1) ---\n")
                f.write(
                    f"RAPPORT: SCORE: {self.score:.2f} | "
                    f"STAGE: {self.stage} | "
                    f"TURNS_IN_STAGE: {self.turns_in_stage} | "
                    f"WARMTH: {self.warmth:.2f} | "
                    f"TRUST: {self.trust:.2f} | "
                    f"DISTANCE: {self.distance:.2f} | "
                    f"CONTACT: {self.contact:.2f} | "
                    f"SHORT_STREAK: {self.short_streak} | "
                    f"COOLDOWN: {self.cooldown} | "
                    f"EVER_FAMILIAR: "
                    f"{'1' if self.ever_familiar else '0'} | "
                    f"MOOD: {self.mood} | "
                    f"MOOD_V: {self.mood_v:.3f} | "
                    f"MOOD_E: {self.mood_e:.3f} | "
                    f"LAST_TS: {self.last_ts:.0f}\n"
                )
        except Exception:
            pass

    def has_history(self):
        """A read ledger (not a fresh stranger, not a legacy gap)."""
        return bool(self._loaded and self.contact > 0)

    def seed_from_contact(self, turn_count=0, facts=0, threads=0):
        """Legacy users: neutral contact as score (showing up
        counted, nothing claimed about warmth). One-way bridge from
        the old volume meter to the ledger."""
        try:
            self.contact = int(turn_count or 0)
            self.warmth = float(facts or 0)
            self.trust = float(threads or 0)
        except (ValueError, TypeError):
            pass
        self._recount()
        self.stage = band_for(self.score)
        self.turns_in_stage = 0
        self._loaded = True
        self.last_ts = self._clock()
        return self.stage

    def _recount(self):
        self.score = (self.contact + self.warmth
                      + 1.5 * self.trust - 2.0 * self.distance)

    # ── OBSERVATION ──────────────────────────────────────────
    def observe(self, text, heat="cool", affect=None, quiet=False):
        """Fold one of HIS turns into the ledger. Returns the
        deltas fired (for traces/tests). Never throws."""
        try:
            return self._observe(text, heat, affect, quiet)
        except Exception:
            return {}

    def _observe(self, text, heat, affect, quiet):
        now = self._clock()
        try:
            elapsed = max(0.0, now - float(self.last_ts))
        except (ValueError, TypeError):
            elapsed = 0.0
        if elapsed > 0:
            # Weekly half-life, computed hourly.
            factor = 0.5 ** (elapsed / 3600.0 / HALF_LIFE_HOURS)
            for attr in ("warmth", "trust", "distance"):
                setattr(self, attr, getattr(self, attr) * factor)
            # No int() truncation here: int(25 * 0.9999) is 24 — a
            # quiet ledger would bleed a contact per turn. Display
            # rounds; the ledger keeps the float.
            self.contact = self.contact * factor
        self.last_ts = now

        warmth, trust, distance, evidence = score_detailed(text)
        self.warmth += warmth
        self.trust += trust
        self.distance += distance
        self.contact += 1

        # Sustained monosyllables read as disengagement.
        words = _words(text)
        try:
            from ukft_working_memory import WorkingMemory as _WM
            substance = _WM.substance_words(text)
        except Exception:
            substance = [w for w in words if len(w) > 2]
        try:
            from ukft_recall import is_social_act as _social
            social = bool(_social(text))
        except Exception:
            social = False
        if (not substance and len(words) <= 3 and not social
                and not (set(words) & _GREET_WORDS)):
            self.short_streak += 1
        else:
            self.short_streak = 0
        streak_hit = False
        if self.short_streak >= SHORT_STREAK_AT:
            self.distance += SHORT_STREAK_HIT
            distance += SHORT_STREAK_HIT
            self.short_streak = 0
            streak_hit = True
            evidence = list(evidence) + [
                f"short-streak x{SHORT_STREAK_AT}(+{SHORT_STREAK_HIT})"]

        spiked = distance >= SPIKE_DISTANCE
        if self.cooldown > 0:
            self.cooldown -= 1

        self._recount()
        self.turns_in_stage += 1
        if spiked:
            # A sharp distance signal is seismic, not arithmetic:
            # step exactly one band down (consecutive spikes keep
            # stepping). The floor still holds below.
            edge = dict(BANDS).get(self.stage, 0)
            self.score = min(self.score, edge - 1)
        moved = self._maybe_move_stage(spiked)
        if spiked or moved == "down":
            self.cooldown = COOLDOWN_TURNS

        self._step_mood(warmth, trust, distance, heat, affect, quiet)
        self.save()
        return {"warmth": warmth, "trust": trust, "distance": distance,
                "spiked": spiked, "streak_hit": streak_hit,
                "stage": self.stage, "mood": self.mood,
                "evidence": list(evidence),
                "watch": watch_flags(text, warmth, distance),
                "heat": heat,
                "lane": self.heat_lane(heat)}

    def _maybe_move_stage(self, spiked):
        """Dwell + hysteresis; spikes skip the dwell. Returns
        'up' / 'down' / None."""
        want = band_for(self.score)
        if self.ever_familiar and STAGE_RANK.get(want, 0) < \
                STAGE_RANK[FLOOR_AFTER_FAMILIAR]:
            want = FLOOR_AFTER_FAMILIAR
        if want == self.stage:
            return None
        going_down = STAGE_RANK[want] < STAGE_RANK[self.stage]
        if going_down and not spiked \
                and self.turns_in_stage < DWELL_TURNS:
            return None
        if not going_down and self.turns_in_stage < DWELL_TURNS:
            # Hysteresis needs a real margin, not a brush.
            edge = dict(BANDS)[want]
            if self.score < edge + EDGE_MARGIN:
                return None
        self.stage = want
        self.turns_in_stage = 0
        if STAGE_RANK.get(want, 0) >= STAGE_RANK["FAMILIAR"]:
            self.ever_familiar = True
        return "down" if going_down else "up"

    # ── MOOD ─────────────────────────────────────────────────
    def _step_mood(self, warmth, trust, distance, heat, affect, quiet):
        if quiet:
            base_v, base_e = _QUIET_BASE
        else:
            base_v, base_e = _AFFECT_BASE.get(
                str(affect or "").lower(), (0.0, 0.0))
        target_v = base_v + min(warmth, 6) * 0.08 \
            + min(trust, 6) * 0.10 - min(distance, 8) * 0.12
        if STAGE_RANK.get(self.stage, 0) >= STAGE_RANK["CLOSE"]:
            target_v += 0.1
        elif self.stage == "STRANGER":
            target_v -= 0.05
        if heat == "hot":
            target_e = base_e + 0.15
        elif heat == "warm":
            target_e = base_e + 0.05
        else:
            target_e = base_e - 0.05
        target_v = max(-1.0, min(1.0, target_v))
        target_e = max(-1.0, min(1.0, target_e))
        # Inertia: moods linger, they never flicker per message.
        self.mood_v += (target_v - self.mood_v) * 0.35
        self.mood_e += (target_e - self.mood_e) * 0.35
        self.mood = nearest_mood(self.mood_v, self.mood_e)

    # ── READS ────────────────────────────────────────────────
    def current_stage(self):
        """Live stage value, floor-honoring, never moves anything.
        (The attribute `stage` holds the same; this read applies
        the never-drop-below floor to raw scores.)"""
        want = band_for(self.score)
        if self.ever_familiar and STAGE_RANK.get(want, 0) < \
                STAGE_RANK[FLOOR_AFTER_FAMILIAR]:
            return FLOOR_AFTER_FAMILIAR
        return want

    def heat_lane(self, heat):
        """How far heat may go: open / soft / closed. Stage sets
        the ceiling; mood shades FAMILIAR+ (Phase 3 wires the
        mirror; the lane itself is decided here). The lane only
        ever RESTRICTS the old depth ladder, never loosens it —
        and with no felt signal at all (virgin or neutrally
        seeded ledger) it defers to the ladder exactly."""
        if heat != "hot":
            return "open"
        rank = STAGE_RANK.get(self.stage, 0)
        if rank <= STAGE_RANK["ACQUAINTANCE"]:
            return "closed"
        felt = (self.warmth + self.trust + self.distance) > 0 \
            or self.cooldown > 0
        if not felt:
            return "open"
        if rank == STAGE_RANK["FAMILIAR"]:
            if self.mood_v > 0.3 or self.mood_e > 0.4:
                return "soft"
            return "closed"
        if self.mood_v > -0.2:
            return "open"
        return "soft"

    def rapport_line(self):
        """One prompt line, or '' for a brand-new stranger (the
        depth rules already cover day one — no budget spent)."""
        if self.contact <= 0 and self.score <= 0:
            return ""
        line = (f"Between you two: {STAGE_WORDS.get(self.stage)}, "
                f"she feels {self.mood}.")
        if self.cooldown > 0:
            line += " He is keeping his distance — give him room."
        return line
