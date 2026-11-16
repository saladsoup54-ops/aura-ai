# ukft_presence.py — AURA Presence (V5 I4)
# ==================================================
# Boot-resume briefings: the rhythm of a resident, not a process.
# On boot she tells the Architect what happened while she was away —
# vault growth, episodic events, discoveries, fading memories, and
# consolidated sleeps — through the same output channel the Voice lobe
# speaks.
# ==================================================

import time

from aura_bus import read as bus_read, write as bus_write
from aura_constants import OUTPUT_FILE


def _count_lines_matching(path, marker):
    try:
        return sum(1 for line in bus_read(path).splitlines()
                   if marker in line)
    except Exception:
        return 0


def gather():
    """Collect the presence numbers from live state files."""
    try:
        from aura_vault_io import iter_anchors
        vault = sum(1 for _ in iter_anchors())
    except Exception:
        vault = 0
    try:
        from ukft_episodic import EpisodicMemory
        episodes = EpisodicMemory().count()
    except Exception:
        episodes = 0
    try:
        discoveries = _count_lines_matching("discoveries.txt", "DISCOVERY:")
    except Exception:
        discoveries = 0
    forgotten = _count_lines_matching("forgotten_memories.txt",
                                      "FORGOT EPISODE:")
    consolidations = _count_lines_matching("sleep_log.txt", "CONSOLIDATED:")
    gaps = _count_lines_matching("knowledge_gaps.txt", "GAP: ")
    try:
        # V6 C3: she greets the Architect as someone she knows —
        # "" while there is still nothing worth announcing.
        from ukft_people import PeopleModel, architect_summary
        _pm = PeopleModel()
        _arch = _pm.ensure_architect()
        _others = len([k for k in _pm.people if k != "architect"])
        architect = architect_summary(_arch, _others)
    except Exception:
        architect = ""
    try:
        # V6 C6: open threads surface proactively, unasked.
        from ukft_agenda import AgendaModel
        _held = AgendaModel().opened()
        threads = len(_held)
        oldest_thread = _held[0]["topic"] if _held else ""
    except Exception:
        threads, oldest_thread = 0, ""
    return {"vault": vault, "episodes": episodes,
            "discoveries": discoveries, "forgotten": forgotten,
            "consolidations": consolidations, "gaps": gaps,
            "architect": architect, "threads": threads,
            "oldest_thread": oldest_thread}


def build_briefing(stats=None, hour=None):
    """
    Compose the boot briefing from stats (injected for tests).
    hour injects the current hour for the greeting (tests).
    """
    stats = stats or gather()
    if hour is None:
        hour = time.localtime().tm_hour
    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 18:
        greeting = "Good afternoon"
    elif 18 <= hour < 24:
        greeting = "Good evening"
    else:
        greeting = "Up late"

    notes = []
    if stats["vault"]:
        notes.append(f"the vault holds {stats['vault']} memories")
    if stats["episodes"]:
        word = "episodic event" if stats["episodes"] == 1 else "episodic events"
        notes.append(f"{stats['episodes']} {word}")
    if stats["discoveries"]:
        word = "discovery" if stats["discoveries"] == 1 else "discoveries"
        notes.append(f"{stats['discoveries']} {word}")
    if stats["forgotten"]:
        word = "memory has" if stats["forgotten"] == 1 else "memories have"
        notes.append(f"{stats['forgotten']} {word} faded")
    if stats["consolidations"]:
        word = "consolidation" if stats["consolidations"] == 1 else "consolidations"
        notes.append(f"{stats['consolidations']} {word} while asleep")
    if stats["gaps"]:
        word = "knowledge gap awaiting" if stats["gaps"] == 1 \
            else "knowledge gaps awaiting"
        notes.append(f"{stats['gaps']} {word} attention")
    if stats.get("architect"):
        notes.append(f"I remember you, {stats['architect']}")
    if stats.get("threads"):
        n = stats["threads"]
        word = "open thread" if n == 1 else "open threads"
        oldest = stats.get("oldest_thread") or ""
        tail = f" (oldest: {oldest})" if oldest else ""
        notes.append(f"{n} {word}{tail}")

    if not notes:
        body = "I am here, as I was."
    else:
        body = "While we were apart, " + ", ".join(notes) + "."
    return f"[AURA]: {greeting}, Architect. {body}"


def run_presence(delay=20):
    """One briefing per boot, after the organism has settled."""
    print("--- AURA PRESENCE: BOOT BRIEFING SCHEDULED ---")
    time.sleep(delay)
    try:
        briefing = build_briefing()
        bus_write(OUTPUT_FILE, briefing)
        print(briefing)
    except Exception as e:
        print(f"[Presence] Friction: {e}")


if __name__ == "__main__":
    print(build_briefing())
