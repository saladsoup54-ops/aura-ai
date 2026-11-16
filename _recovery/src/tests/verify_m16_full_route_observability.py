"""M16 full-route observability through BrainModule.roleplay().

Safe sandbox only. Proves explicit RAN / OUTPUT PRODUCED / OUTPUT USED /
INFLUENCED DECISION receipts without changing cognition.
"""
import json
import os
import sys
import threading


FAILURES = []


def check(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label}" +
          (f"  [{detail}]" if detail else ""))
    if not ok:
        FAILURES.append(label)


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ["AURA_NO_MOUTH"] = "1"

import _sandbox_guard as _sg
_sg.guard()
import aura_state as _st

ROOT = _st.require_test_root()
LIVE_BEFORE = _st.live_state_hashes()
check("suite runs in declared temp root",
      os.path.normcase(os.path.abspath(os.getcwd())) == ROOT)

import observer_telemetry as obs
import aura_synapse_view as view
from aura_field import FIELD
from ukft_brain_api import BrainModule
from ukft_inference import InferenceEngine
from ukft_user_state import UserStateManager


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def mouth(path, payload, timeout):
    if path == "/health":
        return _Resp({"status": "ok"})
    return _Resp({"content": "I can hold that grounded answer with you."})


usr = UserStateManager(base_dir="users")
brain = BrainModule(user_state_manager=usr, roleplay_fn=mouth)


def write_user(uid, name, text):
    path = usr.user_file(uid, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_profile(uid):
    brain._get_or_create_profile(uid, personality="flirty", name="Lena")
    for name in ("working_memory.txt", "episodic_memory.txt",
                 "locked_patterns.txt", "contradictions.txt",
                 "inferences.txt", "knowledge_graph.txt"):
        path = usr.user_file(uid, name)
        if not path.exists():
            path.write_text("", encoding="utf-8")


GRAPH = """--- AURA KNOWLEDGE GRAPH (V5 R2) | NODES: 6 | EDGES: 3 | TS: 1 ---
NODE: orion
NODE: sirius
EDGE: orion | compare:greater_than | sirius | CONF: 0.90 | SRC: TEST
EDGE: orion | compare:less_than | sirius | CONF: 0.90 | SRC: TEST
NODE: altair
NODE: vega
EDGE: altair | compare:faster_than | vega | CONF: 0.90 | SRC: TEST
"""


def seed_m13(uid):
    seed_profile(uid)
    write_user(uid, "knowledge_graph.txt", GRAPH)
    engine = InferenceEngine(
        graph_path=str(usr.user_file(uid, "knowledge_graph.txt")),
        out_path=str(usr.user_file(uid, "inferences.txt")),
        contradictions_path=str(usr.user_file(uid, "contradictions.txt")))
    engine.infer().save()
    write_user(uid, "locked_patterns.txt", "")
    write_user(uid, "working_memory.txt", "")
    write_user(uid, "episodic_memory.txt", "")


def seed_m14(uid):
    seed_profile(uid)
    write_user(uid, "knowledge_graph.txt",
               "--- AURA KNOWLEDGE GRAPH (V5 R2) | NODES: 1 | EDGES: 0 | TS: 1 ---\nNODE: dummy\n")
    write_user(uid, "inferences.txt",
               "--- AURA INFERENCES (V5 R3) | KNOWN: 0 | TS: 1 ---\n")
    write_user(uid, "contradictions.txt",
               "--- AURA CONTRADICTIONS (V5 R3) | KNOWN: 0 | TS: 1 ---\n")
    write_user(uid, "locked_patterns.txt",
               "ANCHOR: France Maps | DATA: We discussed France cartography maps together. | SOURCE: TEST\n")
    write_user(uid, "working_memory.txt", "")
    write_user(uid, "episodic_memory.txt",
               "--- AURA EPISODIC MEMORY (v1) | EPISODES: 1 ---\n"
               "EPISODE: 100 | KIND: conversation | CONCEPTS: france cartography | "
               "CONTENT: we studied france cartography maps\n")


def trace_path(uid, turn="1"):
    directory = usr.user_dir(uid) / "observer_trace"
    matches = sorted(directory.glob(f"turn_{turn}-*.jsonl"),
                     key=lambda path: path.stat().st_mtime_ns)
    if matches:
        return matches[-1]
    return directory / f"turn_{turn}-missing.jsonl"


def load_trace(uid, turn="1"):
    path = trace_path(uid, turn)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(
        encoding="utf-8").splitlines() if line.strip()]


def receipts(uid, turn="1"):
    return view.evidence_receipts(load_trace(uid, turn))


# 1. M13 guard on the real GF route, plus a same-state unrelated control.
FIELD.nodes.clear()
GUARD = "discord:9"
seed_m13(GUARD)
guard_response = brain.roleplay(
    GUARD, "is orion greater than sirius", personality="flirty", name="Lena")
guard_evs = load_trace(GUARD)
guard_r = receipts(GUARD)
guard_trace = json.loads(json.dumps(brain._get_ego(GUARD).last_trace))
check("Discord-style id writes inside the sanitized user partition",
      trace_path(GUARD).exists()
      and "discord_9" in str(trace_path(GUARD)), str(trace_path(GUARD)))
check("roleplay emits one complete monotonic turn lifecycle",
      bool(guard_evs)
      and [e["sequence"] for e in guard_evs]
      == list(range(1, len(guard_evs) + 1))
      and guard_evs[0]["event_type"] == "turn_started"
      and guard_evs[-1]["event_type"] == "turn_complete")
check("known M13 guard is INFLUENCED DECISION",
      guard_r["m13"]["evidence_level"] == "INFLUENCED DECISION"
      and guard_r["m13"]["influence_basis"] == "guard-selected-conflict"
      and guard_r["m13"]["details"]["guard_applied"],
      str(guard_r.get("m13")))
check("selected basal winner and Pass-2 stance are separate stages",
      guard_r["basal"]["evidence_level"] == "INFLUENCED DECISION"
      and guard_r["basal"]["details"]["winner"] == "conflict"
      and guard_r["stance"]["evidence_level"] == "OUTPUT USED"
      and not guard_r["stance"]["influenced_decision"],
      str((guard_r.get("basal"), guard_r.get("stance"))))
check("mouth is downstream realization, never decision authority",
      guard_r["mouth"]["ran"]
      and guard_r["mouth"]["evidence_level"] == "OUTPUT USED"
      and not guard_r["mouth"]["influenced_decision"],
      str(guard_r.get("mouth")))
check("Pass-1 hearing is future-turn output, not current influence",
      guard_r["hearing_bridge"]["ran"]
      and not guard_r["hearing_bridge"]["output_used"]
      and not guard_r["hearing_bridge"]["influenced_decision"])
check("all required M16 route systems are representable",
      {system for system, _label in view.ROUTE_SYSTEMS} <= set(guard_r),
      str(sorted(guard_r)))

CONTROL = "discord:10"
seed_m13(CONTROL)
brain.roleplay(CONTROL, "is altair faster than vega",
               personality="flirty", name="Lena")
control_r = receipts(CONTROL)
check("M13 detection is distinguishable from guard influence",
      control_r["m13"]["details"]["detected"]
      and not control_r["m13"]["details"]["guard_applied"]
      and control_r["m13"]["evidence_level"] == "OUTPUT USED"
      and not control_r["m13"]["influenced_decision"],
      str(control_r.get("m13")))
check("M3 selected proof is separately visible as influential",
      control_r["m3"]["evidence_level"] == "INFLUENCED DECISION"
      and control_r["m3"]["details"]["kind"] == "proof",
      str(control_r.get("m3")))
check("a subsystem may run/use output without false influence",
      control_r["m1"]["ran"]
      and control_r["m1"]["evidence_level"] != "INFLUENCED DECISION"
      and not control_r["m1"]["influenced_decision"],
      str(control_r.get("m1")))

BRANCH = "branch_user"
seed_profile(BRANCH)
write_user(BRANCH, "people.txt",
           "--- AURA PEOPLE (v1) | N: 1 ---\n"
           "PERSON: sarah | DISPLAY: Sarah | FIRST: 1 | LAST: 2 | "
           "MENTIONS: 2 | IMPORT: 2.000\n"
           "FACT: likes hiking | TS: 1 | SRC: TEST\n")
write_user(BRANCH, "knowledge_graph.txt", "")
write_user(BRANCH, "inferences.txt", "")
write_user(BRANCH, "contradictions.txt", "")
write_user(BRANCH, "locked_patterns.txt", "")
write_user(BRANCH, "working_memory.txt", "")
write_user(BRANCH, "episodic_memory.txt", "")
brain.roleplay(BRANCH, "who is Sarah", personality="flirty", name="Lena")
branch_r = receipts(BRANCH)
check("legacy people branch retains used status without unproven M5",
      branch_r["basal"]["details"]["winner"] == "people"
      and branch_r["people"]["evidence_level"] == "OUTPUT USED"
      and branch_r["people"]["details"]["selected"]
      and not branch_r["people"]["influenced_decision"],
      str(branch_r.get("people")))

M4_USER = "m4_user"
seed_profile(M4_USER)
write_user(M4_USER, "knowledge_graph.txt", "")
write_user(M4_USER, "inferences.txt", "")
write_user(M4_USER, "contradictions.txt", "")
write_user(M4_USER, "episodic_memory.txt", "")
write_user(M4_USER, "locked_patterns.txt",
           "ANCHOR: Brake | DATA: The car pulls right especially during "
           "brake pressure. | SOURCE: TEST\n")
write_user(M4_USER, "working_memory.txt",
           "--- AURA WORKING MEMORY (v1) | TURNS: 1 ---\n"
           "TURN: 1 | WINNER: context | CONCEPTS: car pulling right | "
           "QUERY: My car keeps pulling right | RESP: [AURA]: Does it "
           "get worse when you brake?\n")
brain.roleplay(M4_USER, "yeah especially when I brake",
               personality="flirty", name="Lena")
m4_r = receipts(M4_USER)
check("M4 strong conversation receipt is visible when context wins",
      m4_r["basal"]["details"]["winner"] == "context"
      and m4_r["m4"]["evidence_level"] == "INFLUENCED DECISION"
      and m4_r["m4"]["influence_basis"] == "m4-context-selected",
      str(m4_r.get("m4")))
check("M1/M2 consumed verdicts stop below influence without a turn counterfactual",
      m4_r["m1"]["evidence_level"] == "OUTPUT USED"
      and m4_r["m2"]["evidence_level"] == "OUTPUT USED"
      and not m4_r["m1"]["influenced_decision"]
      and not m4_r["m2"]["influenced_decision"],
      str((m4_r.get("m1"), m4_r.get("m2"))))

# 2. M14 admission on the same real roleplay route.
EPISODE = "episode_user"
seed_m14(EPISODE)
episode_response = brain.roleplay(
    EPISODE, "what did we say about france",
    personality="flirty", name="Lena", explain=True)
episode_r = receipts(EPISODE)
check("M14 episode admission is represented as causal",
      episode_r["m14"]["evidence_level"] == "INFLUENCED DECISION"
      and episode_r["m14"]["influence_basis"] == "episode-admission-selected"
      and episode_r["basal"]["details"]["winner"] == "reasoning",
      str(episode_r.get("m14")))
check("Pass-2 stance carries the selected episode but stays post-selection",
      (episode_response.context_trace or {}).get("m14", {}).get("eligible")
      and episode_r["stance"]["output_used"]
      and not episode_r["stance"]["influenced_decision"])

# Pass 1/1A: a later roleplay turn consumes restored old-brain field state.
FIELD_USER = "field_user"
brain.roleplay(
    FIELD_USER,
    "I finally fixed the gearbox problem today after struggling all week",
    personality="flirty", name="Lena")
for filename in ("working_memory.txt", "episodic_memory.txt"):
    write_user(FIELD_USER, filename, "")
FIELD.nodes.clear()
brain_field = BrainModule(user_state_manager=usr, roleplay_fn=mouth)
brain_field.roleplay(
    FIELD_USER, "what was I struggling with all week",
    personality="flirty", name="Lena")
field_r = receipts(FIELD_USER, turn="2")
check("restored old-brain field influence is visible on the later turn",
      field_r["old_brain_field"]["evidence_level"]
      == "INFLUENCED DECISION"
      and field_r["old_brain_field"]["details"]["restored_nodes"] > 0
      and field_r["basal"]["details"]["winner"] == "field",
      str(field_r.get("old_brain_field")))

# 3. Same turn numbers remain partitioned in traces and viewer/export grouping.
all_events = []
for uid in (GUARD, CONTROL, EPISODE):
    for event in load_trace(uid):
        event["_user_id"] = usr.user_dir(uid).name
        all_events.append(event)
grouped = view.export_real_turns(all_events)
check("different users retain distinct real observer turns",
      {uid for uid, _tid, _events in grouped}
      == {"discord_9", "discord_10", "episode_user"},
      str({(uid, tid) for uid, tid, _events in grouped}))
collision_events = []
for uid in (GUARD, CONTROL):
    for event in load_trace(uid):
        copied = dict(event)
        copied["turn_id"] = "same"
        copied["_user_id"] = usr.user_dir(uid).name
        collision_events.append(copied)
collision_keys = {(uid, tid) for uid, tid, _events
                  in view.export_real_turns(collision_events)}
check("same turn id stays isolated by user in viewer/export grouping",
      collision_keys == {("discord_9", "same"),
                         ("discord_10", "same")}, str(collision_keys))
check("no event crosses user trace files",
      all(e.get("user_id") == GUARD for e in load_trace(GUARD))
      and all(e.get("user_id") == CONTROL for e in load_trace(CONTROL)))

# Viewer refuses an unsupported influence claim even if booleans are forged.
spoof = {
    "event_type": "system_evidence", "subsystem": "mood",
    "advanced_raw": {"system": "mood", "ran": True,
                     "output_produced": True, "output_used": True,
                     "influenced_decision": True,
                     "influence_basis": "selected-winner"},
}
spoofed = view.evidence_receipts([spoof])["mood"]
check("viewer downgrades unsupported influence claims",
      spoofed["evidence_level"] == "OUTPUT USED"
      and not spoofed["influenced_decision"], str(spoofed))

def down_mouth(path, payload, timeout):
    return _Resp({"status": "down"} if path == "/health" else {"content": ""})


FALLBACK = "fallback_user"
brain_down = BrainModule(user_state_manager=usr, roleplay_fn=down_mouth)
fallback_response = brain_down.roleplay(
    FALLBACK, "hello", personality="flirty", name="Lena")
fallback_r = receipts(FALLBACK)
check("static greeting fallback is downstream used phrasing",
      "good to see you" in fallback_response.response.lower()
      and fallback_r["mouth"]["evidence_level"] == "OUTPUT USED"
      and fallback_r["mouth"]["details"]["fallback"]
      == "greeting-fallback"
      and not fallback_r["mouth"]["influenced_decision"],
      str(fallback_r.get("mouth")))

CONCURRENT = "concurrent_user"
seed_profile(CONCURRENT)
thread_errors = []


def concurrent_turn(text):
    try:
        brain.roleplay(CONCURRENT, text, personality="flirty", name="Lena")
    except Exception as exc:
        thread_errors.append(str(exc))


threads = [threading.Thread(target=concurrent_turn,
                            args=("hello from one",)),
           threading.Thread(target=concurrent_turn,
                            args=("hello from two",))]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()
concurrent_files = list((usr.user_dir(CONCURRENT) / "observer_trace")
                         .glob("turn_*.jsonl"))
concurrent_streams = []
for path in concurrent_files:
    events = [json.loads(line) for line in path.read_text(
        encoding="utf-8").splitlines() if line.strip()]
    concurrent_streams.append(events)
check("concurrent roleplay turns keep unique complete trace lifecycles",
      not thread_errors and len(concurrent_streams) == 2
      and all(events and events[-1]["event_type"] == "turn_complete"
              and [event["sequence"] for event in events]
              == list(range(1, len(events) + 1))
              for events in concurrent_streams),
       str((thread_errors, [len(events) for events in concurrent_streams])))

STANDING = "standing_user"
seed_profile(STANDING)
standing_one = brain.roleplay(
    STANDING, "where do we stand?", personality="flirty", name="Lena")
standing_two = brain.roleplay(
    STANDING, "where do we stand?", personality="flirty", name="Lena")
standing_files = list((usr.user_dir(STANDING) / "observer_trace")
                      .glob("turn_*.jsonl"))
standing_streams = []
for path in standing_files:
    standing_streams.append([json.loads(line) for line in path.read_text(
        encoding="utf-8").splitlines() if line.strip()])
check("standing pure reads still emit unique complete lifecycles",
      standing_one.turn_count == 0 and standing_two.turn_count == 0
      and len(standing_files) == 2
      and len({path.name for path in standing_files}) == 2
      and all(events[0]["event_type"] == "turn_started"
              and events[-1]["event_type"] == "turn_complete"
              for events in standing_streams),
      str([path.name for path in standing_files]))
standing_r = view.evidence_receipts(standing_streams[-1])
check("standing read invents no selector influence",
      standing_r and all(not receipt["influenced_decision"]
                         for receipt in standing_r.values()),
      str(standing_r))
check("standing read emits no false writeback change",
      all(event["event_type"] != "writeback_changed"
          for events in standing_streams for event in events))

# 4. Observer off is behaviorally inert on an identical causal route.
OFF = "observer_off"
seed_m13(OFF)
os.environ["AURA_OBSERVER_DISABLED"] = "1"
real_route_evidence = obs.route_evidence
obs.route_evidence = lambda *_args, **_kwargs: (_ for _ in ()).throw(
    AssertionError("disabled observer classified a route"))
try:
    off_response = brain.roleplay(
        OFF, "is orion greater than sirius",
        personality="flirty", name="Lena")
finally:
    obs.route_evidence = real_route_evidence
    os.environ.pop("AURA_OBSERVER_DISABLED", None)
off_ego = brain._get_ego(OFF)
off_winner = off_ego.ganglia.current_winner
off_trace = off_ego.last_trace
check("turning observer off does not alter selected response",
      off_winner == "conflict"
      and off_response.response == guard_response.response
      and off_trace.get("response") == guard_trace.get("response")
      and (off_trace.get("selection_receipt") or {}).get("selector")
      == (guard_trace.get("selection_receipt") or {}).get("selector")
      and off_trace.get("m13") == guard_trace.get("m13"),
      f"{off_winner} | {off_response.response[:80]}")
check("disabled observer writes no trace", not trace_path(OFF).exists())

# Export consumes the explicit receipt table, not prose inference.
diagnostics = view.build_diagnostics_text()
check("diagnostics export includes four-level M16 route evidence",
      "=== M16 ROUTE EVIDENCE ===" in diagnostics
      and "DORMANT" in diagnostics
      and "Mouth" in diagnostics)
check("guarded route evidence table renders proven influence",
      any("INFLUENCED DECISION" in line
          for line in view.format_evidence_table(guard_evs)))

check("candidate saliences remain unchanged",
      guard_r["basal"]["details"]["winner"] == "conflict"
      and abs(float(guard_r["basal"]["details"]["salience"]) - 0.95) < 1e-9)
check("all writes remain inside temp root",
      not _st.under_live(os.path.abspath("users")))
LIVE_AFTER = _st.live_state_hashes()
check("pinned live-state hashes unchanged",
      all(LIVE_BEFORE[k] == LIVE_AFTER[k] for k in _st.PINNED_LIVE_FILES))

print()
if FAILURES:
    print(f"RESULT: {len(FAILURES)} FAILURE(S): {FAILURES}")
    sys.exit(1)
print("RESULT: ALL M16 FULL-ROUTE OBSERVABILITY CHECKS PASSED")

