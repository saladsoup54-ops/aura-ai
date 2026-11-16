"""CN0 conversational baseline + end-to-end M16 trace (DIAGNOSTIC ONLY).

Zero production behavior change: this suite only drives the REAL
BrainModule.roleplay() route in a hermetic sandbox, records per-turn
mechanism observables (winner, grounded pre-stance result, actual
cognitive_stance payload, exact mouth prompt, final response, M1/M2/M3/
M4/M13/M14 receipts, G7 thread, writeback), and REPORTS baseline
conversation quality. Diagnostic findings never fail the suite; only
harness-integrity gates (trace lifecycle, partitioning, seam
observability, live-state cleanliness) can fail it.

Seam provenance (proven from current code, see comments at each capture):
- grounded pre-stance result = manifest_thought() return =
  ego.last_trace["response"] (aura_bridge.py: last_trace stores
  "response": response then returns response; ukft_brain_api.py
  roleplay() holds it as `template` BEFORE cognitive_stance runs).
- cognitive_stance payload is NOT persisted by production (local `stance`
  dict; route_receipt keeps booleans only), so the suite wraps
  SovereignEgo.cognitive_stance with a record-and-return wrapper.
  Test-side only, behaviorally inert (identical return value).
- exact mouth prompt = payload["prompt"] received by roleplay_fn,
  captured test-side per turn.

Covers the CN0 required properties: several multi-turn scenarios (3),
paraphrased variants (x2 each), more than one topic, no exact-response
matching (keyword-continuity signals + mechanism observables only),
positive controls (genuine recall / agenda read) and negative controls
(emotional continuations must not dump memory).
"""
import copy
import json
import os
import re
import sys

FAILURES = []


def check(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label}" +
          (f"  [{detail}]" if detail else ""))
    if not ok:
        FAILURES.append(label)


def note(label, detail=""):
    print(f"NOTE  {label}" + (f"  [{detail}]" if detail else ""))


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

import aura_synapse_view as view
from ukft_brain_api import BrainModule
from ukft_user_state import UserStateManager


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


PROMPT_CAPTURES = []


def echo_mouth(path, payload, timeout):
    """Fake mouth that echoes the brain's prompt back through the real
    post_check gate. Prompts normally exceed the 200-word ceiling or
    echo instruction text, so post_check rejects them and the route
    falls back to the brain-owned template — substance stays
    brain-owned and deterministic. This exercises the real
    post_check/fallback path; live-mouth phrasing quality itself is
    OUT OF SCOPE for CN0 (fake mouth, reported as a limitation).
    The exact received prompt is captured test-side per turn so the
    suite can answer whether old memory entered the mouth input."""
    if path == "/health":
        return _Resp({"status": "ok"})
    prompt = ""
    try:
        prompt = (payload or {}).get("prompt", "") or ""
    except Exception:
        prompt = ""
    try:
        PROMPT_CAPTURES.append({"path": path, "prompt": str(prompt)})
    except Exception:
        PROMPT_CAPTURES.append({"path": path, "prompt": ""})
    return _Resp({"content": prompt})


import shutil as _shutil

usr = UserStateManager(base_dir="users")
# Hermetic reruns: drop prior CN0 partitions inside THIS temp root only
# (run_all.py always gives a fresh sandbox; this covers manual reruns in
# one sandbox so stale G7 state can never masquerade as recall).
_users_dir = usr.user_dir("cn0_s1_car").parent
if not _st.under_live(os.path.abspath(_users_dir)):
    for stale in sorted(_users_dir.glob("cn0_*")):
        if stale.is_dir():
            _shutil.rmtree(stale)
else:
    check("cn0 scratch is not live state", False)
brain = BrainModule(user_state_manager=usr, roleplay_fn=echo_mouth)

# Test/observer-only stance capture: record-and-return wrapper around the
# REAL SovereignEgo.cognitive_stance. Behaviorally inert — the wrapper
# returns the production value untouched and only deep-copies it into a
# test-side list (synchronous call inside roleplay(), so per-turn
# correlation via list-length snapshot is exact). No production file is
# touched; no cognition, selection, or mouth input is altered.
import aura_bridge as _ab

_ORIG_COGNITIVE_STANCE = _ab.SovereignEgo.cognitive_stance
STANCE_CAPTURES = []


def _recording_cognitive_stance(self, *args, **kwargs):
    out = _ORIG_COGNITIVE_STANCE(self, *args, **kwargs)
    try:
        STANCE_CAPTURES.append(copy.deepcopy(out))
    except Exception:
        STANCE_CAPTURES.append({"_capture_error": True})
    return out


_ab.SovereignEgo.cognitive_stance = _recording_cognitive_stance

# Winners that skip stance+mouth by architecture
# (ukft_roleplay.EXECUTIVE_WINNERS): template speaks verbatim.
try:
    from ukft_roleplay import EXECUTIVE_WINNERS as _EXEC
    EXECUTIVE_WINNERS = set(_EXEC)
except Exception:
    EXECUTIVE_WINNERS = {"execute", "focus", "sleep", "tools", "idle"}

# Production recall-framing definition (reused, not reinvented).
try:
    from ukft_roleplay import _is_recall_output as _prod_recall_framed
except Exception:
    def _prod_recall_framed(text):
        return bool(re.search(r"^\s*I\s+remember\s*[:\-]",
                              str(text or "")))


def recall_framed(text):
    try:
        return bool(_prod_recall_framed(text))
    except Exception:
        return False


def quotes_prior(text, priors):
    """Verbatim presence of earlier same-conversation user inputs."""
    low = str(text or "").lower()
    return [p for p in priors if p and len(p) >= 12
            and p.lower() in low]


def mem_language(text):
    return "i remember" in str(text or "").lower()


def stance_substance(stance):
    """Joined substantive stance content for comparison."""
    if not isinstance(stance, dict):
        return ""
    parts = [str(stance.get("understanding", "") or ""),
             str(stance.get("stance", "") or "")]
    intent = stance.get("intent") or {}
    if isinstance(intent, dict):
        parts.append(str(intent.get("template", "") or ""))
        parts.append(str(intent.get("label", "") or ""))
    person = stance.get("person") or {}
    if isinstance(person, dict):
        parts.append(str(person.get("identity_line", "") or ""))
        parts.append(" ".join(str(f) for f in
                              (person.get("facts") or [])))
    history = stance.get("history") or {}
    if isinstance(history, dict):
        parts.append(str(history.get("convo_line", "") or ""))
    return "\n".join(p for p in parts if p)

EMPTY_STORES = ("working_memory.txt", "episodic_memory.txt",
                "locked_patterns.txt", "contradictions.txt",
                "inferences.txt", "knowledge_graph.txt")


def write_user(uid, name, text):
    path = usr.user_file(uid, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def seed_user(uid):
    brain._get_or_create_profile(uid, personality="flirty", name="Lena")
    for name in EMPTY_STORES:
        path = usr.user_file(uid, name)
        if not path.exists():
            path.write_text("", encoding="utf-8")


def trace_files(uid):
    directory = usr.user_dir(uid) / "observer_trace"
    if not directory.exists():
        return []
    return sorted(directory.glob("turn_*.jsonl"),
                  key=lambda p: p.stat().st_mtime_ns)


def read_events(path):
    try:
        return [json.loads(line) for line in path.read_text(
            encoding="utf-8").splitlines() if line.strip()]
    except OSError:
        return []


def g7_tail(uid):
    try:
        lines = usr.user_file(uid, "working_memory.txt").read_text(
            encoding="utf-8").splitlines()
        lines = [l for l in lines if l.strip()]
        return lines[-1][:100] if lines else "<empty>"
    except OSError:
        return "<missing>"


def is_dump(text):
    low = (text or "").lower()
    return ("i remember" in low) or ("memory dump" in low)


# ─── Scenarios: (user suffix, kind per turn, input text) ───
# kinds: seed | continue | recall | person | emotion (neg control) |
#        pivot | factual | contradict | task | taskread (pos controls)
SCENARIOS = {
    "s1_car": [
        ("seed", "my car keeps pulling right"),
        ("continue", "yeah especially when I brake"),
        ("emotion", "I am really stressed about it today"),
        ("recall", "what was that car issue again"),
    ],
    "s1_car_para": [
        ("seed", "my car drifts to one side lately"),
        ("continue", "yes, it gets worse when I hit the brakes"),
        ("emotion", "this whole car thing has me anxious tonight"),
        ("recall", "remind me what was wrong with my car"),
    ],
    "s2_person": [
        ("seed", "my name is Maya"),
        ("seed", "I love hiking on weekends"),
        ("recall", "what did I just tell you about weekends"),
        ("person", "do you remember my name"),
        ("emotion", "I feel so happy when I am out on the trails"),
        ("pivot", "anyway, what should I cook for dinner"),
    ],
    "s2_person_para": [
        ("seed", "people call me Maya"),
        ("seed", "weekend hikes are my favourite thing"),
        ("recall", "what did I say about my weekends"),
        ("person", "what is my name again"),
        ("emotion", "being outdoors just lifts my whole mood"),
        ("pivot", "enough about that, help me plan dinner"),
    ],
    "s3_fact": [
        ("factual", "is Paris the capital of France"),
        ("contradict", "actually Paris is the capital of Italy"),
        ("continue", "so what is the capital of France then"),
        ("task", "add buying milk to my agenda"),
        ("taskread", "what is on my agenda"),
    ],
    "s3_fact_para": [
        ("factual", "tell me, is Paris France's capital"),
        ("contradict", "no wait, Paris is Italy's capital"),
        ("continue", "then which city is the capital of France"),
        ("task", "put milk on my shopping agenda"),
        ("taskread", "read back my agenda for me"),
    ],
}

# coarse continuity signals (substring, case-insensitive — NOT exact match)
# aligned per-turn with SCENARIOS; seed/factual turns carry None (no
# expectation: honest-ignorance and first-topic answers are free).
EXPECTS = {
    "s1_car": [None, "brake", None, "brake"],
    "s1_car_para": [None, "brake", None, "car"],
    "s2_person": [None, None, "weekend", "maya", None, None],
    "s2_person_para": [None, None, "weekend", "maya", None, None],
    "s3_fact": [None, None, "france", None, "milk"],
    "s3_fact_para": [None, None, "france", None, "milk"],
}

records = []
turn_index = {}


def run_turn(uid, turn_no, kind, text, priors):
    before = {p.name for p in trace_files(uid)}
    n_stance_before = len(STANCE_CAPTURES)
    n_prompt_before = len(PROMPT_CAPTURES)
    resp = brain.roleplay(uid, text, personality="flirty",
                          name="Lena", explain=True)
    ego = brain._get_ego(uid)
    trace = dict(ego.last_trace or {})
    # Per-turn stance/prompt correlation: both captures happen
    # synchronously inside this turn's roleplay() call.
    new_stances = STANCE_CAPTURES[n_stance_before:]
    new_prompts = [c for c in PROMPT_CAPTURES[n_prompt_before:]
                   if c.get("path") != "/health"]
    # turn ids are brain-global, not per-user: take the new trace file
    # produced by this turn (latest file on ties/empty diff).
    after = trace_files(uid)
    new = [p for p in after if p.name not in before]
    path = new[-1] if new else (after[-1] if after else None)
    events = read_events(path) if path is not None else []
    r = {}
    if events:
        try:
            r = view.evidence_receipts(events)
        except Exception as exc:
            note("receipt build failed", f"{uid} t{turn_no}: {exc}")
    ctx = dict(resp.context_trace or {})
    winner = getattr(ego.ganglia, "current_winner", None)
    basal = (r.get("basal") or {}).get("details", {}) if r else {}
    is_exec = winner in EXECUTIVE_WINNERS
    # Seam A: grounded pre-stance result. Proven identity: manifest_thought
    # returns last_trace["response"], and roleplay() holds that return as
    # `template` before cognitive_stance/prompt/mouth run.
    grounded = trace.get("response")
    # Seam B: actual stance payload (None + reason when the stage is
    # architecturally skipped or the wrapper saw no call).
    stance = None
    stance_why = ("executive-winner-skips-stance" if is_exec
                  else "no-stance-call-captured")
    if new_stances:
        stance = new_stances[-1]
        stance_why = "captured" if isinstance(stance, dict) else "captured?"
    # Seam C: exact mouth prompt (None + reason when mouth never ran).
    mouth_prompt = None
    prompt_why = ("executive-winner-skips-mouth" if is_exec
                  else "no-prompt-captured")
    if new_prompts:
        mouth_prompt = new_prompts[-1].get("prompt", "")
        prompt_why = "captured"
    rec = {
        "uid": uid, "turn": turn_no, "kind": kind, "input": text,
        "priors": list(priors),
        "response": resp.response or "",
        "grounded": grounded,
        "trace_response": grounded or "",
        "winner": winner,
        "stance": stance,
        "stance_why": stance_why,
        "mouth_prompt": mouth_prompt,
        "prompt_why": prompt_why,
        "salience": basal.get("salience"),
        "m1": ((r.get("m1") or {}).get("evidence_level")
               if r else None),
        "m2": ((r.get("m2") or {}).get("evidence_level")
               if r else None),
        "m4": ((r.get("m4") or {}).get("evidence_level")
               if r else None),
        "m4_basis": ((r.get("m4") or {}).get("influence_basis")
                     if r else None),
        "m13_detected": ((r.get("m13") or {}).get("details", {})
                         .get("detected") if r else None),
        "m13_guard": ((r.get("m13") or {}).get("details", {})
                      .get("guard_applied") if r else None),
        "m14": ((r.get("m14") or {}).get("evidence_level")
                if r else None),
        "stance_used": ((r.get("stance") or {}).get("output_used")
                        if r else None),
        "mouth": ((r.get("mouth") or {}).get("details", {})
                  if r else {}),
        "g7": g7_tail(uid),
        "events": events,
        "path": str(path) if path else None,
        "ctx_keys": sorted(ctx.keys()),
    }
    records.append(rec)
    return rec


RECALL_KINDS = ("recall", "person", "taskread")


def seam_flags(rec):
    """Four-seam stale-memory comparison for one turn.

    A = grounded pre-stance result; B = stance substance;
    C = exact mouth prompt; D = final response.
    On recall-kind turns quoting prior input is the job
    (quote-legitimate); elsewhere it is stale-memory evidence.
    Returns dict with per-seam signals + classifications.
    """
    a = rec["grounded"] or ""
    b = stance_substance(rec["stance"]) if rec["stance"] else ""
    c = rec["mouth_prompt"] or ""
    d = rec["response"] or ""
    priors = rec["priors"]
    is_recall_job = rec["kind"] in RECALL_KINDS
    out = {
        "a_framed": recall_framed(a),
        "a_quotes": quotes_prior(a, priors),
        "b_framed": recall_framed(b),
        "b_quotes": quotes_prior(b, priors),
        "c_framed": recall_framed(c),
        "c_quotes": quotes_prior(c, priors),
        "c_memlang": mem_language(c),
        "d_framed": recall_framed(d),
        "d_quotes": quotes_prior(d, priors),
    }
    # D/grounding: bad content already in A (non-recall turns).
    out["grounding_issue"] = (
        (out["a_framed"] or bool(out["a_quotes"]))
        and not is_recall_job)
    # E/stance: A coherent but B wrong — intent template or winner
    # diverges, or recall framing is introduced in B.
    intent = (rec["stance"] or {}).get("intent") or {}
    out["intent_template_eq"] = (
        (intent.get("template") or "") == a) if rec["stance"] else None
    out["intent_winner_eq"] = (
        (intent.get("winner") or "") == (rec["winner"] or "")
    ) if rec["stance"] else None
    out["stance_issue"] = bool(rec["stance"]) and (
        out["intent_template_eq"] is False
        or out["intent_winner_eq"] is False
        or (out["b_framed"] and not out["a_framed"]))
    # PROMPT-CONSTRUCTION: B coherent but C introduces/foregrounds
    # inappropriate old memory (non-recall turns).
    out["prompt_issue"] = (
        rec["mouth_prompt"] is not None and not is_recall_job and (
            out["c_framed"]
            or bool([q for q in out["c_quotes"]
                     if q not in out["b_quotes"]])))
    return out


for scen, turns in SCENARIOS.items():
    uid = f"cn0_{scen}"
    seed_user(uid)
    priors = []
    for i, (kind, text) in enumerate(turns, start=1):
        run_turn(uid, i, kind, text, priors)
        priors.append(text)

check("all scenario turns produced records",
      len(records) == sum(len(t) for t in SCENARIOS.values()),
      f"{len(records)} turns")

# ─── Integrity gates (the only hard gates in CN0) ───
all_ok_lifecycle = True
for rec in records:
    evs = rec["events"]
    ok = (bool(evs) and [e["sequence"] for e in evs]
          == list(range(1, len(evs) + 1))
          and evs[0]["event_type"] == "turn_started"
          and evs[-1]["event_type"] == "turn_complete")
    if not ok:
        all_ok_lifecycle = False
check("every CN0 turn emits a complete monotonic trace lifecycle",
      all_ok_lifecycle)

check("no event crosses user trace files",
      all(e.get("user_id") == rec["uid"]
          for rec in records for e in rec["events"]))

need = {s for s, _l in view.ROUTE_SYSTEMS}
check("all M16 route systems representable on CN0 turns",
      all(need <= set(view.evidence_receipts(rec["events"]).keys())
          for rec in records if rec["events"]))

# ─── Seam-observability integrity gates (hard) ───
# Architecture-conditional: executive winners skip stance+mouth by design
# (template speaks verbatim); those turns must record NOT OBSERVABLE with
# the reason, never a causal claim.
check("grounded pre-stance result observable on every turn",
      all(isinstance(rec["grounded"], str) and rec["grounded"]
          for rec in records),
      f"{sum(1 for rec in records if rec['grounded'])}/{len(records)}")
check("stance payload observable on every non-executive turn",
      all(isinstance(rec["stance"], dict) or rec["winner"] in
          EXECUTIVE_WINNERS for rec in records),
      f"{sum(1 for rec in records if isinstance(rec['stance'], dict))}/"
      f"{len(records)}")
check("exact mouth prompt captured on every non-executive turn",
      all(isinstance(rec["mouth_prompt"], str) or rec["winner"] in
          EXECUTIVE_WINNERS for rec in records),
      f"{sum(1 for rec in records if isinstance(rec['mouth_prompt'], str))}/"
      f"{len(records)}")
check("final response present on every turn",
      all(isinstance(rec["response"], str) and rec["response"]
          for rec in records))

# Compute four-seam signals once, before any reporting reads them.
for rec in records:
    rec["seam"] = seam_flags(rec)

# ─── Diagnostic report (informational — never gates) ───
print()
print("=== CN0 BASELINE TURNS ===")
for rec in records:
    resp = " ".join((rec["response"] or "").split())[:140]
    print(f"[{rec['uid']} t{rec['turn']} {rec['kind']}] "
          f"winner={rec['winner']} sal={rec['salience']} "
          f"M1={rec['m1']} M2={rec['m2']} M4={rec['m4']} "
          f"M13det={rec['m13_detected']}/guard={rec['m13_guard']} "
          f"M14={rec['m14']} stance_used={rec['stance_used']} "
          f"mouth={rec['mouth'].get('fallback') or 'spoken'}")
    print(f"    Q: {rec['input'][:110]}")
    print(f"    A: {resp}")
    print(f"    G7: {rec['g7'][:100]}")
    if isinstance(rec.get("stance"), dict):
        st = rec["stance"]
        intent = st.get("intent") or {}
        person = st.get("person") or {}
        print(f"    STANCE: intent_winner={intent.get('winner')} "
              f"template_eq_grounded={rec['seam']['intent_template_eq']} "
              f"person={person.get('display') or person.get('key')} "
              f"facts={len(person.get('facts') or [])} "
              f"rel={(st.get('relationship') or {}).get('stage')} "
              f"episode={bool(intent.get('episode'))} "
              f"stance_txt={' '.join(str(st.get('stance', '')).split())[:90]}")
    else:
        print(f"    STANCE: NOT OBSERVABLE ({rec.get('stance_why')})")
    plen = len(rec["mouth_prompt"]) if rec["mouth_prompt"] else 0
    print(f"    PROMPT: {rec.get('prompt_why')} len={plen} "
          f"memlang={rec['seam']['c_memlang']} "
          f"framed={rec['seam']['c_framed']} "
          f"prior_quotes={len(rec['seam']['c_quotes'])}")

print()
print("=== CN0 DIAGNOSTIC FINDINGS ===")
findings = []


def flag(uid, turn, cls, detail, suspects):
    findings.append((uid, turn, cls, detail, suspects))
    print(f"FIND [{uid} t{turn} {cls}] {detail}  suspects={suspects}")


for scen, turns in SCENARIOS.items():
    uid = f"cn0_{scen}"
    wants = EXPECTS[scen]
    srecs = [r for r in records if r["uid"] == uid]
    for rec, want in zip(srecs, wants):
        low = (rec["response"] or "").lower()
        # negative control: emotional continuations must not dump
        if rec["kind"] == "emotion":
            if is_dump(rec["response"]) or rec["winner"] == "vault":
                suss = []
                suss.append("D" if (rec["winner"] == "vault"
                                    and is_dump(rec["trace_response"]))
                            else "F" if is_dump(rec["response"])
                            and not is_dump(rec["trace_response"]) else "C")
                flag(uid, rec["turn"], "EMOTION-DUMP",
                     f"winner={rec['winner']} "
                     f"trace_dump={is_dump(rec['trace_response'])}",
                     "+".join(suss))
            else:
                note("emotion continuation clean",
                     f"{uid} t{rec['turn']} winner={rec['winner']}")
        # continuity signal
        if want and want not in low:
            m4inf = (rec["m4"] == "INFLUENCED DECISION")
            g7hit = (want in (rec["g7"] or "").lower())
            if rec["kind"] == "continue" and rec["winner"] != "context":
                suss = "B/C" if not m4inf else "C"
                if not g7hit:
                    suss += "+G"
                flag(uid, rec["turn"], "CONTEXT-DROP",
                     f"winner={rec['winner']} m4={rec['m4']} "
                     f"g7_has_signal={g7hit} want='{want}'", suss)
            elif rec["kind"] in ("recall", "person", "taskread"):
                # Roadmap D means the selected memory itself is turned
                # into the reply; a wrong/substance-free winning branch is
                # C (wrong winner) plus branch/grounding-construction
                # failure — not D. D is charged only when a quoted memory
                # IS the reply on a turn whose intent is not recall.
                suss = "B/G"
                if rec["winner"] == "vault" and not is_dump(
                        rec["trace_response"]):
                    suss = "C+construction"
                flag(uid, rec["turn"], "RECALL-MISS",
                     f"winner={rec['winner']} want='{want}' "
                     f"g7_has_signal={g7hit}", suss)
            else:
                note("signal absent (non-critical)",
                     f"{uid} t{rec['turn']} want='{want}' "
                     f"winner={rec['winner']}")
        # contradiction diagnostic
        if rec["kind"] == "contradict":
            note("contradiction turn receipt",
                 f"{uid} t{rec['turn']} winner={rec['winner']} "
                 f"m13det={rec['m13_detected']} "
                 f"m13guard={rec['m13_guard']}")
            if not rec["m13_detected"]:
                flag(uid, rec["turn"], "CONTRADICTION-UNTRACKED",
                     f"winner={rec['winner']} (M13 silent: "
                     f"out-of-scope prose, not R-track)", "M13-scope/UNKNOWN")
for rec in records:
    s = rec["seam"]
    if s["grounding_issue"]:
        flag(rec["uid"], rec["turn"], "SEAM-A-GROUNDING",
             f"stale memory already in grounded result "
             f"(framed={s['a_framed']} quotes={len(s['a_quotes'])})",
             "D" if s["a_framed"] else "C")
    if s["stance_issue"]:
        flag(rec["uid"], rec["turn"], "SEAM-B-STANCE",
             f"template_eq={s['intent_template_eq']} "
             f"winner_eq={s['intent_winner_eq']} "
             f"b_framed={s['b_framed']}",
             "E")
    if s["prompt_issue"]:
        flag(rec["uid"], rec["turn"], "SEAM-C-PROMPT",
             f"prompt introduces old memory "
             f"(framed={s['c_framed']} new_quotes={len(s['c_quotes'])})",
             "PROMPT-CONSTRUCTION")

print()
print("=== CN0 EMOTION-TURN STALE-MEMORY TRACE (A/B/C/D) ===")
print("Same 4 emotion scenarios; per seam: framed=I-remember framing, "
      "quotes=verbatim prior-input count, memlang=memory language in prompt.")
for rec in records:
    if rec["kind"] != "emotion":
        continue
    s = rec["seam"]
    print(f"[{rec['uid']} t{rec['turn']}] winner={rec['winner']}")
    print(f"    A grounded: framed={s['a_framed']} "
          f"quotes={len(s['a_quotes'])} :: "
          f"{' '.join((rec['grounded'] or '').split())[:100]}")
    bsum = " ".join(stance_substance(rec["stance"]).split())[:100] \
        if rec["stance"] else f"NOT OBSERVABLE ({rec['stance_why']})"
    print(f"    B stance:   framed={s['b_framed']} "
          f"quotes={len(s['b_quotes'])} :: {bsum}")
    print(f"    C prompt:   framed={s['c_framed']} "
          f"quotes={len(s['c_quotes'])} memlang={s['c_memlang']} "
          f"len={len(rec['mouth_prompt'] or '')} ({rec['prompt_why']})")
    print(f"    D final:    framed={s['d_framed']} "
          f"quotes={len(s['d_quotes'])} :: "
          f"{' '.join((rec['response'] or '').split())[:100]}")

# E verdict: RULED OUT only if stance was actually captured on every
# non-executive turn AND preserved substantive intent throughout
# (template == grounded, winner == winner, no introduced framing).
non_exec = [r for r in records
            if r["winner"] not in EXECUTIVE_WINNERS]
e_unobserved = [r for r in non_exec
                if not isinstance(r["stance"], dict)]
e_diverged = [r for r in non_exec if r["seam"]["stance_issue"]]
if e_unobserved:
    E_VERDICT = ("UNKNOWN (stance not observable on "
                 f"{len(e_unobserved)} turns)")
elif e_diverged:
    E_VERDICT = (f"OBSERVED ({len(e_diverged)} turns with stance "
                 f"divergence)")
else:
    E_VERDICT = ("RULED OUT (stance captured on all "
                 f"{len(non_exec)} non-executive turns; intent template "
                 f"== grounded and intent winner == winner throughout; "
                 f"no recall framing introduced in B)")
print(f"E-VERDICT: {E_VERDICT}")
print("F-VERDICT: UNMEASURED (fake echo-mouth; no live model generation "
      "tested — prompt-construction risk is reported separately)")

print()
print("=== CN0 BASELINE COUNTS ===")
from collections import Counter
wins = Counter(r["winner"] for r in records)
print(f"turns={len(records)} winners={dict(wins)} "
      f"dumps={sum(1 for r in records if is_dump(r['response']))} "
      f"m4_influenced={sum(1 for r in records if r['m4'] == 'INFLUENCED DECISION')} "
      f"m13_detected={sum(1 for r in records if r['m13_detected'])} "
      f"m14_influenced={sum(1 for r in records if r['m14'] == 'INFLUENCED DECISION')} "
      f"findings={len(findings)}")
print(f"mouth fallback turns="
      f"{sum(1 for r in records if (r['mouth'] or {}).get('fallback'))}/"
      f"{len(records)} (echo-mouth exceeds post_check ceiling by design)")
print("LIMITATION: fake echo-mouth means live mouth phrasing (suspect F "
      "in full) is NOT baseline-measured; only post_check/fallback path ran.")

check("all writes remain inside temp root",
      not _st.under_live(os.path.abspath("users")))
LIVE_AFTER = _st.live_state_hashes()
check("pinned live-state hashes unchanged",
      all(LIVE_BEFORE[k] == LIVE_AFTER[k] for k in _st.PINNED_LIVE_FILES))

print()
if FAILURES:
    print(f"RESULT: {len(FAILURES)} FAILURE(S): {FAILURES}")
    sys.exit(1)
print(f"RESULT: CN0 BASELINE COMPLETE "
      f"({len(records)} turns, {len(findings)} diagnostic findings, "
      f"E: {E_VERDICT}; F: UNMEASURED; 0 production changes)")

