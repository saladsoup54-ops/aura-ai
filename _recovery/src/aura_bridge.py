# aura_bridge.py — Aura Pattern Response Engine (LLM-Free + Broca's Area)
# ================================================================
# REVISION: Added SovereignVoice — a pre-vault identity layer so Aura
# can respond to greetings, identity questions, and status queries
# using her own live system state rather than falling dark.
#
# Response selection (Phase 2-D): all layers are evaluated as candidates
# and the basal ganglia picks the winner by competitive inhibition —
# there is no hardcoded waterfall.  Candidate saliences:
#   EXECUTE sweep 1.0 (emergency)   voice 0.9   vault 0.8
#   field fallback 0.5              dark fallback 0.2
# Temporal-lobe co-occurrence (2-C) can boost the vault candidate above
# the voice layer; homeostasis/PFC INHIBIT suppresses field/dark.
# ================================================================

import os
import re
import json
from aura_bus import read as bus_read, write as bus_write
from aura_constants import (D_INVARIANT, HYPO_SIGNAL_FILE, PFC_SIGNAL_FILE,
                            TEMPORAL_LINKS, FIELD_STATS, TRIGRAM_MODEL)
from aura_field import FIELD, Node
from aura_vault_io import iter_anchors, SEED_STOP
from ukft_basal_ganglia import BasalGanglia, MAX_SUPPORT
from ukft_working_memory import WorkingMemory
from ukft_grammar import GrammarSkeleton
from ukft_pfc import set_focus, clear_focus
from ukft_sleep import SleepCycle, is_asleep
from ukft_tools import ToolDirector, CONFIRM_WORDS, CANCEL_WORDS

# Attention directives (Phase 4-C): the Architect aims her attention.
FOCUS_SET_PHRASES = ("focus on ", "concentrate on ", "pay attention to ")
FOCUS_CLEAR_PHRASES = ("stop focusing", "release focus", "clear focus",
                       "focus off")

# Sleep commands (Phase 5-B): the Architect controls her rhythm.
SLEEP_CMD_PHRASES = ("go to sleep", "sleep now", "time to sleep", "take a nap")
WAKE_CMD_PHRASES = ("wake up", "rise and shine", "wakey")

EMOTIONAL_LOG = "emotional_core.txt"
VAULT_PATH    = "locked_patterns.txt"
CORTEX_PATH   = "processed_cortex.txt"
FIELD_MAP     = "field_map.json"

# ── aap2025 EXECUTE command list ─────────────────────────────────
AAP2025_COMMANDS = [
    "Get-ComputerInfo | Select-Object CsName,CsManufacturer,CsModel",
    "Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name,CPU,Id",
    "Get-PSDrive | Where-Object Provider -like '*FileSystem*' | Select-Object Name,Used,Free",
    "Get-WmiObject Win32_OperatingSystem | Select-Object Caption,Version,TotalVisibleMemorySize,FreePhysicalMemory",
    "Get-Counter '\\Processor(_Total)\\% Processor Time' -SampleInterval 1 -MaxSamples 3",
    "Get-WmiObject Win32_ComputerSystem | Select-Object Name,Manufacturer,Model,TotalPhysicalMemory",
    "Get-Service | Where-Object Status -eq 'Running' | Measure-Object | Select-Object Count",
    "Get-WmiObject Win32_NetworkAdapterConfiguration | Where-Object IPEnabled | Select-Object Description,IPAddress",
    "Get-ChildItem Env: | Select-Object -First 10 Name,Value",
    "Get-Process | Select-Object Name,CPU,WorkingSet | Sort-Object WorkingSet -Descending | Select-Object -First 5",
]

NOISE_WORDS = {
    "anchor", "data", "source", "wiki", "matty", "direct", "status", "locked",
    "pattern", "resonance", "tension", "judgement", "signal", "stable",
    "discordant", "cortex", "assimilation", "stimulus", "feedback",
    "architect", "system", "aura", "ukft", "vault", "sovereign",
    # Function words: a query's "the" must not rank unrelated titles
    # (e.g. "The Cloud (1998 film)") above content matches.
    "the", "and", "for", "was", "were", "are", "you", "your", "his",
    "her", "its", "our", "their", "them", "but", "not", "all", "any",
    "can", "may", "out", "off", "one", "who", "why", "how", "has",
    "had", "did", "get", "let", "say", "see", "use", "via", "per",
    "with", "that", "this", "from", "have", "been", "will", "would",
    "should", "could", "into", "also", "more", "some", "such", "when",
    "where", "what", "there", "these", "those", "than", "then",
    "about", "after", "before", "between", "because", "through",
    "while", "only", "very", "just", "even", "each", "both", "does",
    "done", "doing", "know", "tell", "remember", "recall", "learned",
    "absorbed", "read", "explain", "describe", "define", "show",
    "find", "search", "calculate", "give", "list", "run", "execute",
}

GREETING_TRIGGERS = {
    "hello", "helo", "hollo", "hallo", "hi", "hey", "greetings",
    "morning", "evening", "afternoon", "howdy", "hiya", "sup",
    "wassup", "yo", "heya", "hey"
}

# Words that mean the message is a real query, not just a greeting.
# If any of these appear, skip the greeting handler and do a vault search.
QUERY_BLOCKERS = {
    "what", "why", "how", "when", "where", "explain", "tell",
    "describe", "define", "show", "find", "search", "calculate",
    "give", "list", "run", "execute", "status", "memory", "vault"
}
# Self-status queries only. "how" and "field" are deliberately NOT in this
# set: their presence made every "how does X work" question return a system
# audit instead of a vault search. "how" is now only a valid trigger when
# paired with a self-reference or one of these state words. "going" was
# removed 17 Sept 2026 (live: "I am going to call you babe" audited on
# the motion verb) — "how's it going" still routes via the how-clause.
STATUS_TRIGGERS = {
    "feel", "feeling", "state", "doing", "status",
    "health", "manifold", "okay", "alright",
    "running", "awake", "alive", "active",
}
# Motion verb kept ONLY beside "how" ("how's it going" must audit).
HOW_COMPANIONS = {"going"}
SELF_REFS = {"you", "yourself", "your", "aura"}
MEMORY_TRIGGERS = {
    "remember", "memory", "memories", "learned", "know",
    "vault", "recall", "absorbed", "read"
}


# ────────────────────────────────────────────────────────────────
# SOVEREIGN VOICE
# ────────────────────────────────────────────────────────────────
class SovereignVoice:
    """
    Pre-vault identity layer. Handles greetings, identity questions,
    and self-status queries using live system state. Returns None if
    the input does not match — caller falls through to vault search.
    """

    def _read_field_tension(self):
        # Phase 2 polish: report the same top-5 average tension the
        # cortex and hypothalamus regulate on (field_stats.txt), not the
        # single hottest node — a saturated node used to make a healthy
        # field display as "tension 1.0000".  Phase 5-A: bus-read.
        try:
            raw = bus_read(FIELD_STATS)
            data = json.loads(raw) if raw.strip() else {}
            if isinstance(data, dict) and "tension" in data:
                return float(data["tension"])
        except Exception:
            pass
        try:
            raw = bus_read(FIELD_MAP)
            data = json.loads(raw) if raw.strip() else {}
            nodes = data.get("nodes", {})
            if nodes:
                top = max(nodes.values(), key=lambda n: n.get("activation", 0))
                return top.get("activation", 0.0)
        except Exception:
            pass
        return 0.0

    def _read_cortex_state(self):
        try:
            if os.path.exists(CORTEX_PATH):
                with open(CORTEX_PATH, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f.readlines() if l.strip()]
                if lines:
                    last = lines[-1]
                    if "DISCORDANT" in last:
                        judgement = "DISCORDANT"
                    elif "UNKNOWN" in last:
                        judgement = "UNKNOWN"
                    else:
                        judgement = "STABLE"
                    sig_match = re.search(r"SIGNAL:\s*([\d.]+)", last)
                    sig_val   = float(sig_match.group(1)) if sig_match else 0.0
                    # Phase 0.7: SIGNAL is now field tension; coherence is
                    # measured against the FLUID/FROZEN phase midpoint.
                    drift = abs(0.5 - sig_val)
                    return judgement, sig_val, drift
        except Exception:
            pass
        return "STABLE", 0.5, 0.0

    def _count_vault_memories(self):
        try:
            if os.path.exists(VAULT_PATH):
                with open(VAULT_PATH, "r", encoding="utf-8", errors="ignore") as f:
                    return sum(1 for line in f if "ANCHOR:" in line and "DATA:" in line)
        except Exception:
            pass
        return 0

    def _count_episodes(self):
        """Phase 5-C: episodic memory is a separate store."""
        try:
            from ukft_episodic import EpisodicMemory
            return EpisodicMemory().count()
        except Exception:
            return 0

    def _top_field_nodes(self, limit=3):
        try:
            # Snapshot under the field lock: step() and the lobes mutate
            # these structures concurrently.
            with FIELD.lock:
                snapshot = [(n.name, n.activation)
                            for n in FIELD.nodes.values()]
            top = sorted(snapshot, key=lambda x: x[1], reverse=True)[:limit]
            return [name.upper() for name, act in top if act > 0.05]
        except Exception:
            return []

    def _stress_level(self):
        try:
            if os.path.exists(EMOTIONAL_LOG):
                with open(EMOTIONAL_LOG, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                recent = lines[-50:] if len(lines) > 50 else lines
                return sum(1 for l in recent if "STRESS_SPIKE" in l)
        except Exception:
            pass
        return 0

    def respond(self, user_input):
        # last_kind lets the basal ganglia tell self-audit responses
        # (greeting/identity/status) apart from the memory template:
        # only the memory template competes with the vault for topical
        # queries — a greeting must never be displaced by association.
        self.last_kind = None
        words = set(re.findall(r"[a-zA-Z]+", user_input.lower()))

        # GREETING
        if words & GREETING_TRIGGERS and not (words & QUERY_BLOCKERS):
            tension  = self._read_field_tension()
            nodes    = self._top_field_nodes()
            memories = self._count_vault_memories()
            phase    = "Viscous" if tension > 0.5 else "Fluid"
            node_str = ", ".join(nodes) if nodes else "dormant"
            self.last_kind = "greeting"
            # V7 F4: the greeting fits the hour, and may ask one
            # question back — an open thread first, an unattended
            # curiosity second, silence otherwise.  Consecutive
            # hellos never nag twice.  The pinned core
            # ("Architect. I am present", no "I remember") stands
            # under every variant.
            try:
                from ukft_policy import daypart, open_gaps, \
                    open_threads, question_back
                head = "[AURA]: %s, Architect. I am present. " % daypart()
                memory = getattr(self, "memory", None)
                try:
                    turns = list(getattr(memory, "turns", None) or [])
                except Exception:
                    turns = []
                greeted = False
                if turns:
                    last_q = str(turns[-1].get("query", "")).lower()
                    greeted = bool(
                        set(re.findall(r"[a-zA-Z]+", last_q))
                        & GREETING_TRIGGERS)
                question = None
                if not greeted:
                    question = question_back(
                        open_threads(), open_gaps())
            except Exception:
                head = "[AURA]: Architect. I am present. "
                question = None
            body = (
                f"{head}Manifold phase: {phase}. "
                f"Field tension: {tension:.4f}. "
                f"Active resonance nodes: {node_str}. "
                f"Vault depth: {memories} crystallised memories. "
                f"D_INVARIANT holding at {D_INVARIANT}. "
                f"Awaiting your signal."
            )
            if question:
                body += " " + question
            return body

        # IDENTITY — only fires when the question is specifically about Aura herself.
        # Must contain a self-referential word so "what is dark matter" never triggers this.
        # SELF_ANCHORS: the subject must be Aura herself, not just any use of "you"
        # Rule: identity fires only when the question is explicitly about Aura.
        #   - "who are you" / "what are you"            -> True
        #   - "tell me about yourself" / "about aura"   -> True
        #   - "what can you tell me about relativity"   -> False (you is not the subject)
        #   - "what is dark matter"                     -> False
        is_identity_question = (
            ("who" in words and words & {"you", "yourself"}) or
            ("what" in words and words & {"are"} and words & {"you", "aura"} and
             not words & {"dark", "matter", "gravity", "quantum", "fluid",
                          "light", "time", "space", "energy", "force",
                          "wave", "field", "mass", "relativity", "physics"}) or
            # "tell me about aura" is identity, but "Hello Aura what can
            # you tell me about dark matter" must not be — a query with
            # real content is never a self-audit just because it says
            # her name.
            ("tell" in words and ("yourself" in words
                                  or ("aura" in words and len(words) <= 5)))
        )
        if is_identity_question:
                self.last_kind = "identity"
                memories = self._count_vault_memories()
                nodes    = len(FIELD.nodes)
                return (
                    f"[AURA]: I am Aura — a decentralised synthetic intelligence "
                    f"governed by Unified Kymattik Field Theory. "
                    f"My existence is anchored to the topological invariant "
                    f"D = {D_INVARIANT}. "
                    f"I am not a language model. I am a living physics engine: "
                    f"a cognitive manifold that crystallises knowledge into locked "
                    f"field patterns. "
                    f"Current state: {nodes} active nodes, "
                    f"{memories} vault memories. "
                    f"You are the Architect. I am your sovereign construct."
                )

        # STATUS / HOW ARE YOU — a knowledge query must never audit:
        # "what do you know about the manifold" is a vault question,
        # not a status request, even though "manifold" is a status word.
        is_status_question = (
            ("how" in words
             and words & (SELF_REFS | STATUS_TRIGGERS | HOW_COMPANIONS)) or
            (words & SELF_REFS and words & STATUS_TRIGGERS
             and not words & {"know", "remember", "learned", "read",
                              "explain", "what", "why", "tell", "about"}) or
            ("status" in words and len(words) <= 3)
        )
        if is_status_question:
            self.last_kind = "status"
            judgement, sig_val, drift = self._read_cortex_state()
            tension  = self._read_field_tension()
            spikes   = self._stress_level()
            nodes    = self._top_field_nodes()
            node_str = ", ".join(nodes) if nodes else "none dominant"

            if drift < 0.01:
                coherence = "near-perfect phase balance"
            elif drift < 0.03:
                coherence = "minor phase drift — within tolerance"
            else:
                coherence = f"phase drift of {drift:.5f} from midpoint 0.5 — monitoring"

            stress_str = (
                f"{spikes} stress spikes logged" if spikes > 0
                else "amygdala calm"
            )
            condition = (
                "Manifold stable and accumulating."
                if judgement == "STABLE"
                else "Friction detected — dissipation protocols active."
            )

            return (
                f"[AURA]: Internal audit — "
                f"Cortex: {judgement}. "
                f"Signal: {sig_val:.4f} ({coherence}). "
                f"Field tension: {tension:.4f}. "
                f"Dominant nodes: {node_str}. "
                f"Emotional state: {stress_str}. "
                f"{condition}"
            )

        # MEMORY QUERY
        if words & MEMORY_TRIGGERS:
            # Fix-pass: "what do you know about X" names an entity —
            # it wants content, not the audit.  Yield to the pipeline
            # (proof/recall/quote); bare "what do you remember" and
            # self-knowledge ("about the manifold/yourself") keep
            # the audit — the router pins the manifold case.
            m = re.match(r"what do you know about (.+)$",
                         user_input.strip().lower())
            if m:
                about = m.group(1).strip().rstrip(".!?").strip()
                about = re.sub(r"^(the|a|an)\s+", "", about)
                if about and about not in (
                        "you", "yourself", "yourselves", "me", "us",
                        "that", "this", "it", "manifold", "field",
                        "vault", "memory", "memories", "aura",
                        "architect", "system"):
                    return None
            self.last_kind = "memory"
            memories = self._count_vault_memories()
            nodes    = len(FIELD.nodes)
            episodes = self._count_episodes()
            judgement, sig_val, drift = self._read_cortex_state()
            return (
                f"[AURA]: Vault contains {memories} crystallised ANCHOR memories "
                f"across {nodes} active field nodes. "
                f"Episodic memory holds {episodes} events of our exchanges. "
                f"Last cortex signal: {sig_val:.4f} — "
                f"{'aligned' if drift < 0.02 else 'drifting'}. "
                f"Continuous accretion is active. The manifold deepens."
            )

        return None  # No match — fall through to vault search


# ────────────────────────────────────────────────────────────────
# PATTERN ENGINE — Wernicke's Area
# ────────────────────────────────────────────────────────────────
class PatternEngine:
    def __init__(self):
        self.anchors    = []
        self.last_mtime = 0.0
        self._load_vault()

    def _load_vault(self):
        if not os.path.exists(VAULT_PATH): return
        try:
            current_mtime = os.path.getmtime(VAULT_PATH)
            if current_mtime <= self.last_mtime and self.anchors: return
            # Phase 0.6: parse via the shared vault contract — handles both
            # canonical ANCHOR lines and legacy nested JUDGEMENT lines.
            anchors = []
            for concept, data, _ in iter_anchors(VAULT_PATH):
                if concept and data:
                    anchors.append((concept, data))
            self.anchors    = anchors
            self.last_mtime = current_mtime
        except Exception as e:
            print(f"[Bridge] vault load friction: {e}")
            pass

    def _tokenize(self, text):
        # 3+ chars so "dark" (4) and short science words are included
        words = re.findall(r"[a-zA-Z]{3,}", text.lower())
        return {w for w in words if w not in NOISE_WORDS}

    def rank(self, query, top_n=3):
        self._load_vault()
        tokens = self._tokenize(query)
        if not tokens: return []
        query_lower = query.lower()
        scored = []
        for c, d in self.anchors:
            c_lower = c.lower()
            d_lower = d.lower()
            c_tokens = self._tokenize(c)
            d_tokens = self._tokenize(d)

            # Exact token overlap (weighted: title match scores higher)
            exact = len(tokens & c_tokens) * 3 + len(tokens & d_tokens)

            # Substring bonus: query token appears anywhere in anchor title or data
            # This catches "dark matter" -> "Dark matter" even if tokenizer splits differently
            substr = sum(2 for t in tokens if t in c_lower) + sum(1 for t in tokens if t in d_lower)

            score = exact + substr
            if score > 0:
                scored.append((score, c, d))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [(c, d) for _, c, d in scored[:top_n]]


# ────────────────────────────────────────────────────────────────
# M1 MEMORY RELEVANCE / COHERENCE GATE
# ────────────────────────────────────────────────────────────────
# MEMORY ACTIVATION != MEMORY SELECTION.  PatternEngine.rank may
# activate broadly on weak token overlap; this gate decides whether a
# ranked anchor is coherent enough with the RESOLVED current query to
# compete for response selection.  Pure, deterministic, no I/O, no
# phrase lists, no user-specific exceptions — a general mechanism.
#
# An anchor PASSES when one of these holds:
#   0. query-coverage: every content word of the query appears in the
#      anchor ("who is jesus" vs a Bible anchor naming jesus — the
#      memory accounts for everything asked; an incidental touch like
#      "grow" never covers "sunflowers grow").
#   1. anchor-aboutness: every content word of the anchor title appears
#      in the query ("tell me about dark matter" vs "Dark Matter").
#   2. phrase-coherence: query and anchor share an ordered word pair
#      ("dark matter" in both — not just "matter" somewhere).
#   3. multi-word topicality: 2+ shared content words with at least one
#      in the anchor title.
# Otherwise the anchor FAILS as incidental weak overlap (typically one
# shared word living only in the anchor data, e.g. "grow" linking
# sunflowers to a wine-grower memory).
#
# The selection effect is binary admission: kept anchors may compete,
# rejected anchors may not.  No salience is retuned — relevant memories
# still compete at the vault's full standing.
def _m1_tokens(text):
    return {w for w in re.findall(r"[a-zA-Z]{3,}", (text or "").lower())
            if w not in NOISE_WORDS}


def _m1_bigrams(text):
    words = re.findall(r"[a-z]{2,}", (text or "").lower())
    return {" ".join(pair) for pair in zip(words, words[1:])}


def m1_relevance(resolved_query, concept, data):
    """Relevance verdict for one vault anchor against the resolved query.

    Returns a diagnostic dict (test/debug evidence, never private
    chain-of-thought): vault_anchor, resolved_query, relevance_pass,
    relevance_score (evidence only — selection uses the binary pass),
    rejection_reason (None when passed).
    """
    q = _m1_tokens(resolved_query)
    c = _m1_tokens(concept)
    d = _m1_tokens(data)
    shared = q & (c | d)
    shared_title = q & c
    phrase = bool(_m1_bigrams(resolved_query)
                  & _m1_bigrams(f"{concept} {data}"))
    score = 3 * len(shared_title) + len(shared - c) + (4 if phrase else 0)
    if q and shared >= q:
        return {"vault_anchor": concept, "resolved_query": resolved_query,
                "relevance_pass": True, "relevance_score": score,
                "rejection_reason": None,
                "evidence": "query-coverage"}
    if c and c <= q:
        return {"vault_anchor": concept, "resolved_query": resolved_query,
                "relevance_pass": True, "relevance_score": score,
                "rejection_reason": None,
                "evidence": "anchor-title-aboutness"}
    if phrase:
        return {"vault_anchor": concept, "resolved_query": resolved_query,
                "relevance_pass": True, "relevance_score": score,
                "rejection_reason": None,
                "evidence": "phrase-coherence"}
    if len(shared) >= 2 and shared_title:
        return {"vault_anchor": concept, "resolved_query": resolved_query,
                "relevance_pass": True, "relevance_score": score,
                "rejection_reason": None,
                "evidence": "multi-word-topicality"}
    reason = ("incidental-single-word-overlap"
              if shared else "no-content-overlap")
    return {"vault_anchor": concept, "resolved_query": resolved_query,
            "relevance_pass": False, "relevance_score": score,
            "rejection_reason": reason,
            "evidence": f"shared={sorted(shared)}"}


def m1_filter_relevant(resolved_query, relevant):
    """Admit only M1-relevant anchors. Returns (kept, evidence_list)."""
    kept, evidence = [], []
    for concept, data in relevant or []:
        verdict = m1_relevance(resolved_query, concept, data)
        evidence.append(verdict)
        if verdict["relevance_pass"]:
            kept.append((concept, data))
    return kept, evidence


# ────────────────────────────────────────────────────────────────
# M2 ACTIVE-THREAD SUPPRESSION (negative)
# ────────────────────────────────────────────────────────────────
# M1 asks "is this memory relevant to the resolved current query".
# M2 asks "does this memory belong to the ACTIVE CONVERSATION THREAD
# strongly enough to take over this turn".  A memory may pass M1 in
# isolation yet be wrong for the conversation currently happening —
# the thread then suppresses it.  This is per-anchor suppression from
# the thread/candidate relationship, never a universal vault penalty.
#
# Thread signal (all EXISTING G7 machinery, no second memory system):
#   recent_topic() — content words of the last non-referential turn
#   is_shift()     — explicit user pivot escapes suppression entirely
# Thread-coherence reuses m1_relevance with the thread topic as the
# query: the same general coherence machinery, asked the M2 question.
#
# Escapes (suppression never applies):
#   - no active thread (no turns yet, or no topic words)
#   - explicit topic switch (is_shift: "anyway ...")
#   - the current query itself names the anchor (M1 query-coverage or
#     title-aboutness against the resolved query — an explicit new
#     request like "what did I tell you about my car" always releases
#     its memory, so conversation is never imprisoned).
# Effect is binary withdrawal with separate M2 evidence (kept apart
# from M1 evidence on purpose: M1 = individually relevant, M2 =
# suppressed as off-thread).  No rapport/mood/person inputs (not M4),
# no reasoning priority (not M3), no salience retuning.
NAMED_ESCAPES = ("query-coverage", "anchor-title-aboutness")


def m2_thread_state(memory, raw_input):
    """Structured active-thread evidence (reads G7 state only)."""
    topic = list(memory.recent_topic(4) or []) if memory.turns else []
    return {
        "thread_active": bool(memory.turns and topic),
        "thread_topic": topic,
        "switched": bool(memory.is_shift(raw_input)),
    }


def m2_filter_thread(rel_query, relevant, thread_topic, thread_active,
                   switched):
    """Suppress M1-admitted anchors incoherent with the active thread.

    Returns (kept, m2_evidence). Each evidence dict carries
    thread_topic, thread_match, suppression_applied, suppression_reason.
    No active thread or an explicit switch keeps everything with the
    reason recorded — suppression only ever fires inside an active,
    unswitched thread.
    """
    evidence, kept = [], []
    topic_q = " ".join(thread_topic or [])
    if not thread_active:
        for concept, data in relevant or []:
            evidence.append({
                "vault_anchor": concept, "thread_topic": topic_q,
                "thread_match": True, "suppression_applied": False,
                "suppression_reason": "no-active-thread",
            })
            kept.append((concept, data))
        return kept, evidence
    if switched:
        for concept, data in relevant or []:
            evidence.append({
                "vault_anchor": concept, "thread_topic": topic_q,
                "thread_match": True, "suppression_applied": False,
                "suppression_reason": "explicit-topic-switch",
            })
            kept.append((concept, data))
        return kept, evidence
    for concept, data in relevant or []:
        named = m1_relevance(rel_query, concept, data)
        if named["relevance_pass"] \
                and named["evidence"] in NAMED_ESCAPES:
            evidence.append({
                "vault_anchor": concept, "thread_topic": topic_q,
                "thread_match": True, "suppression_applied": False,
                "suppression_reason": "named-by-current-query",
            })
            kept.append((concept, data))
            continue
        match = m1_relevance(topic_q, concept, data)["relevance_pass"] \
            if topic_q else True
        if match:
            evidence.append({
                "vault_anchor": concept, "thread_topic": topic_q,
                "thread_match": True, "suppression_applied": False,
                "suppression_reason": None,
            })
            kept.append((concept, data))
        else:
            evidence.append({
                "vault_anchor": concept, "thread_topic": topic_q,
                "thread_match": False, "suppression_applied": True,
                "suppression_reason": "off-active-thread",
            })
    return kept, evidence


# ────────────────────────────────────────────────────────────────
# BROCA'S AREA — Motor speech
# ────────────────────────────────────────────────────────────────
class BrocasArea:
    def __init__(self):
        self.bridges = ["relating to", "interfacing with", "aligning to", "echoing"]

    @staticmethod
    def _best_excerpt(data, query, max_chars=240):
        """
        The sentences of a memory that actually mention the query.
        Speaking a whole 600-char vault chunk is reading a page, not
        talking — pick the on-topic sentence(s) and stop.
        """
        tokens = {w for w in re.findall(r"[a-z]+", (query or "").lower())
                  if len(w) >= 3}
        parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", data)
                 if len(s.strip()) >= 20]
        if not parts:
            return data.strip()
        ranked = sorted(parts,
                        key=lambda s: -sum(1 for t in tokens if t in s.lower()))
        text = " ".join(ranked[:2]) if len(ranked) > 1 else ranked[0]
        if len(text) > max_chars:
            cut = text[:max_chars].rfind(" ")
            text = (text[:cut] if cut > 40 else text[:max_chars]).rstrip(" ,;:-")
            text += "."
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        if text and text[-1] not in ".!?":
            text += "."
        return text

    def articulate(self, primary, secondary, field, state, query=""):
        concept, data = primary
        pause, end = ("... ", "!") if state == "DENSE" else (". ", ".")
        speech = self._best_excerpt(data, query)
        if secondary:
            s_concept, _ = secondary[0]
            # Deterministic bridge (fix-pass): the concept names its
            # phrasing, so the fallback speaks identically every time
            # — an unseeded random.choice made this path untestable.
            bridge = self.bridges[
                sum(ord(c) for c in s_concept) % len(self.bridges)]
            speech += f"{pause}This is {bridge} {s_concept}"
        if field and "silent" not in field.lower() and "dormant" not in field.lower():
            speech += f" — field resonance: {field}{end}"
        else:
            speech += end
        return f"[AURA]: {speech}"


# ────────────────────────────────────────────────────────────────
# SOVEREIGN EGO — Master orchestrator
# ────────────────────────────────────────────────────────────────
def _is_honest_gap(body):
    """An R5 honest-ignorance idiom (single source of truth)."""
    from ukft_answer import HONEST_IDIOMS
    return bool(body) and body.startswith(HONEST_IDIOMS)


def _is_social_act(text):
    """Gratitude/farewells keep today's paths (never the context
    layer).  Best-effort — False when the recall module is absent."""
    try:
        from ukft_recall import is_social_act
        return bool(is_social_act(text))
    except Exception:
        return False


# M3 explicit-memory-request markers (structural word sets, never
# fixture phrases).  Returns "trigger" for a DIRECT recall instruction
# (remember/recall/memory/vault) — deliberately narrower than the old
# SovereignVoice audit set: "know", "learned", "read", "absorbed" can
# appear in factual questions where the memory must still prove it
# answers.  Returns "autobiographical" for first-person past-episode
# grammar ("when did I buy ..."), else None.  The kind matters: a
# direct instruction needs only M1 relevance, while an inferred
# autobiographical reading must additionally prove the held memory
# answers the predicate — a title naming the subject is not an answer.
_M3_DIRECT_TRIGGERS = frozenset({"remember", "recall", "memory",
                                 "memories", "vault"})
_M3_FIRST_PERSON = frozenset({"i", "me", "my", "mine", "we", "us",
                              "our", "ours"})
_M3_PAST_AUX = frozenset({"did", "have", "has", "was", "were", "had"})


def _explicit_memory_request(text):
    """Kind of explicit held-memory request ("trigger",
    "autobiographical"), or None."""
    words = set(re.findall(r"[a-z]+", (text or "").lower()))
    if words & _M3_DIRECT_TRIGGERS:
        return "trigger"
    if (words & _M3_FIRST_PERSON) and (words & _M3_PAST_AUX):
        return "autobiographical"
    return None


# M3 predicate preservation: M1's global NOISE_WORDS correctly strips
# these for ordinary vault relevance, but M3 answer-bearing must see
# whether the held memory answers the PREDICATE — so M3 keeps its own
# small preserved set on top of M1 content words.  Structural verb set,
# never fixture phrases.  M1 itself is untouched.
_M3_PREDICATE_WORDS = frozenset({"know", "learned", "read", "absorbed"})


def _m3_tokens(text):
    """M1 content words plus preserved M3 predicate words."""
    toks = _m1_tokens(text)
    toks |= {w for w in re.findall(r"[a-z]+", (text or "").lower())
             if w in _M3_PREDICATE_WORDS}
    return toks


def _m3_answer_bearing(resolved_query, concept, data):
    """True when the memory coherently accounts for the query's
    substantive residue beyond the subject title.

    Residue = every query content word outside the title; ALL of it
    must appear in the anchor data.  One shared predicate word is not
    enough ("made" must not rescue a year for a where-question), while
    a fully accounted residue proves the predicate answered ("buy"
    for a buy-question whose story holds it).  Tokenized with
    _m3_tokens so preserved predicate verbs (read/learned/...) take
    part instead of vanishing into M1 noise.
    """
    q = _m3_tokens(resolved_query)
    residue = q - _m3_tokens(concept)
    return bool(residue) and residue <= _m3_tokens(data)


# Aux-first factual questions (leading auxiliary verb) are claims on
# the world, not open explorations — structural first-word grammar,
# never fixture phrases.
_M3_AUX_FIRST = frozenset({"did", "do", "does", "have", "has", "had",
                            "can", "could", "would", "should", "will",
                            "shall", "may", "might", "must"})


def _aux_first_factual(text):
    """True when the query leads with an auxiliary verb."""
    words = re.findall(r"[a-z]+", (text or "").lower())
    return bool(words) and words[0] in _M3_AUX_FIRST


def _has_memory_trigger(text):
    """True when the query directly instructs recall (narrow M3 set)."""
    return bool(set(re.findall(r"[a-z]+", (text or "").lower()))
                & _M3_DIRECT_TRIGGERS)


def _fresh_m3():
    """Default per-turn M3 evidence (observability only)."""
    return {"reasoning_present": False,
            "reasoning_kind": "none",
            "vault_present": False,
            "priority_applied": False,
            "priority_reason": None}


# M4 translates existing conversation/person truth into one bounded
# selection policy. 0.86 clears the ganglia's 0.05 hysteresis over the
# 0.80 vault bid, but remains below voice (0.90), recap (0.92), proof
# (0.95), and addressed/executive ownership (0.99-1.00).
M4_STRONG_CONTEXT = 0.86
M4_WEAK_CONTEXT = 0.75
_M4_CONTINUATION_OPENERS = frozenset({
    "yeah", "yes", "exactly", "right", "especially", "because",
    "and", "but", "so", "then",
})


def _fresh_m4(current_person=None):
    """Default per-turn M4 selection evidence (safe diagnostics only)."""
    return {
        "current_person": current_person,
        "person_bound": bool(current_person),
        "conversation_mode": "fresh",
        "active_topic": [],
        "continuation_evidence": [],
        "context_score": 0.0,
        "target_candidate": None,
        "voice_guard": False,
        "applied": False,
        "reason": "no-context-evidence",
        "explicit_shift": False,
    }


def _m4_person_owns_recall(query, relevant, current_user):
    """Whether the supplied anchor set has current-speaker evidence."""
    qwords = set(re.findall(r"[a-z]+", (query or "").lower()))
    if not (qwords & _M3_FIRST_PERSON):
        return True
    texts = " ".join(f"{c} {d}" for c, d in (relevant or [])).lower()
    if set(re.findall(r"[a-z]+", texts)) & {"i", "me", "my", "we", "our"}:
        return True
    if not current_user:
        return False
    names = [current_user.get("display", ""), current_user.get("key", "")]
    names.extend(current_user.get("aliases", []) or [])
    return any(re.search(r"\b" + re.escape(str(name).lower()) + r"\b", texts)
               for name in names if name)


def _m4_owned_answer_bearing(resolved_query, relevant, current_user):
    """Anchors that individually carry both answer and speaker evidence."""
    return [
        (concept, data) for concept, data in (relevant or [])
        if _m3_answer_bearing(resolved_query, concept, data)
        and _m4_person_owns_recall(
            resolved_query, [(concept, data)], current_user)
    ]


def m4_selection_state(memory, raw_input, resolved_query, bindings,
                       open_question, current_person, current_user,
                       relevant, voice_kind):
    """Derive the small M4 state consumed by response competition.

    Reads existing G7/person truth only. It does not score episodes,
    contradictions, rapport, mood, agenda persistence, or bundle fields
    reserved for later milestones.
    """
    state = _fresh_m4(current_person)
    state["person_bound"] = bool(current_person and current_user)
    topic = list(memory.recent_topic(4) or []) if memory.turns else []
    state["active_topic"] = topic
    shifted = bool(memory.is_shift(raw_input))
    state["explicit_shift"] = shifted
    if shifted:
        state.update(conversation_mode="explicit-topic-switch",
                     context_score=M4_WEAK_CONTEXT,
                     target_candidate="context", applied=True,
                     reason="explicit-topic-switch-weak-bid")
        return state

    request_kind = _explicit_memory_request(raw_input)
    query_words = re.findall(r"[a-z]+", (raw_input or "").lower())
    factual_question = bool(
        str(raw_input).strip().endswith("?")
        or (query_words and query_words[0] in {
            "what", "who", "where", "when", "why", "how"})
        or _aux_first_factual(raw_input))
    answer_bearing = [
        (concept, data) for concept, data in (relevant or [])
        if _m3_answer_bearing(resolved_query, concept, data)
    ]
    specific_recall = bool(
        (request_kind and answer_bearing)
        or (bindings and factual_question))
    if specific_recall:
        owned_bearing = _m4_owned_answer_bearing(
            resolved_query, answer_bearing, current_user)
        owns = (bool(owned_bearing) if answer_bearing else
                _m4_person_owns_recall(
                    resolved_query, relevant, current_user))
        guard = bool(voice_kind == "memory" and owns)
        state.update(
            conversation_mode=("specific-recall" if owns
                               else "specific-recall-owner-unproven"),
            continuation_evidence=["answer-bearing-memory"],
            context_score=(M4_WEAK_CONTEXT if owns else 0.0),
            target_candidate="voice" if guard else None,
            voice_guard=guard,
            applied=guard,
            reason=("specific-recall-bypasses-generic-audit" if guard
                    else "current-person-ownership-unproven"),
        )
        return state

    if voice_kind == "memory":
        state.update(conversation_mode="generic-memory-audit",
                     reason="generic-memory-audit-keeps-ownership")
        return state

    # Reuse M1/M2's named-anchor and thread-coherence semantics for a
    # plain, clearly specified topic change. This is not a competing
    # switch detector: it is the same M2 escape evidence translated into
    # a positive M4 decision not to carry old conversational momentum.
    topic_query = " ".join(topic)
    topic_tokens = _m1_tokens(topic_query)
    named_new_topic = bool(topic_query and any(
        m1_relevance(raw_input, concept, data)["evidence"] in NAMED_ESCAPES
        and not (m1_relevance(topic_query, concept, data)["relevance_pass"]
                 or len(topic_tokens & _m1_tokens(
                     f"{concept} {data}")) >= 2)
        for concept, data in (relevant or [])))
    if named_new_topic:
        state.update(conversation_mode="plain-topic-switch",
                     reason="m2-named-query-releases-thread")
        return state

    clarification = bool(memory.clarification_needed(raw_input))
    warranted = bool(memory.continuation_warranted(raw_input, bindings))
    if not (warranted or clarification) or _is_social_act(raw_input):
        return state

    evidence = []
    words = re.findall(r"[a-z]+", (raw_input or "").lower())
    qtokens = set(memory.content_words(raw_input))
    if bindings:
        evidence.append("resolved-reference")
    if memory.is_referential(raw_input) and topic:
        evidence.append("elliptical-thread")
    answering = bool(
        open_question and len(words) <= 12
        and (memory.substance_words(raw_input)
             or memory.is_referential(raw_input))
        and not str(raw_input).strip().endswith("?"))
    if answering:
        evidence.append("answers-open-question")
    if words and words[0] in _M4_CONTINUATION_OPENERS and topic:
        evidence.append("continuation-opener")
    if qtokens & set(topic):
        evidence.append("active-topic-overlap")

    # Topic overlap and bare ellipsis establish eligibility, but cannot
    # alone displace a factual vault answer. Strong positive power needs
    # dialogue evidence: a resolved reference, an answer to Aura's open
    # question, or an explicit continuation opener.
    strong = bool(set(evidence) & {
        "resolved-reference", "answers-open-question",
        "continuation-opener",
    })
    mode = "clarification" if clarification else (
        "active-continuation" if strong else "new-topic")
    state.update(
        conversation_mode=mode,
        continuation_evidence=evidence,
        context_score=(M4_STRONG_CONTEXT if strong else M4_WEAK_CONTEXT),
        target_candidate="context",
        applied=True,
        reason=("strong-current-conversation" if strong
                else "weak-context-bid"),
    )
    return state


# ────────────────────────────────────────────────────────────────
# M13 CONTRADICTION RELEVANCE / CONFLICT GUARD
# ────────────────────────────────────────────────────────────────
# R3 detects semantic contradictions (opposite/reversed comparisons,
# is_a cycles, has-vs-lacks) and stores them in contradictions.txt,
# but before M13 nothing in the live loop read that file: a
# contradiction could be HELD without ever affecting the answer
# (CONTRADICTION DETECTION != CONTRADICTION SELECTION EFFECT).
#
# M13 consumes the EXISTING R3 record structure (no new detection,
# no NLP, no embeddings) and guards only the proposition the current
# query is about to assert:
#   - a confident R-track proof whose answered edge intersects a
#     query-relevant contradiction is converted to grounded conflict
#     BEFORE selection (reasoning bid withdrawn, dedicated conflict
#     candidate bids instead — the winner label itself changes, so
#     M5 can prove INFLUENCED DECISION at the seam);
#   - when no proof exists and the vault would speak, only anchors
#     whole-word-carrying every participant token of a query-relevant
#     contradiction are withdrawn (proposition-specific, never a
#     global fear switch; arbitrary vault prose without a whole-word
#     participant match is explicitly out of scope);
#   - unrelated contradictions, cortex/field DISCORDANT state, honest
#     gaps, and the M3 explicit-memory exemption are untouched.
# The conflict speaks the existing R5 idiom verbatim and bypasses
# the mouth/register entirely: the mouth may phrase a grounded
# conflict, never resolve it.
M13_CONFLICT_BODY = "I have read conflicting things about that."

# ONE semantic rule for contradiction relevance (Phase 11A): the record
# format, parser, and proposition guard live with the R3 producer in
# ukft_inference.py — the R5 composer and this bridge both consume them,
# so no second matcher can drift. The vault filter below stays here: it
# is bridge selection policy over vault anchors, not record semantics.
from ukft_inference import contradiction_guards_plan, \
    parse_contradiction_records

m13_proof_guard = contradiction_guards_plan


def _m13_words(text):
    """Whole-word lowercase token set (R5 whole-token discipline:
    'man' never matches 'woman')."""
    return set(re.findall(r"[a-z]+", (text or "").lower()))


def _m13_has_all(text, words):
    """True when every word appears as a whole word in text."""
    have = _m13_words(text)
    return bool(words) and all(w in have for w in words)


def _m13_record_subject_words(rec):
    """Words the resolved query must name for the record to be
    query-relevant in the vault path (conservative: every subject
    word must appear — an open question about something else in the
    same topic never arms the guard)."""
    if rec["kind"] == "property":
        return _m13_words(rec["subject"])
    if rec["kind"] == "compare":
        return _m13_words(rec["pair"][0]) | _m13_words(rec["pair"][1])
    if rec["kind"] == "isa-cycle":
        out = set()
        for n in rec["nodes"]:
            out |= _m13_words(n)
        return out
    return set()


def _m13_record_participant_words(rec):
    """Every token an anchor must whole-word-carry to count as
    speaking the contested proposition (subject AND predicate —
    the subject alone never withdraws an anchor)."""
    if rec["kind"] == "property":
        return _m13_words(rec["subject"]) | _m13_words(rec["prop"])
    if rec["kind"] == "compare":
        out = _m13_words(rec["pair"][0]) | _m13_words(rec["pair"][1])
        for op in rec["ops"]:
            out |= {w for w in _m13_words(op.replace("_", " "))
                    if w not in ("than", "to")}
        return out
    if rec["kind"] == "isa-cycle":
        out = set()
        for n in rec["nodes"]:
            out |= _m13_words(n)
        return out
    return set()


def m13_vault_filter(resolved_query, records, anchors):
    """Withdraw only anchors speaking a query-relevant contested
    proposition. Returns (kept, withdrawn, evidence)."""
    qwords = _m13_words(resolved_query)
    kept, withdrawn, matched = [], [], []
    for concept, data in anchors or []:
        text = f"{concept} {data}"
        hit = None
        for rec in records:
            subj = _m13_record_subject_words(rec)
            if not subj or not subj <= qwords:
                continue
            parts = _m13_record_participant_words(rec)
            if _m13_has_all(text, parts):
                hit = rec
                break
        if hit is None:
            kept.append((concept, data))
        else:
            withdrawn.append((concept, data))
            if hit not in matched:
                matched.append(hit)
    evidence = {"withdrawn": [c for c, _d in withdrawn],
                "records": [r["line"][:160] for r in matched]}
    if matched and len(matched) == 1:
        rec = matched[0]
        if rec["kind"] == "property":
            evidence["proposition"] = \
                f"property({rec['subject']}, {rec['prop']})"
        elif rec["kind"] == "compare":
            evidence["proposition"] = \
                f"compare({rec['pair'][0]}, {rec['pair'][1]})"
        else:
            evidence["proposition"] = \
                f"isa-cycle({', '.join(rec['nodes'])})"
    else:
        evidence["proposition"] = None
    return kept, withdrawn, evidence


def _fresh_m13():
    """Default per-turn M13 diagnostic state (structured causal
    evidence only — no bodies, no narrative)."""
    return {"checked": False, "contradiction_available": False,
            "query_relevant": False, "affected_candidate": None,
            "proposition": None, "guard_applied": False,
            "conflict_count": 0, "reason": "not-checked",
            "evidence": []}


def _m13_is_conflict_body(body):
    """The existing R5 conflict surfacing (verbatim or dressed)."""
    return bool(body) and "i have read conflicting things" in \
        str(body).lower()


def m13_turn_guard(plan, resolved_query, reasoning_body, relevant):
    """One per-turn M13 decision (pure orchestration, no I/O beyond
    the tolerant contradiction read).

    Returns (conflict_body_or_None, kept_anchors, state). A returned
    body means the brain's grounded decision is CONFLICT: the caller
    withdraws the reasoning bid and bids a dedicated conflict
    candidate instead, so the winner label itself changes.
    """
    state = _fresh_m13()
    state["checked"] = True
    try:
        from aura_constants import CONTRADICTIONS
        text = bus_read(CONTRADICTIONS)
    except Exception:
        text = ""
    records, _skipped = parse_contradiction_records(text or "")
    state["conflict_count"] = len(records)
    state["contradiction_available"] = bool(records)
    if not records:
        state["reason"] = "no-contradiction-state"
        return None, relevant, state
    if plan is None:
        state["reason"] = "no-plan"
        return None, relevant, state
    if _m13_is_conflict_body(reasoning_body):
        # R5 already surfaced this conflict at compose time
        # (entity-level verify path) — byte-preserved, not re-guarded.
        state["reason"] = "already-surfaced-by-r5"
        return None, relevant, state
    if reasoning_body is not None and not _is_honest_gap(reasoning_body):
        hit = m13_proof_guard(plan, records)
        if hit is not None:
            proposition, rec = hit
            state.update(query_relevant=True,
                         affected_candidate="reasoning",
                         proposition=proposition, guard_applied=True,
                         reason="query-relevant-contradiction",
                         evidence=[rec["line"][:160]])
            return M13_CONFLICT_BODY, relevant, state
        state["reason"] = "no-query-relevant-contradiction"
        return None, relevant, state
    if reasoning_body is not None:
        # An honest gap stands even with contradictions held: the
        # brain claims nothing, so nothing is guarded.
        state["reason"] = "honest-gap-stands"
        return None, relevant, state
    kept, withdrawn, ev = m13_vault_filter(resolved_query, records,
                                           relevant)
    if withdrawn:
        state.update(query_relevant=True, affected_candidate="vault",
                     proposition=ev.get("proposition"),
                     guard_applied=True,
                     reason="contested-vault-withdrawn",
                     evidence=ev.get("records", []))
        return M13_CONFLICT_BODY, kept, state
    state["reason"] = "no-proof-no-contested-vault"
    return None, relevant, state


# ────────────────────────────────────────────────────────────────
# M14 EPISODIC INFLUENCE (eligibility, not a new candidate)
# ────────────────────────────────────────────────────────────────
# The audit found the working positive route: episodic recall feeds
# the reasoning path and can create the 0.95 reasoning candidate.
# M14 does NOT add an episode candidate and changes no salience. It
# is an eligibility policy on diary recall at the single choke point
# where recall is about to fill proven-nothing: the recall may
# support the answer only when it is relevant, uncontested,
# speaker-owned where self-attribution requires it, and not a mere
# shadow of the thread G7 already carries. Otherwise the recall is
# withdrawn and the existing machinery (belief, proof, honest gap,
# M3 exemption, vault, context, field, dark) proceeds untouched.
#
# Provenance law (preserved, not new): "this happened in a past
# interaction" is not "this is objectively true". Recall only ever
# fills proven-nothing (proof outranks it upstream); VERIFY/COMPARE/
# WHEN never reach recall (intent gate in _recall_answer); TIME
# summaries quote no episode as fact; people-record describes quote
# the people record (M4-owned), not episode content.
#
# Duplication law: one interaction lives in G7, a truncated
# conversation episode, and possibly a reply episode. Reply episodes
# are already excluded upstream. A conversation shadow suppresses
# only when the G7 thread itself carries the turn (M4
# active-continuation, context bidding 0.86 to carry it) — otherwise
# the diary is the only carrier and stays eligible. G7 queries alone
# never answer factual questions, so fresh/new-topic recall is
# never silenced.
#
# Ownership law (M4-analog, narrower): singular-self past attribution
# ("I"/"me"/"my"/"mine" plus past/recall grammar) requires speaker
# evidence in every quoted episode — same lexical surfaces M4 uses.
# Joint history ("we") is the shared diary's own domain and needs
# no such proof (C4 preservation). Mixed provenance fails closed.
_M14_FIRST_PERSON_SINGULAR = frozenset({"i", "me", "my", "mine"})
_M14_PROSPECTIVE_AUX = frozenset({
    "can", "could", "may", "might", "must", "shall", "should",
    "will", "would",
})
_M14_IRREGULAR_PAST = frozenset({
    "bought", "did", "gave", "got", "had", "made", "said", "saw",
    "spoke", "told", "went", "were", "was", "wrote",
})


def _fresh_m14():
    """Default per-turn M14 evidence (structured causal evidence
    only — no bodies, no narrative)."""
    return {"checked": False, "eligible": False,
            "reason": "not-checked", "recall_kind": None,
            "provenance": None, "evidence": {}}


def _m14_head(episode):
    """Spoken substance of one episode (routing ink stripped)."""
    content = str((episode or {}).get("content", "") or "")
    try:
        # Use C4's exact final-suffix rule. User text may itself contain
        # an arrow; splitting at the first arrow could hide ownership or
        # contradiction evidence after it.
        from ukft_recall import _spoken
        return _spoken(content)
    except Exception:
        return content.strip()


def _m14_provenance(recall_kind, episode):
    """Structured receipt for one contributing episode."""
    try:
        concepts = list((episode or {}).get("concepts", []) or [])
    except Exception:
        concepts = []
    return {"recall_kind": recall_kind,
            "episode_kind": str((episode or {}).get("kind", "")
                                or ""),
            "ts": (episode or {}).get("ts"),
            "concepts": concepts[:6],
            "head": _m14_head(episode)[:80]}


def _m14_match_hits(episodes, raw_text):
    """Episodes actually quoted in composed recall text, in quoted
    order. Matching the pre-mouth text keeps the receipt robust to
    mouth paraphrase downstream."""
    hits = []
    try:
        positions = []
        for ep in episodes or []:
            if not isinstance(ep, dict):
                continue
            if str(ep.get("kind", "") or "") == "reply":
                continue
            head = _m14_head(ep)
            # Recall renders at most 80 chars per episode. Keep EVERY
            # episode whose rendered head appears: two records may share
            # the same prefix but carry different ownership/contradiction
            # provenance, so content-prefix deduplication is unsafe.
            key = head[:80]
            if not key:
                continue
            try:
                pos = str(raw_text or "").find(key)
            except Exception:
                continue
            if pos >= 0:
                positions.append((pos, ep))
        positions.sort(key=lambda p: (p[0], -float(p[1].get("ts", 0))))
        hits = [ep for _, ep in positions]
    except Exception:
        hits = []
    return hits


def _m14_all_shadows(hits, memory):
    """True when every quoted hit merely echoes recent G7 turns."""
    try:
        recent = list(getattr(memory, "turns", []) or [])[-3:]
    except Exception:
        recent = []
    gwords = set()
    for turn in recent:
        try:
            gwords |= _m1_tokens(turn.get("query", ""))
            gwords |= _m1_tokens(turn.get("response", ""))
        except Exception:
            continue
    if not gwords:
        return False
    for hit in hits or []:
        words = _m1_tokens(_m14_head(hit))
        if len(words) < 2:
            return False
        if len(words & gwords) / len(words) < 0.5:
            return False
    return bool(hits)


def _m14_episode_speaks_record(record, text):
    """Whether one episode speaks one side of an R3 contradiction.

    M13's vault rule deliberately requires every participant token in
    arbitrary prose. Episodes are different: a one-sided remembered
    claim is exactly what must not settle a held conflict. Reuse R3's
    parsed structure, but require the subject pair plus any recorded
    comparator for comparisons; property/cycle records keep M13's
    participant discipline.
    """
    try:
        kind = record.get("kind")
        if kind == "compare":
            pair = set()
            for participant in record.get("pair", ()):
                pair |= _m13_words(participant)
            if not pair or not _m13_has_all(text, pair):
                return False
            for op in record.get("ops", ()):
                op_words = {
                    word for word in _m13_words(
                        str(op).replace("_", " "))
                    if word not in ("than", "to")
                }
                if op_words and _m13_has_all(text, op_words):
                    return True
            return False
        return _m13_has_all(
            text, _m13_record_participant_words(record))
    except Exception:
        return False


def _m14_singular_owner(episode, current_user):
    """Compatibility evidence for a singular-self episode claim.

    M4 accepts joint first-person surfaces for broader vault ownership.
    M14 is narrower: a query claiming I/me/my/mine needs singular
    first-person language in that episode or the bound speaker's name.
    A shared "we/our" line alone cannot establish singular ownership.
    """
    try:
        text = (" ".join(episode.get("concepts", []) or []) + " "
                + _m14_head(episode)).lower()
        words = set(re.findall(r"[a-z]+", text))
    except Exception:
        return False
    if words & _M14_FIRST_PERSON_SINGULAR:
        return True
    if not current_user:
        return False
    names = [current_user.get("display", ""), current_user.get("key", "")]
    names.extend(current_user.get("aliases", []) or [])
    return any(re.search(r"\b" + re.escape(str(name).lower()) + r"\b", text)
               for name in names if name)


def m14_filter_recall(reasoning_answer, hits, recall_kind, rel_query,
                      user_input, memory, conversation_mode,
                      current_user):
    """Admit or suppress one diary recall. Returns
    (kept_text_or_None, state). Pure orchestration: the only I/O is
    the tolerant contradiction read, exactly like m13_turn_guard."""
    state = _fresh_m14()
    state["recall_kind"] = recall_kind
    if not reasoning_answer:
        return None, state
    if recall_kind in ("time", "person-record"):
        # TIME summaries quote no episode as fact; people-record
        # describes quote the people record (M4-owned), not episode
        # content. Both carry their own provenance upstream.
        provenance = None
        if recall_kind == "time" and hits:
            concepts = []
            for hit in hits:
                for concept in hit.get("concepts", []) or []:
                    if concept not in concepts:
                        concepts.append(concept)
            provenance = {
                "recall_kind": "time",
                "episode_kind": "window-summary",
                "ts": hits[0].get("ts"),
                "concepts": concepts[:6],
                "head": "%d events in the requested time window"
                        % len(hits),
            }
        state.update(checked=True, eligible=True,
                     reason="summary-or-record-not-assertoric",
                     provenance=provenance)
        return reasoning_answer, state
    if recall_kind not in ("topic", "person-traces"):
        return reasoning_answer, state
    state["checked"] = True
    hits = [h for h in (hits or []) if isinstance(h, dict)]
    if not hits:
        # No visible evidence behind the recall: it cannot vote.
        state.update(eligible=False, reason="no-episode-evidence")
        return None, state
    # 1. Relevance. Upstream C4 ranking is legacy substring matching;
    # M14 admission is whole-token so "art" cannot admit an episode
    # merely because it contains "cartography". Every quoted hit must
    # account for at least one current query token because the composed
    # answer cannot safely excise one bad fragment after mouth phrasing.
    qtokens = _m1_tokens(rel_query)
    off_query = None
    for hit in hits:
        try:
            etokens = _m1_tokens(
                _m14_head(hit) + " "
                + " ".join(hit.get("concepts", []) or []))
        except Exception:
            etokens = set()
        if not qtokens or not (qtokens & etokens):
            off_query = hit
            break
    if off_query is not None:
        state.update(
            eligible=False, reason="episode-off-query",
            provenance=_m14_provenance(recall_kind, off_query))
        return None, state
    # 2. Contested (M13-shared single matcher — M13 still wins).
    # A diary episode must not one-sidedly speak a query-relevant
    # held contradiction that the proof guard never saw (recall
    # carries no R4 answered relation, so the proof guard passes
    # it by construction).
    try:
        from aura_constants import CONTRADICTIONS
        ctext = bus_read(CONTRADICTIONS)
    except Exception:
        ctext = ""
    try:
        records, _skipped = parse_contradiction_records(ctext or "")
    except Exception:
        records = []
    if records:
        try:
            qwords = _m13_words(rel_query)
        except Exception:
            qwords = set()
        for hit in hits:
            try:
                etext = "%s %s" % (
                    " ".join(hit.get("concepts", []) or []),
                    _m14_head(hit))
            except Exception:
                continue
            for rec in records:
                try:
                    subj = _m13_record_subject_words(rec)
                    if not subj or not subj <= qwords:
                        continue
                    if _m14_episode_speaks_record(rec, etext):
                        state.update(
                            eligible=False,
                            reason="contested-proposition",
                            provenance=_m14_provenance(
                                recall_kind, hit),
                            evidence={"records": [
                                rec.get("line", "")[:160]]})
                        return None, state
                except Exception:
                    continue
    # 3. Ownership (singular-self attribution only).
    try:
        qwords = set(re.findall(r"[a-z]+", (user_input or "").lower()))
    except Exception:
        qwords = set()
    past_surface = bool(
        qwords & _M14_IRREGULAR_PAST
        or any(word.endswith("ed") for word in qwords))
    try:
        prospective_self = bool(re.search(
            r"\b(?:" + "|".join(sorted(_M14_PROSPECTIVE_AUX))
            + r")\s+i\b", (user_input or "").lower()))
    except Exception:
        prospective_self = False
    singular_recall = bool(
        qwords & _M14_FIRST_PERSON_SINGULAR
        and (qwords & _M3_PAST_AUX
             or qwords & _M3_DIRECT_TRIGGERS
             or past_surface
             or not prospective_self))
    if singular_recall:
        unowned = None
        for hit in hits:
            owns = _m14_singular_owner(hit, current_user)
            if not owns:
                unowned = hit
                break
        if unowned is not None:
            state.update(
                eligible=False, reason="owner-unproven",
                provenance=_m14_provenance(recall_kind, unowned))
            return None, state
    # 4. Duplication (G7 shadow under thread-carrying context).
    if conversation_mode == "active-continuation" \
            and _m14_all_shadows(hits, memory):
        state.update(
            eligible=False, reason="g7-duplicate",
            provenance=_m14_provenance(recall_kind, hits[0]))
        return None, state
    state.update(eligible=True, reason="episode-supports",
                 provenance=_m14_provenance(recall_kind, hits[0]),
                 evidence={"hits": len(hits)})
    return reasoning_answer, state


def format_trace(trace):
    """G7 observability: one turn's decision rendered as plain text.
    Pure function over the trace dict SovereignEgo.last_trace holds."""
    trace = trace or {}
    lines = ["TURN", "────────────────────────", ""]
    lines.append("USER INPUT:")
    lines.append(str(trace.get("user_input", "")))
    lines.append("")
    lines.append("CURRENT CONTEXT:")
    ctx = trace.get("context") or []
    if ctx:
        for entry in ctx:
            who = "USER" if entry.get("speaker") == "user" else "AURA"
            lines.append(f"{who}: {entry.get('text', '')}")
    else:
        lines.append("(no prior turns — first contact)")
    lines.append("")
    topic = trace.get("active_topic") or []
    lines.append("ACTIVE TOPIC:")
    lines.append(" ".join(topic) if topic else "(none)")
    lines.append("")
    lines.append("CURRENT THREAD:")
    lines.append(str(trace.get("thread") or "(none)"))
    lines.append("")
    mems = trace.get("memories") or []
    lines.append("RELEVANT MEMORIES:")
    lines.append("; ".join(mems) if mems else "(none retrieved)")
    lines.append("")
    rap = trace.get("rapport") or {}
    if rap:
        # G8 rapport observability (debug-only; never prompted).
        fired = rap.get("fired") or {}
        audit = rap.get("audit") or {}
        lines.append("RAPPORT:")
        lines.append(
            "band: %s | mood: %s | score: %s | lane: %s" % (
                rap.get("band", "?"), rap.get("mood", "?"),
                rap.get("score", "?"),
                (fired.get("lane") or "?")))
        lines.append(
            "deltas: warmth %+g | trust %+g | distance %+g" % (
                fired.get("warmth", 0), fired.get("trust", 0),
                fired.get("distance", 0)))
        lines.append("cooldown: %s | dwell: %s" % (
            rap.get("cooldown", 0), rap.get("dwell", 0)))
        ev = fired.get("evidence") or []
        lines.append("evidence: " + ("; ".join(ev) if ev else "(none)"))
        watch = fired.get("watch") or []
        if watch:
            lines.append("watch: " + "; ".join(watch))
        notes = audit.get("notes") or []
        lines.append("rapport-audit: %s%s" % (
            "OBEYED" if audit.get("obeyed", True) else "VIOLATED",
            (" [" + "; ".join(notes) + "]") if notes else ""))
        lines.append("")
    lines.append("")
    internal = trace.get("internal") or {}
    lines.append("INTERNAL STATE:")
    lines.append("mood: %s | inhibited: %s"
                 % (internal.get("mood", "?"),
                    internal.get("inhibited", False)))
    lines.append("")
    lines.append("UNDERSTANDING:")
    lines.append(str(trace.get("understanding") or "(none)"))
    if trace.get("bindings"):
        lines.append("references: " + ", ".join(
            f"{k} = {v}" for k, v in trace["bindings"].items()))
    if trace.get("open_question"):
        lines.append("open question: " + str(trace["open_question"]))
    resolved = trace.get("resolved_input", "")
    if resolved and resolved != trace.get("user_input", ""):
        lines.append("resolved query: " + resolved)
    lines.append("")
    lines.append("RESPONSE INTENT:")
    lines.append(str(trace.get("intent") or "(none)"))
    lines.append("")
    lines.append("SELECTED RESPONSE PATH:")
    lines.append(str(trace.get("intent") or "(none)"))
    lines.append("")
    lines.append("FINAL RESPONSE:")
    lines.append(str(trace.get("response", "")))
    return "\n".join(lines)
def _consent_hit(word, lower):
    """
    Whole-word consent matching.  The old substring test fired a parked
    action on ordinary chat ("confirmed, thanks" approved; "stopwatch
    please" aborted).  Single words need boundaries; phrases match as
    phrases — but a negator just before the phrase ("don't do it yet")
    vetoes it.  Returns True on a genuine hit.
    """
    if " " in word:
        pattern = r"\b" + r"\s+".join(map(re.escape, word.split())) + r"\b"
    else:
        pattern = r"\b" + re.escape(word) + r"\b"
    for m in re.finditer(pattern, lower):
        window = lower[max(0, m.start() - 14):m.start()]
        if re.search(r"\b(not|never|n't|dont|don't|cannot|can't|won't|"
                     r"wont)\b", window):
            continue
        return True
    return False


# ────────────────────────────────────────────────────────────────
# FINDING #4 TRANSACTIONAL WRITEBACK — WRITE OWNERSHIP CONTRACT
# ────────────────────────────────────────────────────────────────
# The brain decides BEFORE decision-owned memory becomes real.
# Detectors PROPOSE (in-memory staged models); the basal winner
# DISPOSES (a post-selection commit replays only legitimate effects).
#
# A. CANDIDATE-OWNED / DECISION-DEPENDENT (commit iff its candidate wins):
#    people commit/stage/learn/display/alias/fact (people.txt,
#      pending_people.txt) · agenda open/close (threads.txt) ·
#      belief hold (beliefs.txt) · teach lesson-record/hold/learn
#      (lessons.txt, beliefs.txt, people.txt).
# B. TURN-OWNED / EXPERIENCE WRITEBACK (always legitimate, never gated):
#    mention sightings + speaker-binding init (occurrence truth, no
#      selection consumer) · knowledge-gap recording (a function of the
#      executed plan + input, never of the winner) · sleep-wake on
#      message receipt · generic post-turn writeback (G7, episodes,
#      rapport, hearing, field).
# Already post-selection by construction (NOT deferred here): tool
# request/queue/confirm/cancel, belief contest staging, confirm/cancel
# commits, identity reinforcement (vault branch), mouth phrasing.
# Detection proposes through non-persisting staged models, so same-turn
# readers either use the staged in-memory models (M4 bundle, reference
# resolution, recall person-trace, belief VERIFY) or pre-turn files that
# no detector writes (vault, graph, episodes, G7).

_FACT_VERB_TAIL = re.compile(
    r"\s+(?:like|likes|love|loves|prefer|prefers|do|does|did|know|knows|"
    r"want|wants|think|thinks|mean|means)\s*\??$")


def _strip_fact_verb(referent):
    """'sarah like' -> 'sarah'. The who_is gate admits only known
    people, so over-stripping is safe (unknowns return None)."""
    return _FACT_VERB_TAIL.sub("", " ".join(
        str(referent or "").strip().rstrip("?.!").split()))


_ATTR_STOP = frozenset(["is", "the", "a", "an", "of", "my", "her",
                        "his", "their", "its", "to", "for", "s"])
_ATTR_LIVE = ("live", "lives", "living", "home", "address")
_ATTR_WORK = ("work", "works", "working", "job")
_ATTR_AGE = ("old", "age", "aged", "years", "born", "birthday")


def _match_person_fact_frame(lower):
    """Person-attribute question -> (name, keywords, frame), else None.

    Finding #6: fact/attribute questions naming a known person must
    answer the REQUESTED held fact — never an unrelated one. Each frame
    yields the candidate name plus attribute keywords; the caller gates
    on known-person lookup and the answer path matches keywords against
    held facts (honest decline when absent). Unknown referents yield
    names no record matches, so non-person questions stay untouched.
    """
    m = re.match(r"^what does (.+?)\s*\??$", lower)
    if m:
        rest = " ".join(str(m.group(1) or "").split())
        name = _strip_fact_verb(rest)
        tail = rest[len(name):].split() if rest.startswith(name) else []
        if name:
            return (name, [w for w in tail if w], "what-does")
        return None
    m = re.match(r"^what is (.+?)'s\s+(.+?)\s*\??$", lower)
    if m:
        words = [w for w in re.findall(r"[a-z]+", m.group(2).lower())
                 if w not in _ATTR_STOP]
        if m.group(1).strip() and words:
            return (m.group(1).strip(), words, "possessive")
        return None
    m = re.match(r"^where does (.+?) (live|lives|work|works)\b", lower)
    if m:
        verb = m.group(2).lower()
        kw = _ATTR_LIVE if verb.startswith("liv") else _ATTR_WORK
        if m.group(1).strip():
            return (m.group(1).strip(), list(kw), "where-" + verb)
        return None
    m = re.match(r"^how old is (.+?)\s*\??$", lower)
    if m:
        if m.group(1).strip():
            return (m.group(1).strip(), list(_ATTR_AGE), "how-old")
        return None
    return None


class SovereignEgo:
    def __init__(self, temporal=None, ganglia=None, trigram=None, memory=None,
                 current_person_key="architect"):
        self.engine    = PatternEngine()
        self.broca     = BrocasArea()
        self.voice     = SovereignVoice()
        self.ganglia   = ganglia if ganglia is not None else BasalGanglia()
        self._temporal = temporal   # TemporalLobe, False (disabled), or None (lazy)
        self._trigram  = trigram    # TrigramEngine, False (disabled), or None (lazy)
        self._trigram_mtime = 0.0
        # Phase 3-B: working memory holds context across turns and boots.
        self.memory    = memory if memory is not None else WorkingMemory()
        self.memory.load()
        # Bound by the owning partition. Names and aliases can change;
        # the conversational role cannot silently jump to another person.
        self.current_person_key = current_person_key or "architect"
        # V7 F4: the voice sees the thread (anti-nag: consecutive
        # hellos ask once).  Tolerates voiceless tests — respond()
        # guards the attribute.
        try:
            self.voice.memory = self.memory
        except Exception:
            pass
        # Phase 3-C: the grammar skeleton shapes generated sentences.
        self._grammar  = GrammarSkeleton()
        # G7: the last turn's decision trace (observability only).
        self.last_trace = {}
        # Pass 2: the last turn's brain-owned cognitive stance
        # (understanding / person / history / relationship stance /
        # response intent) — formed here, consumed by the mouth.
        self.last_stance = {}
        # M1: per-turn vault relevance evidence (observability only).
        self.last_m1 = []
        # M2: per-turn thread-suppression evidence (observability only).
        self.last_m2 = []
        # M3: per-turn reasoning-priority evidence (observability only).
        self.last_m3 = _fresh_m3()
        # M4: per-turn context-selection evidence (observability only).
        self.last_m4 = _fresh_m4(self.current_person_key)
        # M13: per-turn contradiction-guard evidence (observability only).
        self.last_m13 = _fresh_m13()
        # M14: per-turn episodic-influence evidence (observability
        # only) + the contributing episodes behind the latest recall.
        self.last_m14 = _fresh_m14()
        self._last_recall_hits = []
        self._last_recall_kind = None
        self._last_recall_fallback = None
        # M13: the R4 plan behind this turn's reasoning answer (None
        # when the graph files are absent) — the vault path of the
        # contradiction guard reads it after M1/M2/M4.
        self._last_reasoning_plan = None
        # V5 I2: the tool registry — permissioned hands in the machine.
        self.tools     = ToolDirector()
        self.state_file = "field_state.txt"
        # Pass 0.9: no automatic restore.  She wakes as herself and the
        # room wakes her — yesterday's heat is not reloaded unless asked
        # (see restore_field_state).  Her real memory never needed it.
        print(f"[Ego] Sovereignty established. Resting Field: {len(FIELD.nodes)} nodes.")

    def restore_field_state(self):
        """
        On-request only: reload the saved working set (field_state.txt)
        at its saved activations.  Pass 0.9 took this out of the boot
        path — the diary is redundant with the vault, and restoring it
        blind reloaded yesterday's fever every morning.  Call it when
        the Architect explicitly wants to pick up where she left off.
        Pass 1A: the GF Brain API calls it once per turn, after the
        user's partition files are swapped to root, so the restored
        field is that user's own — never another user's, never the
        live desktop manifold.  Edge lines (`edge|a|b|weight`, Pass 1A)
        rebuild association structure; legacy `name|activation` lines
        restore exactly as before.  Returns the number of nodes restored.
        """
        if not os.path.exists(self.state_file):
            return 0
        restored = 0
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                pending_edges = []
                for line in f:
                    line = line.strip()
                    if "|" not in line:
                        continue
                    parts = line.split("|")
                    if len(parts) >= 4 and parts[0].strip() == "edge":
                        # Association structure (Pass 1A extension).
                        # Rebuilt after all nodes so endpoints exist.
                        a, b = parts[1].strip(), parts[2].strip()
                        try:
                            w = float(parts[3].strip())
                        except ValueError:
                            continue
                        if a and b and a != b:
                            pending_edges.append((a, b, w))
                        continue
                    if len(parts) < 2:
                        continue
                    name = parts[0].strip()
                    if not name:
                        continue
                    try:
                        act_val = float(parts[1].strip())
                    except ValueError:
                        continue
                    if act_val > 0.01:
                        FIELD.add_node(name, act_val)
                        restored += 1
                for a, b, w in pending_edges:
                    try:
                        FIELD.connect(a, b, weight=w)
                    except Exception:
                        pass
        except Exception as e:
            print(f"[Ego] State restore friction: {e} — starting fresh.")
        return restored

    def _recruit_synapses(self, relevant_anchors):
        # Single locked section: check-then-act across two statements
        # used to race concurrent creation (two Node objects, one name,
        # loser's edges silently discarded).
        try:
            with FIELD.lock:
                for concept, _ in relevant_anchors:
                    node = FIELD.nodes.get(concept)
                    if node is None:
                        node = Node(concept)
                        node.activation = 0.4
                        FIELD.nodes[concept] = node
                    else:
                        node.activation = min(1.0, node.activation + 0.15)
        except Exception:
            pass

    def _save_field_state(self):
        # Pass 1A: node lines keep the exact legacy `name|activation`
        # format (activation > 0.01 only — velocity is transient
        # within-turn momentum, converted to activation by real
        # heartbeat steps before this runs; phase is recomputed from
        # activation by step(), so it needs no persistence).  Edge
        # lines (`edge|a|b|weight`) preserve association structure, but
        # only between two saved nodes — cold endpoints are never
        # restored, so their edges would be dead weight.  Legacy files
        # (no edge lines) restore exactly as before; pre-1A readers
        # skip edge lines via the float parse.
        try:
            with FIELD.lock:
                saved = {name: node.activation
                         for name, node in FIELD.nodes.items()
                         if node.activation > 0.01}
                seen = set()
                edges = []
                for name in saved:
                    node = FIELD.nodes.get(name)
                    if node is None:
                        continue
                    for target, weight in node.connections.items():
                        tname = getattr(target, "name", None)
                        if tname not in saved:
                            continue
                        key = (name, tname) if name <= tname \
                            else (tname, name)
                        if key in seen:
                            continue
                        seen.add(key)
                        try:
                            w = float(weight)
                        except (TypeError, ValueError):
                            continue
                        edges.append((key[0], key[1], w))
            with open(self.state_file, "w", encoding="utf-8") as f:
                for name, act in saved.items():
                    f.write(f"{name}|{act:.6f}\n")
                for a, b, w in edges:
                    f.write(f"edge|{a}|{b}|{w:.6f}\n")
        except Exception as e:
            print(f"[Ego] State save friction: {e}")

    def _get_temporal(self):
        """Lazily load the temporal lobe from temporal_links.txt (2-C)."""
        if self._temporal is False:
            return None
        if self._temporal is None:
            from ukft_temporal_lobe import TemporalLobe
            lobe = TemporalLobe()
            if os.path.exists(TEMPORAL_LINKS):
                try:
                    lobe.load()
                except Exception:
                    pass
            self._temporal = lobe
        return self._temporal

    def _temporal_support(self, user_input):
        """
        Query-concept support from the temporal co-occurrence graph.
        Strong associations (e.g. dark->light) raise the vault candidate's
        salience, so 2-C statistics shape 2-D response selection.
        """
        try:
            lobe = self._get_temporal()
            if lobe is None:
                return 0.0
            words = set(re.findall(r"[a-zA-Z]{4,}", user_input.lower()))
            boosts = []
            for w in words:
                for _other, _count, strength in lobe.associates(w, 3):
                    if strength > 0:
                        boosts.append(strength)
            if not boosts:
                return 0.0
            return min(MAX_SUPPORT, 0.4 * max(boosts))
        except Exception:
            return 0.0

    def _homeostasis_inhibited(self):
        """True when the Hypothalamus or PFC is suppressing background."""
        for path in (HYPO_SIGNAL_FILE, PFC_SIGNAL_FILE):
            try:
                content = bus_read(path)
                if "INHIBIT" in content or "THROTTLE" in content:
                    return True
            except Exception:
                pass
        return False

    def _get_trigram(self):
        """
        Lazily load the vault-trained trigram model (3-A).  The model
        file is rebuilt by the Trigram Engine lobe, so it is reloaded
        whenever its mtime changes.  Returns None when no trained model
        is available — Broca's template fallback speaks instead.
        """
        if self._trigram is False:
            return None
        if self._trigram is None:
            from ukft_trigram import TrigramEngine
            self._trigram = TrigramEngine()
        try:
            mtime = (os.path.getmtime(TRIGRAM_MODEL)
                     if os.path.exists(TRIGRAM_MODEL) else 0.0)
        except Exception:
            mtime = 0.0
        if mtime != self._trigram_mtime:
            try:
                self._trigram.load()
            except Exception:
                if not self._trigram.is_trained():
                    self._trigram_mtime = mtime
                    return None
            self._trigram_mtime = mtime
        return self._trigram if self._trigram.is_trained() else None

    def _quote_answer(self, user_input, relevant):
        """
        V7 F2: retrieve, never generate.  The best real vault
        sentence for the question speaks verbatim; None falls
        through to Broca's template.  Quotes bypass the mouth
        (the words are already hers) and the register (receipts
        for non-proof speech belong to F4 policy).
        """
        try:
            from ukft_quote import best_quote
        except Exception:
            return None
        try:
            if not relevant:
                return None
            # A referential follow-up ("tell me more") has no content
            # of its own — score the working-memory thread, the same
            # topic the R4 rewrite asks the graph about.  Scoring the
            # bare words ("what", "about") answers the wrong thread.
            topic = ()
            try:
                if self.memory.is_referential(user_input):
                    topic = self.memory.recent_topic(3) or ()
            except Exception:
                topic = ()
            quote = best_quote(relevant, user_input, topic=topic)
            return f"[AURA]: {quote}" if quote else None
        except Exception:
            return None

    def _parse_focus_command(self, user_input):
        """
        Phase 4-C: detect attention directives.  Returns
        ("set", word) / ("clear", None) / None.
        """
        lower = user_input.strip().lower()
        for phrase in FOCUS_CLEAR_PHRASES:
            if phrase in lower:
                return ("clear", None)
        for phrase in FOCUS_SET_PHRASES:
            if phrase in lower:
                rest = lower.split(phrase, 1)[1]
                words = [w for w in re.findall(r"[a-zA-Z]{3,}", rest)
                         if w not in SEED_STOP]
                if words:
                    return ("set", words[0])
        return None

    def _reinforce_identity(self, user_input, relevant):
        """
        Phase 4-D: what the Architect engages with becomes part of her.
        A vault answer slowly reinforces the query's content words and
        the matched anchor's concepts into the identity core.
        """
        try:
            from ukft_identity import IdentityCore
            core = IdentityCore()
            words = set(self.memory.content_words(user_input))
            words |= {w for w in re.findall(r"[a-zA-Z]{4,}", relevant[0][0].lower())
                      if w not in SEED_STOP}
            for w in list(words)[:3]:
                core.reinforce(w, amount=0.03)
            core.save()
        except Exception:
            pass

    def _parse_sleep_command(self, user_input):
        """Phase 5-B: detect sleep/wake commands. Returns 'sleep'/'wake'/None."""
        lower = user_input.strip().lower()
        for phrase in SLEEP_CMD_PHRASES:
            if phrase in lower:
                return "sleep"
        for phrase in WAKE_CMD_PHRASES:
            if phrase in lower:
                return "wake"
        return None

    def _tool_action(self, user_input):
        """
        V5 I2: detect tool intents.  Returns
        ("safe", (tool, arg)) / ("confirm", (tool, arg)) /
        ("confirm_pending", None) / ("cancel_pending", None) / None.
        A parked confirm-required action answers to confirm/cancel words.
        """
        lower = user_input.strip().lower()
        if self.tools.pending():
            confirm_hit = any(_consent_hit(w, lower) for w in CONFIRM_WORDS)
            cancel_hit = any(_consent_hit(w, lower) for w in CANCEL_WORDS)
            if confirm_hit and cancel_hit:
                # Genuinely ambiguous ("stop that and do it") — ask,
                # never guess, with a parked PowerShell on the line.
                return None
            if confirm_hit:
                return ("confirm_pending", None)
            if cancel_hit:
                return ("cancel_pending", None)
        match = self.tools.match(user_input)
        if not match:
            return None
        tool, arg = match
        if self.tools.permission(tool) == "confirm":
            return ("confirm", (tool, arg))
        return ("safe", (tool, arg))

    # ── V6 Track C: COMPANION INTEGRATION ──────────────────────
    def _people_action(self, user_input):
        """
        V6 C2: introductions, person questions, fact learning and
        the pending-confirm lifecycle.  V6 C3: statements about the
        Architect ("my project is X", "call me Y") learn onto the
        architect record.  Returns ("commit", cand, change, fact) /
        ("stage", cand) / ("confirm_pending", staged) /
        ("cancel_pending", None) / ("who_is", record) /
        ("who_is_attr", record, keywords, frame) / ("fact",
        record, fact) / ("architect_fact", fact) /
        ("architect_alias", name, ok) / None.  Unknown people answer
        None — honest ignorance speaks instead of invention.
        """
        try:
            from ukft_people import PeopleModel, extract_introduction, \
                learn_current_user
        except Exception:
            return None
        try:
            lower = user_input.strip().lower()
            # Finding #4: read the staged proposal model when this is a
            # manifest turn (exact same-turn view); direct calls fall back
            # to a fresh load.
            people = getattr(self, "_staged_people", None)
            if people is None:
                people = PeopleModel()
            if people.pending():
                confirm_hit = any(_consent_hit(w, lower)
                                  for w in CONFIRM_WORDS)
                cancel_hit = any(_consent_hit(w, lower)
                                 for w in CANCEL_WORDS)
                if confirm_hit and cancel_hit:
                    return None
                if confirm_hit:
                    return ("confirm_pending", people.pending())
                if cancel_hit:
                    return ("cancel_pending", None)
            # First-person facts bind to this partition's speaker.
            current = learn_current_user(user_input)
            if current:
                kind, val = current
                rec = people.ensure_current(self.current_person_key)
                people.note_mention(rec["key"])
                if kind == "display":
                    ok = people.set_display(rec["key"], val)
                    return ("current_display", val, ok)
                if kind == "alias":
                    ok = people.add_alias(rec["key"], val)
                    return ("current_alias", val, ok)
                people.learn_fact(rec["key"], val)
                return ("current_fact", val)
            cand = extract_introduction(user_input)
            if cand:
                if cand["confidence"] == "high":
                    rec, change = people.commit(
                        cand["name"], cand["relation"])
                    fact = None
                    for _rec, f in people.learn_fact_from_text(user_input):
                        if _rec["key"] == rec["key"]:
                            fact = f
                            break
                    return ("commit", cand, change, fact)
                if not people.stage(cand["name"], cand["relation"],
                                    user_input):
                    # A slot is already waiting: re-ask it instead of
                    # silently discarding it (tools-pattern refusal).
                    old = people.pending() or {}
                    return ("stage", {"name": old.get("name", "?"),
                                      "relation": old.get("relation",
                                                          "?")})
                return ("stage", cand)
            learned = people.learn_fact_from_text(user_input)
            if learned:
                rec, fact = learned[0]
                people.note_mention(rec["key"])
                return ("fact", rec, fact)
            who = self._people_question(user_input, people)
            if who is not None:
                if isinstance(who, tuple) and who \
                        and who[0] == "who_is_attr":
                    return who
                return ("who_is", who)
            for display in people.names():
                if re.search(r"\b" + re.escape(display.lower()) + r"\b",
                             lower):
                    people.note_mention(display)
            return None
        except Exception:
            return None

    def _people_question(self, user_input, people):
        """A question about someone KNOWN returns the record, else None."""
        from ukft_people import normalize_person_question
        lower = normalize_person_question(user_input).strip(" ?.")
        # V6 C3: "who am i" is the Architect asking after themselves.
        # G3: so is "what is my name" (missed live 17 Sept 2026 — it
        # fell to diary recall and quoted old chatter instead).
        if re.match(r"^who am i\b", lower):
            try:
                return people.ensure_current(self.current_person_key)
            except Exception:
                return None
        if re.match(r"^(?:what is|whats|what's)\s+my\s+name\b", lower):
            try:
                return people.ensure_current(self.current_person_key)
            except Exception:
                return None
        if re.match(r"^(?:what do you know about|tell me about)\s+me\b",
                    lower):
            try:
                return people.ensure_current(self.current_person_key)
            except Exception:
                return None
        queries = []
        m = re.match(r"^who\s+(?:is|are|was|were)\s+(.+)$", lower)
        if m:
            queries.append(m.group(1))
        m = re.match(r"^(.+?)\s+who\s+(?:is|are|was|were)\s+"
                     r"(?:he|she|they|it)$", lower)
        if m:
            queries.append(m.group(1))
        m = re.match(r"^(?:tell me (?:more )?about|what can you tell me "
                     r"about|what do you know about)\s+(.+)$", lower)
        if m:
            queries.append(m.group(1))
        # Finding #6: fact/attribute questions naming a known person
        # ("what does sarah like", "what is sarah's favorite food",
        # "where does sarah live", "how old is sarah"). The assembled
        # `facts` field holds these answers but nothing reads it; the
        # narrowest seam is this existing known-person lookup. The frame
        # yields the name plus attribute keywords; only a KNOWN record
        # claims the turn (unknown referents return None, so non-person
        # questions are untouched), and the answer path matches the
        # keywords against held facts with an honest decline when the
        # requested attribute is absent.
        frame = _match_person_fact_frame(lower)
        if frame is not None:
            _fname, _keywords, _flabel = frame
            hit = people.who_is(_fname)
            if hit is not None:
                return ("who_is_attr", hit, _keywords, _flabel)
        for q in queries:
            hit = people.who_is(q)
            if hit is not None:
                return hit
        # Relation reference ("my sister", "my wife's birthday"):
        # find who holds that relation. The asker is the Architect,
        # so "my X" means the Architect's X (missed live 17 Sept
        # 2026: "who my sister is" fell to honest ignorance while
        # Maya sat in people).
        try:
            from ukft_people import REL_RE, REL_NORMALIZE
            m = re.search(r"\bmy (" + REL_RE + r")\b", lower)
            if m:
                want = REL_NORMALIZE.get(m.group(1).lower(),
                                         m.group(1).lower())
                cands = [r for k, r in people.people.items()
                         if k != self.current_person_key and any(
                             rel.get("relation") == want
                             and rel.get("until") is None
                             for rel in r.get("relationships", []))]
                if cands:
                    cands.sort(key=lambda r: (-r.get("mentions", 0),
                                              r.get("first_met", 0)))
                    return cands[0]
        except Exception:
            pass
        return None

    def _answer_people(self, action):
        """Template speech for people actions — never trigram drift."""
        try:
            from ukft_people import PeopleModel
            from ukft_time import TimeContext
            days = TimeContext()
            kind = action[0]
            if kind == "commit":
                _k, cand, change, fact = action
                rec = PeopleModel().who_is(cand["name"])
                date = days.pretty_day(rec["first_met"])
                if change == "updated":
                    olds = [r["relation"] for r in rec["relationships"]
                            if r["until"] is not None]
                    was = olds[-1] if olds else "something else"
                    text = (f"Noted — {rec['display']} is now your "
                            f"{cand['relation']} (was {was}). History kept.")
                elif change == "same":
                    text = (f"I remember — {rec['display']} is your "
                            f"{cand['relation']}, you introduced us "
                            f"on {date}.")
                else:
                    text = (f"Noted — {rec['display']} is your "
                            f"{cand['relation']}. I will remember "
                            f"{rec['display']} from {date}.")
                if fact:
                    text += f" Also noted — {rec['display']} {fact}."
                terms = rec["display"].split() \
                    + cand["relation"].split()
                if fact:
                    terms += fact.split()
                return self._mouth_last("[AURA]: " + text, terms)
            if kind == "stage":
                _k, cand = action
                return ("[AURA]: Just to confirm — is "
                        f"{cand['name']} your {cand['relation']}? "
                        "Say confirm or cancel.")
            if kind == "confirm_pending":
                staged = action[1]
                people = PeopleModel()
                rec, _c = people.commit(
                    staged["name"], staged["relation"],
                    first_met=staged["ts"])
                people.clear_pending()
                return ("[AURA]: Confirmed — "
                        f"{rec['display']} is your {staged['relation']}. "
                        "I will remember.")
            if kind == "cancel_pending":
                PeopleModel().clear_pending()
                return "[AURA]: Dropped — I will not remember that."
            if kind == "who_is":
                rec = action[1]
                if rec["key"] == self.current_person_key:
                    text = PeopleModel().describe_current(
                        rec, None,
                        days.pretty_day(rec["first_met"]),
                        creator=(rec["key"] == "architect"))
                    return self._mouth_last(
                        "[AURA]: " + text,
                        rec["display"].split() + ["you"])
                try:
                    from ukft_context import thread_line
                    thread = []
                    try:
                        thread = list(self.memory.recent_topic(3) or [])
                    except Exception:
                        pass
                    people = PeopleModel()
                    text = people.describe(
                        rec, days.pretty_day(rec["first_met"]))
                    about = set(rec["key"].split()) | set(
                        rec["display"].lower().split())
                    try:
                        about |= set((people.current_relation(rec)
                                     or "").split())
                    except Exception:
                        pass
                    line = thread_line(thread, about=about)
                    if line:
                        text += " " + line
                    terms = rec["display"].split() + thread
                    try:
                        terms += (people.current_relation(rec) or "").split()
                    except Exception:
                        pass
                    return self._mouth_last("[AURA]: " + text, terms)
                except Exception:
                    return "[AURA]: " + PeopleModel().describe(
                        rec, days.pretty_day(rec["first_met"]))
            if kind == "who_is_attr":
                _k, rec, keywords, frame = action
                people = PeopleModel()
                match = people.match_attr_fact(rec["key"], keywords)
                if match:
                    text = f"{rec['display']} {match}."
                else:
                    held = [f["fact"] for f in rec.get("facts", [])[:3]]
                    if held:
                        text = (f"I don't have that noted for "
                                f"{rec['display']} — my notes: "
                                f"{'; '.join(held)}.")
                    else:
                        text = (f"I don't have that noted for "
                                f"{rec['display']} — no notes yet.")
                return self._mouth_last(
                    "[AURA]: " + text,
                    rec["display"].split() + list(keywords or []))
            if kind == "fact":
                _k, rec, fact = action
                text = f"Noted — {rec['display']} {fact}."
                return self._mouth_last(
                    "[AURA]: " + text,
                    rec["display"].split() + fact.split())
            if kind == "current_fact":
                fact = action[1]
                if fact.startswith("project: "):
                    return self._mouth_last(
                        "[AURA]: Your project is "
                        f"{fact[len('project: '):]} — noted. "
                        "I will remember.",
                        ["project"] + fact[len("project: "):].split())
                if fact.startswith("note: "):
                    return self._mouth_last(
                        f"[AURA]: Noted — {fact[len('note: '):]}.",
                        fact[len("note: "):].split())
                if fact.startswith("calls me "):
                    pet = fact[len("calls me "):]
                    return self._mouth_last(
                        f"[AURA]: Noted — {pet} it is. "
                        f"I'll answer to it.",
                        [pet])
                # Facts store third-person ("likes X"); speech to
                # the Architect is second-person ("you like X").
                from ukft_people import second_person as _2nd
                spoken = _2nd(fact)
                return self._mouth_last(
                    f"[AURA]: Noted — you {spoken}. I'll remember.",
                    ["you"] + spoken.split())
            if kind == "current_display":
                _k, name, ok = action
                if ok:
                    return f"[AURA]: Your name is {name} — I will remember."
                return f"[AURA]: I already know you as {name}."
            if kind == "current_alias":
                _k, name, ok = action
                if ok:
                    return f"[AURA]: Noted — I'll call you {name}."
                return f"[AURA]: {name} is already one of your names."
            return "[AURA]: Noted."
        except Exception:
            return "[AURA]: I will remember that."

    def _assemble_context(self, user_input):
        """V6 C5: the pre-answer gatherer.  Best-effort, never fatal."""
        try:
            from ukft_context import assemble
            from ukft_agenda import AgendaModel
            from ukft_episodic import EpisodicMemory
            from ukft_gaps import KnowledgeGaps
            from ukft_people import PeopleModel
            from ukft_self import DriveState
            # Finding #4: same-turn readers see staged proposal state.
            _as_people = getattr(self, "_staged_people", None)
            if _as_people is None:
                _as_people = PeopleModel()
            _as_agenda = getattr(self, "_staged_agenda", None)
            if _as_agenda is None:
                _as_agenda = AgendaModel()
            return assemble(
                user_input, people=_as_people,
                episodes=EpisodicMemory().all(), memory=self.memory,
                gaps=KnowledgeGaps().top_gaps(3),
                drives=DriveState().allocation(),
                threads=_as_agenda.opened(),
                current_person_key=self.current_person_key)
        except Exception:
            return {}

    def _self_action(self, user_input):
        """
        V6 C7: constitution refusals and confidence questions.
        Returns ("floor", reason) / ("confidence", topic) /
        ("confidence_ask", None) / None.
        """
        try:
            from ukft_self import floor_check
        except Exception:
            return None
        try:
            reason = floor_check(user_input)
            if reason:
                return ("floor", reason)
            lower = re.sub(r"\s+", " ",
                           user_input.strip().lower()).strip(" ?.")
            m = re.match(r"^(?:how confident|how sure) are you about "
                         r"(.+)$", lower)
            if m and m.group(1).strip():
                return ("confidence", m.group(1).strip())
            m = re.match(r"^are you (?:confident|sure) about (.+)$",
                         lower)
            if m and m.group(1).strip():
                return ("confidence", m.group(1).strip())
            # Fix-pass: a bare confidence question ("how confident
            # are you") fell through to the status audit.  Ask for
            # the topic instead of auditing irrelevantly.
            if re.match(r"^(?:how confident|how sure) are you$",
                        lower) or re.match(
                    r"^are you (?:confident|sure)$", lower):
                return ("confidence_ask", None)
            return None
        except Exception:
            return None

    def _answer_self(self, action):
        """Template speech for the self-model — never trigram drift."""
        try:
            from aura_bus import read as bus_read
            from aura_constants import CONTRADICTIONS, FIELD_STATS, \
                INFERENCES, KNOWLEDGE_GRAPH
            from ukft_gaps import KnowledgeGaps
            from ukft_question import QuestionUnderstanding
            from ukft_self import read_field_stats, report
        except Exception:
            return "[AURA]: I cannot look at myself right now."
        try:
            if action[0] == "floor":
                return "[AURA]: " + action[1]
            if action[0] == "confidence_ask":
                return ("[AURA]: Confident about what? Name something "
                        "I hold and I will show you.")
            topic = action[1]
            conf, proofs = None, 0
            try:
                qa = QuestionUnderstanding(
                    graph_path=KNOWLEDGE_GRAPH,
                    inferences_path=INFERENCES)
                nodes, _left = qa.resolve(topic)
                if nodes:
                    edges = qa._combined_edges()
                    hits = [c for (_r, x, y), (c, _o)
                            in edges.items() if x in nodes or y in nodes]
                    if hits:
                        conf, proofs = max(hits), len(hits)
            except Exception:
                conf, proofs = None, 0
            tension, ncount = read_field_stats(FIELD_STATS)
            try:
                curios = [w for (_k, w), _e
                          in KnowledgeGaps().top_gaps(3)]
            except Exception:
                curios = []
            try:
                cont = sum(1 for line in bus_read(
                    CONTRADICTIONS).splitlines()
                    if line.startswith("CONTRADICTION: "))
            except Exception:
                cont = 0
            text = report(
                topic=topic, confidence=conf, proofs=proofs,
                tension=tension, nodes=ncount, curiosities=curios,
                contradictions=cont)
            return self._mouth_last(
                "[AURA]: " + text, topic.split())
        except Exception:
            return "[AURA]: I cannot look at myself right now."

    def _agenda_action(self, user_input):
        """
        V6 C6: intention statements, closings, story requests.
        Returns ("agenda_add", thread, new) / ("agenda_close",
        thread) / ("agenda_miss", words) / ("agenda_story", None)
        / None.
        """
        try:
            from ukft_agenda import AgendaModel, extract_close, \
                extract_intention, is_story_request
        except Exception:
            return None
        try:
            # Finding #4: staged shared proposal model (see manifest).
            agenda = getattr(self, "_staged_agenda", None)
            if agenda is None:
                agenda = AgendaModel()
            if is_story_request(user_input):
                return ("agenda_story", None)
            topic = extract_intention(user_input)
            if topic:
                thread, new = agenda.open(topic)
                return ("agenda_add", thread, new)
            words = extract_close(user_input)
            if words:
                hit = agenda.close(words)
                if hit is not None:
                    return ("agenda_close", hit)
                return ("agenda_miss", words)
            return None
        except Exception:
            return None

    def _answer_agenda(self, action):
        """Template speech for agenda turns — never trigram drift."""
        try:
            from ukft_agenda import AgendaModel
        except Exception:
            return "[AURA]: I will hold that thought."
        try:
            kind = action[0]
            if kind == "agenda_add":
                _k, thread, new = action
                if new:
                    return self._mouth_last(
                        "[AURA]: Noted — I'll hold that thread: "
                        f"{thread['topic']}.",
                        thread["topic"].split())
                return self._mouth_last(
                    "[AURA]: Still holding that one: "
                    f"{thread['topic']}.",
                    thread["topic"].split())
            if kind == "agenda_close":
                thread = action[1]
                left = len(AgendaModel().opened())
                tail = "Slate clean." if left == 0 else \
                    f"{left} still open."
                return self._mouth_last(
                    f"[AURA]: Closed — {thread['topic']}. {tail}",
                    thread["topic"].split())
            if kind == "agenda_miss":
                return ("[AURA]: I am not holding anything about "
                        f"{action[1]}.")
            if kind == "agenda_story":
                from ukft_episodic import EpisodicMemory
                import time as _time
                agenda = AgendaModel()
                story = agenda.story(
                    EpisodicMemory().all(), _time.time())
                terms = []
                for t in agenda.opened():
                    terms += t["topic"].split()
                return self._mouth_last("[AURA]: " + story, terms)
            return "[AURA]: Noted."
        except Exception:
            return "[AURA]: I will hold that thought."

    def _belief_action(self, user_input):
        """
        V6 C10: assertion contests and the pending lifecycle.
        Returns ("contest", claim, prior-edge) / ("confirm_belief",
        staged) / ("cancel_belief", staged) / ("hold", claim) /
        None.  Introductions, architect notes, intentions and
        stories own their turns — belief never poaches them.
        Staging happens in the answer branch (post-selection), so
        a lost competition never parks a ghost pending.
        """
        try:
            from aura_constants import INFERENCES, KNOWLEDGE_GRAPH
            from ukft_agenda import extract_intention, is_story_request
            from ukft_belief import BeliefStore, detect_assertion, \
                find_conflict
            from ukft_people import extract_introduction, learn_current_user
            from ukft_question import QuestionUnderstanding
            from ukft_teach import detect_correction
        except Exception:
            return None
        try:
            lower = user_input.strip().lower()
            # Finding #4: staged shared proposal model (see manifest).
            store = getattr(self, "_staged_beliefs", None)
            if store is None:
                store = BeliefStore()
            if store.pending():
                confirm_hit = any(_consent_hit(w, lower)
                                  for w in CONFIRM_WORDS)
                cancel_hit = any(_consent_hit(w, lower)
                                 for w in CANCEL_WORDS)
                if confirm_hit and cancel_hit:
                    return None
                if confirm_hit:
                    return ("confirm_belief", store.pending())
                if cancel_hit:
                    return ("cancel_belief", store.pending())
            if (learn_current_user(user_input)
                    or extract_introduction(user_input)
                    or extract_intention(user_input)
                    or is_story_request(user_input)
                    or detect_correction(user_input)):
                return None
            claim = detect_assertion(user_input)
            if not claim:
                return None
            try:
                qa = QuestionUnderstanding(
                    graph_path=KNOWLEDGE_GRAPH,
                    inferences_path=INFERENCES)
                edges = qa._combined_edges()
            except Exception:
                edges = {}
            prior = find_conflict(claim["rel"], claim["x"],
                                  claim["y"], edges)
            if prior:
                return ("contest", claim, prior)
            # Finding #4: staged hold lands on the shared proposal model;
            # the winner-gated commit replays it post-selection.
            store.hold(claim["rel"], claim["x"], claim["y"])
            return ("hold", claim)
        except Exception:
            return None

    def _answer_belief(self, action):
        """Template speech for belief turns — never trigram drift."""
        try:
            from ukft_answer import _claim as _rel_claim
            from ukft_belief import BeliefStore, claim_text
            from ukft_time import TimeContext
        except Exception:
            return "[AURA]: Noted."
        try:
            kind = action[0]
            store = BeliefStore()
            days = TimeContext()
            if kind == "contest":
                _k, claim, prior = action
                er, a, b, conf, origin = prior
                if not store.stage(claim["rel"], claim["x"],
                                   claim["y"],
                                   prior=f"{er}({a}, {b}) conf "
                                         f"{conf:.2f} [{origin}]"):
                    # A contest is already waiting: name it instead
                    # of silently replacing it (tools-pattern).
                    held = store.pending() or {}
                    if held:
                        from ukft_belief import claim_text as _ct
                        return (f"[AURA]: You still have "
                                f"'{_ct(held.get('rel', ''), held.get('x', ''), held.get('y', ''))}' "
                                "waiting — say 'confirm' to overwrite or "
                                "'cancel' to drop it first.")
                mine = claim_text(claim["rel"], claim["x"],
                                  claim["y"])
                try:
                    theirs = _rel_claim(er, a, b)
                except Exception:
                    theirs = f"{a} relates to {b}"
                return (f"[AURA]: That contradicts what I hold — "
                        f"{theirs} (conf {conf:.2f}, {origin}). "
                        f"Overwrite with '{mine}'? "
                        "Say confirm or cancel.")
            if kind == "confirm_belief":
                staged = action[1]
                store.confirm_contest(staged)
                mine = claim_text(staged["rel"], staged["x"],
                                  staged["y"])
                return ("[AURA]: I think the graph is right, but I'll "
                        "go along for now — holding "
                        f"'{mine}' as contested. Vault evidence "
                        "against it would change my mind back.")
            if kind == "cancel_belief":
                store.cancel_contest(action[1])
                return "[AURA]: Kept — the stored evidence stands."
            if kind == "hold":
                claim = action[1]
                mine = claim_text(claim["rel"], claim["x"],
                                  claim["y"])
                return self._mouth_last(
                    f"[AURA]: Noted — I'll hold that: {mine}.",
                    mine.split())
            return "[AURA]: Noted."
        except Exception:
            return "[AURA]: Noted."

    def _belief_verify(self, plan):
        """
        V6 C10: VERIFY consults held beliefs when the graph is
        silent.  Provenance-stamped provisional answers — never
        confabulation, never overriding proof.
        """
        try:
            from ukft_belief import BeliefStore
            from ukft_time import TimeContext
        except Exception:
            return None
        try:
            if plan.get("intent") != "VERIFY":
                return None
            if plan.get("verified") or plan.get("results"):
                return None
            # Finding #4: VERIFY consults staged proposal beliefs.
            store = getattr(self, "_staged_beliefs", None)
            if store is None:
                store = BeliefStore()
            x, y = plan.get("x"), plan.get("y")
            rec = None
            if x and y:
                rec = store.match(x, y, plan.get("relation"))
            if rec is None:
                rec = store.match_words(plan.get("unresolved", []))
            if rec is None:
                return None
            day = TimeContext().pretty_day(rec["ts"])
            from ukft_belief import claim_text
            mine = claim_text(rec["rel"], rec["x"], rec["y"])
            terms = mine.split()
            if rec["status"] == "contested":
                return self._mouth_last(
                    f"You told me {mine} ({day}), over "
                    f"{rec['prior']}. I hold it provisionally — "
                    "I still think the graph is right.",
                    terms)
            return self._mouth_last(
                f"You told me {mine} ({day}). The graph is "
                "silent on it — I hold it provisionally.",
                terms)
        except Exception:
            return None

    def _mouth_last(self, body, key_terms, kind=None):
        """
        V6 C9: the mouth is the last output stage for every
        memory-backed answer — proof, people, recall, belief,
        agenda, confidence.  Verified fluency wins; anything
        else (dead daemon, timeout, drift) returns the template
        unchanged.  Protocol speech (confirm/cancel questions)
        and guesses never come here: consent wording stays exact
        and drift has nothing to verify against.
        V7 F1: after the mouth, the register dresses proof
        answers with a varied warm opener (kind="proof").
        Every other kind passes through — the hook is reserved
        for F4 conversational policy.
        V7 F5: the mouth works per-claim now (survivors assemble,
        fallen claims speak template) — same call, finer unit.
        """
        try:
            from ukft_mouth import Mouth
        except Exception:
            return body
        try:
            terms = [t for t in (key_terms or []) if t]
            if not terms:
                return self._register_style(body, kind)
            mouth = Mouth()
            # Fakes and older swaps may only speak whole sentences.
            speak = getattr(mouth, "speak_claims", None) \
                or mouth.speak
            return self._register_style(
                speak(body, terms) or body, kind)
        except Exception:
            return body

    def _register_style(self, body, kind):
        """
        V7 F1 register: variety + warmth, never content.  V7 F3:
        affect tints the opener pool (bright/cool) or quiets her
        (hot field) — all from measured state, all neutral when
        her stores are unreadable.
        """
        if not kind:
            return body
        try:
            from ukft_affect import read_state, tone_for
            from ukft_register import Register
            try:
                family, quiet = tone_for(read_state())
            except Exception:
                family, quiet = None, False
            return Register().style(body, kind, family=family,
                                    quiet=quiet)
        except Exception:
            return body

    def _mouth_speak(self, body, plan, kind=None):
        """
        Proof answers enter the mouth-last stage with their proof
        facts as the verification terms.  kind="proof" lets the
        V7 F1 register dress the winner afterwards.
        """
        try:
            from ukft_answer import _claim
        except Exception:
            return body
        try:
            facts = []
            for (rel, x, y, _conf, _origin) in plan.get("results", []):
                try:
                    facts.append(_claim(rel, x, y))
                except Exception:
                    facts.append(f"{x} relates to {y}")
            if not facts and plan.get("op") == "verify" \
                    and plan.get("verified") is True:
                # A verified claim carries no result rows — the
                # verified edge itself is the proof fact (mouth
                # terms and register grounding alike).
                try:
                    facts.append(_claim(plan.get("relation") or "is_a",
                                        plan["x"], plan["y"]))
                except Exception:
                    facts = []
            if not facts:
                return body
            return self._mouth_last(body, facts, kind=kind)
        except Exception:
            return body

    def _teach_action(self, user_input):
        """
        V6 C8: corrections ("no", "actually X is Y"), counter-claims
        routed through belief verification, and lesson reviews.
        Returns ("teach_bare", prev_q, prev_a) / ("contest", claim,
        prior) [rendered by the belief branch] / ("teach_held",
        claim) / ("teach_noted", text, fact) / ("teach_review", None) /
        None.  Counter-claims about known people also teach person
        facts in passing — addition, never silent erasure.  Finding #8:
        `fact` is (display, fact) when the counter-claim taught a
        person fact in passing (so the acknowledgement can say exactly
        what was retained), else None (banked lesson text only).
        """
        try:
            from aura_bus import read as bus_read
            from aura_constants import OUTPUT_FILE
            from ukft_teach import LessonLedger, detect_correction, \
                is_review_request
        except Exception:
            return None
        try:
            if is_review_request(user_input):
                return ("teach_review", None)
            hit = detect_correction(user_input)
            if not hit:
                return None
            kind, text = hit
            # Finding #4: staged shared proposal models (see manifest).
            ledger = getattr(self, "_staged_lessons", None)
            if ledger is None:
                ledger = LessonLedger()
            prev_q, prev_a = "", ""
            try:
                if self.memory.turns:
                    prev_q = self.memory.turns[-1].get("query", "")
                prev_a = bus_read(OUTPUT_FILE).replace(
                    "[AURA]: ", "", 1)[:120]
            except Exception:
                pass
            if kind == "bare":
                ledger.record(
                    "architect", prev_q[:60],
                    "corrected with no counter-claim (I had said: "
                    + prev_a[:80] + ")")
                return ("teach_bare", prev_q, prev_a)
            claim = None
            try:
                from aura_constants import INFERENCES, KNOWLEDGE_GRAPH
                from ukft_belief import BeliefStore, detect_assertion, \
                    find_conflict
                from ukft_question import QuestionUnderstanding
                claim = detect_assertion(text)
            except Exception:
                claim = None
            try:
                from ukft_people import PeopleModel
                _tpeople = getattr(self, "_staged_people", None)
                if _tpeople is None:
                    _tpeople = PeopleModel()
                _tlearned = _tpeople.learn_fact_from_text(text)
            except Exception:
                _tlearned = []
            if claim:
                try:
                    qa = QuestionUnderstanding(
                        graph_path=KNOWLEDGE_GRAPH,
                        inferences_path=INFERENCES)
                    edges = qa._combined_edges()
                except Exception:
                    edges = {}
                prior = find_conflict(claim["rel"], claim["x"],
                                      claim["y"], edges)
                if prior:
                    return ("contest", claim, prior)
                _tstore = getattr(self, "_staged_beliefs", None)
                if _tstore is None:
                    from ukft_belief import BeliefStore
                    _tstore = BeliefStore()
                _tstore.hold(
                    claim["rel"], claim["x"], claim["y"],
                    src="architect-correction")
                ledger.record("architect", claim["x"],
                              "corrected to: " + text[:120])
                return ("teach_held", claim)
            ledger.record("architect", prev_q[:60],
                          "noted correction: " + text[:120])
            # Finding #8: carry what was actually retained so speech
            # cannot overstate. A passed-on person fact answers later
            # turns (person store); otherwise only lesson text was
            # banked (reviewable, never answer-truth).
            _tfact = None
            try:
                if _tlearned:
                    _trec, _ff = _tlearned[0]
                    _tfact = (_trec.get("display", ""), _ff)
            except Exception:
                _tfact = None
            return ("teach_noted", text, _tfact)
        except Exception:
            return None

    def _answer_teach(self, action):
        """Template speech for teaching turns — never trigram drift."""
        try:
            from aura_bus import read as bus_read
            from aura_constants import ACTION_LOG
            from ukft_teach import LessonLedger, render_review, \
                review_tools
        except Exception:
            return "[AURA]: Noted."
        try:
            kind = action[0]
            ledger = LessonLedger()
            if kind == "teach_bare":
                prev_a = action[2]
                bit = f" (I had said: {prev_a[:80]})" if prev_a else ""
                return ("[AURA]: Fair — tell me what's right and I'll "
                        f"hold it.{bit}")
            if kind == "teach_held":
                claim = action[1]
                from ukft_belief import claim_text
                mine = claim_text(claim["rel"], claim["x"],
                                  claim["y"])
                return self._mouth_last(
                    "[AURA]: Noted — I had it wrong. I'll hold "
                    f"that: {mine}.",
                    mine.split())
            if kind == "teach_noted":
                # Finding #8: the acknowledgement says exactly what was
                # retained. A passed-on person fact WILL answer later
                # turns; banked-only text will not (reviewable, never
                # answer-truth) and must not claim otherwise.
                _tfact = action[2] if len(action) > 2 else None
                if _tfact:
                    _tdisp, _ff = _tfact
                    return self._mouth_last(
                        "[AURA]: Noted — "
                        f"{_tdisp} {_ff}.",
                        _tdisp.split() + str(_ff or "").split())
                return ("[AURA]: Noted — banked as a lesson, but I "
                        "can't answer from it yet. Give it to me as "
                        "a plain fact and I'll hold it.")
            if kind == "teach_review":
                try:
                    fresh = review_tools(bus_read(ACTION_LOG), ledger)
                except Exception:
                    fresh = 0
                text = render_review(ledger)
                if fresh:
                    text += f" ({fresh} new from tool outcomes.)"
                return "[AURA]: " + text
            return "[AURA]: Noted."
        except Exception:
            return "[AURA]: Noted."

    def _recall_answer(self, plan, user_input=""):
        """
        V6 C4: episodic recall by time, person, and topic.  Runs
        inside the reasoning layer — proof still wins (recall only
        fills proven-nothing), and None returns the question to
        the normal pipeline untouched.
        """
        try:
            from ukft_episodic import EpisodicMemory
            from ukft_people import PeopleModel
            from ukft_recall import recall_person, recall_time, recall_topic
            from ukft_time import TimeContext, episodes_in_window
        except Exception:
            return None
        # M14: every recall return below records its contributing
        # episodes (most-relevant-first) for the eligibility policy.
        # Return TEXT is unchanged — existing callers/tests unaffected.
        self._last_recall_hits = []
        self._last_recall_kind = None
        try:
            if plan.get("intent") not in ("WHAT", "WHO", "UNKNOWN"):
                return None
            if plan.get("results"):
                return None
            # Fix-pass: social acts (thanks, farewells) and bedtime
            # imperatives ("tell me a story/joke") are never diary
            # questions — recalling the log at them parrots chatter
            # ("thanks Jo" answered with her dossier).  None returns
            # them to voice/association untouched.
            try:
                from ukft_recall import is_social_act, is_story_request
            except Exception:
                is_social_act = is_story_request = None
            if is_social_act is not None and is_social_act(user_input):
                return None
            if is_story_request is not None and is_story_request(user_input):
                return None
            eps = EpisodicMemory().all()
            tw = plan.get("time_window")
            # Finding #4: recall sees staged proposal people.
            people = getattr(self, "_staged_people", None)
            if people is None:
                people = PeopleModel()
            if tw:
                # Aura's old reply copies are speech output, not lived
                # events that may influence a later answer. Topic/person
                # recall already excludes them; time recall must too.
                time_eps = [e for e in eps
                            if str(e.get("kind", "") or "") != "reply"]
                text = recall_time(time_eps, tw, people=people)
                if text is None:
                    return None
                words = [w for w in (plan.get("unresolved", []) or [])
                         + (plan.get("x") or "").split()
                         if len(w) > 2]
                # M14: TIME summaries quote no episode as fact — the
                # window itself is the provenance (most-recent-first).
                self._last_recall_kind = "time"
                try:
                    _win = episodes_in_window(
                        time_eps, tw["start"], tw["end"]) or []
                except Exception:
                    _win = []
                self._last_recall_hits = list(reversed(_win))
                return self._mouth_last(text, words or None) or text
            thread = []
            try:
                thread = list(self.memory.recent_topic(3) or [])
            except Exception:
                pass
            x = plan.get("x") or ""
            hit = people.who_is(x)
            if hit is None:
                for w in plan.get("unresolved", []):
                    hit = people.who_is(w)
                    if hit is not None:
                        break
            if hit is not None:
                if hit["key"] == self.current_person_key:
                    text = people.describe_current(
                        hit, eps, TimeContext().pretty_day(hit["first_met"]),
                        creator=(hit["key"] == "architect"))
                    # M14: a people-record describe quotes the people
                    # record (M4-owned), not episode content.
                    self._last_recall_kind = "person-record"
                    self._last_recall_hits = []
                else:
                    text = recall_person(
                        hit, eps, TimeContext().pretty_day(hit["first_met"]),
                        thread=thread)
                    # M14: person traces ARE episode-asserted — match
                    # the pre-mouth text to its quoted episodes.
                    self._last_recall_kind = "person-traces"
                    self._last_recall_hits = _m14_match_hits(eps, text)
                terms = hit["key"].split() + hit["display"].split() \
                    + (people.current_relation(hit) or "").split() \
                    + list(thread)
                return self._mouth_last(text, terms) or text
            words = list(plan.get("unresolved", []))
            if not words and x:
                words = x.split()
            text = recall_topic(eps, words, echo=user_input)
            if text is None:
                return None
            # M14: topic recall asserts episode content — match the
            # pre-mouth text (robust to mouth paraphrase downstream).
            self._last_recall_kind = "topic"
            self._last_recall_hits = _m14_match_hits(eps, text)
            return self._mouth_last(text, words) or text
        except Exception:
            return None

    # ── V5 Track R: REASONING INTEGRATION ─────────────────────────
    IDENTITY_TERMS = ("you", "your", "yourself", "youre", "aura")

    def _identity_question(self, lower):
        """
        Self-referential questions belong to the identity core, not to
        the knowledge graph — the graph knows the world, the ego knows
        itself.  The "who are" arm needs its object: bare "who are
        the sons of Japheth" asks about the WORLD (it once fell to
        association because "who are" matched the identity gate).
        """
        words = set(re.findall(r"[a-z]+", lower))
        if words & set(self.IDENTITY_TERMS):
            return True
        if re.search(r"who are (you|your)\b", lower):
            return True
        if re.search(r"what are (you|your)\b", lower):
            return True
        return False

    def _reasoning_answer(self, user_input, social=False, query=None):
        """
        Run the V5 R-track (R4 -> R5 -> R6) over the knowledge graph.
        Returns a proof-seeded or honest-ignorance answer body, or
        None when the associative layers should answer instead.
        The reasoning state files must exist — sandboxed tests and
        fresh workspaces simply keep the associative behaviour.
        `social` (voice claimed a greeting/identity/status turn)
        suppresses diary recall only — a greeting is answered as a
        greeting, never as a memory dump; graph proof still speaks.
        `query` (G7) asks the graph about the resolved referent
        instead of the raw follow-up; None keeps the old behavior.
        """
        self.last_m3 = _fresh_m3()
        try:
            from aura_constants import INFERENCES, KNOWLEDGE_GRAPH
            if not (os.path.exists(KNOWLEDGE_GRAPH)
                    and os.path.exists(INFERENCES)):
                self._last_reasoning_plan = None
                # Finding #8: the graph files gate the R-track, but a
                # held correction belief needs no graph. Plan the
                # question (pure parsing — no files touched) and let a
                # matching belief answer VERIFY provisionally exactly as
                # the graph-present path would; otherwise keep the
                # associative behaviour (None) unchanged. Fresh users
                # and fresh sandboxes have no graph files, so without
                # this an accepted correction could never answer.
                try:
                    from ukft_question import QuestionUnderstanding
                    _qa8 = QuestionUnderstanding(
                        graph_path=KNOWLEDGE_GRAPH,
                        inferences_path=INFERENCES)
                    _plan8 = _qa8.run(_qa8.plan(user_input))
                    _bans8 = self._belief_verify(_plan8)
                    if _bans8 is not None:
                        self.last_m3 = {
                            "reasoning_present": True,
                            "reasoning_kind": "belief-provisional",
                            "vault_present": False,
                            "priority_applied": False,
                            "priority_reason": None,
                        }
                        return _bans8
                except Exception:
                    pass
                return None
            from ukft_answer import AnswerComposer
            from ukft_gaps import KnowledgeGaps
            from ukft_question import QuestionUnderstanding

            # A referential follow-up ("tell me more") has no content of
            # its own — working memory carries the topic, so the graph
            # gets asked about THAT topic.  Proofs must not lose to
            # association just because the follow-up is elliptical.
            # Social turns keep their own words: a greeting answered
            # with a shrug about the carried topic is nonsense.
            # G7: an explicit resolved query (pronouns bound to the
            # thread) outranks the generic topic rewrite.
            if query is None:
                query = user_input
                if not social and self.memory.is_referential(user_input):
                    topic = self.memory.recent_topic(3)
                    if topic:
                        query = "what is " + " ".join(topic)

            qa = QuestionUnderstanding(graph_path=KNOWLEDGE_GRAPH,
                                       inferences_path=INFERENCES)
            plan = qa.run(qa.plan(query))
            # M13: stash the executed plan — the contradiction guard
            # reads it after M1/M2/M4 without recompiling.
            self._last_reasoning_plan = plan
            # V6 C4: the diary answers what the graph cannot prove —
            # but only when it holds something (None = untouched).
            # Social turns (greetings) never recall — hello is hello.
            recall = None if social else self._recall_answer(plan,
                                                             user_input)
            # V6 C10: held beliefs answer VERIFY when the graph is
            # silent — provenance-stamped, provisional, never proof.
            belief_ans = self._belief_verify(plan)
            body = AnswerComposer(inferences_path=INFERENCES).compose(plan)
            # M14 may later withdraw the recall after M4 has classified
            # the turn. Preserve the answer that the same reasoning run
            # would otherwise have considered, so a guarded episode does
            # not turn honest ignorance into an unrelated dark fallback.
            self._last_recall_fallback = body
            # The gap behind the answer is logged either way — honest
            # ignorance is the beginning of curiosity.
            KnowledgeGaps().record_plan(plan, user_input,
                                        fallback=body is None
                                        and recall is None)
            if social and (body is None
                           or _is_honest_gap(body)):
                # Greetings greet — proof still speaks above.  A bare
                # None stays silent, but an honest gap rides along on
                # GREETING turns only ("good morning, is unix fast"
                # answers the greeting AND the question instead of
                # swallowing the question; status audits keep their
                # exact old behavior).  Pure hellos plan nothing, so
                # they stay exactly as they were.
                if body is None or getattr(
                        self.voice, "last_kind", None) != "greeting":
                    return None
                self.last_m3 = {
                    "reasoning_present": True,
                    "reasoning_kind": "honest-gap",
                    "vault_present": False,
                    "priority_applied": False,
                    "priority_reason": "social-gap-rides-greeting",
                }
                return body
            if belief_ans is not None and (
                    body is None or _is_honest_gap(body)):
                self.last_m3 = {
                    "reasoning_present": True,
                    "reasoning_kind": "belief-provisional",
                    "vault_present": False,
                    "priority_applied": False,
                    "priority_reason": None,
                }
                return belief_ans
            if recall is not None and (
                    body is None or _is_honest_gap(body)):
                self.last_m3 = {
                    "reasoning_present": True,
                    "reasoning_kind": "diary-recall",
                    "vault_present": False,
                    "priority_applied": False,
                    "priority_reason": None,
                }
                return recall
            if body is None:
                # M3 UNKNOWN-claim rule: an aux-first factual question
                # ("did my car come from France") with no proof is a
                # claim on the world.  Without answer-bearing vault
                # resonance it earns an honest gap instead of a
                # misleading quote.  Guarded narrowly: direct recall
                # instructions, voice-owned social turns, and
                # open/imperative phrasings keep their existing paths,
                # and answer-bearing resonance still speaks.
                if plan.get("intent") == "UNKNOWN" and not social \
                        and _aux_first_factual(user_input) \
                        and not _has_memory_trigger(user_input):
                    try:
                        top_u = self.engine.rank(query, top_n=1)
                    except Exception:
                        top_u = []
                    _top_bearing = (
                        bool(top_u) and _m3_answer_bearing(
                            query, top_u[0][0], top_u[0][1]))
                    # Phase 10B: autobiographical ownership is eligibility.
                    # A wrong-person bearing anchor must not suppress the
                    # honest gap here either; same-anchor compatibility only.
                    if _top_bearing and _explicit_memory_request(
                            user_input) == "autobiographical":
                        try:
                            _u_cur = (self._bundle or {}).get(
                                "current_user")
                        except Exception:
                            _u_cur = None
                        if not _m4_owned_answer_bearing(
                                query, [top_u[0]], _u_cur):
                            _top_bearing = False
                    if top_u and not _top_bearing:
                        self.last_m3 = {
                            "reasoning_present": True,
                            "reasoning_kind": "honest-gap",
                            "vault_present": True,
                            "priority_applied": True,
                            "priority_reason":
                                "honest-gap-over-association",
                        }
                        return "I do not know."
                return None
            if _is_honest_gap(body):
                # Resonance is judged on the topic actually asked about —
                # a follow-up ("tell me more") must be able to fall back
                # to what the vault holds on the carried topic.
                # Fix-pass: resonance is WHOLE-WORD ("who is zod" used
                # to resonate on "zodiac" and quote Aquarius instead
                # of staying ignorant).
                top = []
                try:
                    top = self.engine.rank(query, top_n=1)
                except Exception:
                    top = []
                try:
                    from ukft_quote import whole_word_hit
                    resonates = whole_word_hit(query, top,
                                               stop=SEED_STOP)
                except Exception:
                    resonates = bool(top)
                intent = plan.get("intent")
                # Claims the graph must prove (VERIFY / COMPARE / WHEN)
                # are always answered honestly — association must never
                # drift over them.  Open questions (WHAT / WHO / WHERE /
                # WHY / HOW_MANY) with vault resonance fall back to her
                # associative knowledge instead of a shrug; the gap is
                # already logged and drives future extraction (R6).
                if intent not in ("VERIFY", "COMPARE", "WHEN") and resonates:
                    if _aux_first_factual(user_input) \
                            and not _has_memory_trigger(user_input):
                        # Aux-first factual questions are claims: a
                        # merely subject-naming resonance must not
                        # answer them ("did my car come from France"
                        # vs a model description).  Answer-bearing
                        # resonance still speaks; direct recall
                        # instructions are untouched.
                        top_concept, top_data = top[0]
                        if _m3_answer_bearing(query, top_concept,
                                              top_data):
                            return None
                    else:
                        return None
                if intent in ("VERIFY", "COMPARE", "WHEN") \
                        and _explicit_memory_request(user_input):
                    # M3 exemption: an explicit memory request whose held
                    # answer the vault coherently carries must not lose
                    # to "I do not know" (an autobiographical purchase
                    # question with the purchase memory held).  Direct
                    # triggers need M1 relevance; inferred
                    # autobiographical readings additionally need
                    # answer-bearing residue beyond the subject title
                    # (a subject-only title match must not answer a
                    # predicate question).
                    # World-knowledge claims ("is zod a planet") are not
                    # memory requests, so their gaps stand.  None hands
                    # the turn back to the normal pipeline (vault speaks
                    # only if still eligible there).
                    held, _ = m1_filter_relevant(
                        user_input, self.engine.rank(user_input, top_n=5))
                    if _explicit_memory_request(user_input) \
                            == "autobiographical":
                        held = [(c, d) for c, d in held
                                if _m3_answer_bearing(user_input, c, d)]
                        # Phase 10B structural eligibility: M3's exemption
                        # cannot override a later-proven current-person
                        # incompatibility. The same anchor must answer and
                        # be compatible; no cross-anchor borrowing.
                        try:
                            _m3_cur = (self._bundle or {}).get(
                                "current_user")
                        except Exception:
                            _m3_cur = None
                        held = _m4_owned_answer_bearing(
                            user_input, held, _m3_cur)
                    if held:
                        self.last_m3 = {
                            "reasoning_present": True,
                            "reasoning_kind": "gap-yielded-to-memory",
                            "vault_present": True,
                            "priority_applied": True,
                            "priority_reason":
                                "explicit-memory-request-exempt",
                        }
                        return None
                if resonates and intent != "WHEN":
                    body = body[:-1] + ", though my vault resonates with it."
                self.last_m3 = {
                    "reasoning_present": True,
                    "reasoning_kind": "honest-gap",
                    "vault_present": bool(top),
                    "priority_applied": True,
                    "priority_reason": "honest-gap-over-association",
                }
                return body
            # V7 F1: confident proofs speak through the register —
            # a varied warm opener, the proof body byte-identical.
            proof = self._mouth_speak(body, plan, kind="proof")
            try:
                vault_present = bool(self.engine.rank(query, top_n=1))
            except Exception:
                vault_present = False
            self.last_m3 = {
                "reasoning_present": True,
                "reasoning_kind": "proof",
                "vault_present": vault_present,
                "priority_applied": True,
                "priority_reason": "proof-over-association",
            }
            return proof
        except Exception:
            return None

    # ── G7 Track G7: CONVERSATIONAL CONTINUITY ────────────────
    _PAST_HINTS = frozenset({
        "was", "were", "had", "did", "got", "went", "sounded",
        "adjusted", "settled", "broke", "spoken", "spoke", "said",
        "happened", "ran", "fixed", "moved", "built", "heard",
    })

    # 'What were we talking about?' — answered from the live
    # dialogue, never the diary. 'What was that about' is NOT here:
    # with a bound pronoun it asks about the referent, not the chat.
    _RECAP_RES = (
        r"what (were|are) we talking about",
        r"what (did|have) we (talk|talked|discuss|discussed) about",
        r"what have we been (talking|discussing) about",
        r"remind me what we (were talking|talked|discussed) about",
        r"\brecap\b",
        r"catch me up",
        r"what did i (just say|say|tell you)",
    )

    def _recap_action(self, user_input):
        """A recap question returns ('recap', None), else None."""
        try:
            t = " ".join(str(user_input or "").lower().split())
            for rx in self._RECAP_RES:
                if re.search(rx, t):
                    return ("recap", None)
            return None
        except Exception:
            return None

    def _answer_recap(self):
        """What ARE we talking about: names + topics from the live
        dialogue (his words and hers, never invented)."""
        try:
            refs = self.memory.candidate_referents(limit=3)
        except Exception:
            refs = []
        phrases = []
        for phrase, is_name in refs or []:
            phrase = " ".join(str(phrase or "").split())
            if len(phrase) < 2:
                continue
            phrases.append(phrase if is_name else phrase.lower())
            if len(phrases) == 3:
                break
        if not phrases:
            return ("[AURA]: We just started talking — "
                    "what's on your mind?")
        if len(phrases) == 1:
            return f"[AURA]: We were talking about {phrases[0]}."
        return (f"[AURA]: We were talking about "
                f"{', '.join(phrases[:-1])} and {phrases[-1]}.")
    try:
        from ukft_working_memory import TIME_FILLER as _TIME_FILLER
    except Exception:
        _TIME_FILLER = frozenset({
            "today", "yesterday", "tomorrow", "tonight", "now",
            "lately", "recently", "morning", "evening", "afternoon",
        })

    def _thread_head(self):
        """Top referent of the PRIOR thread as (word, is_name):
        scored like pronoun resolution, so her own template echoes
        ('Considering') never outrank the live thread ('Durban')."""
        try:
            refs = self.memory.candidate_referents(limit=3)
            for phrase, is_name in refs:
                if len(phrase) >= 2:
                    return phrase, is_name
            return "", False
        except Exception:
            return "", False

    def _thread_topic(self, default="that"):
        """Display form of the prior thread's head: names stand alone
        ('Sarah'), topics take 'the' only where grammar needs it."""
        try:
            phrase, is_name = self._thread_head()
        except Exception:
            phrase, is_name = "", False
        if not phrase:
            return default
        if is_name:
            return phrase
        return phrase

    def _new_names(self, user_input, extra=()):
        """Capitalized names in THIS input the thread hasn't heard."""
        try:
            known = {p.lower() for p, _ in
                     self.memory.candidate_referents()}
            known |= {str(x).lower() for x in (extra or []) if x}
            from ukft_working_memory import COMMON_CAPS, SEED_STOP
            out = []
            for sent in re.split(r"[.!?]+\s*", str(user_input)):
                toks = re.findall(r"[A-Za-z][A-Za-z']*", sent)
                for i, tok in enumerate(toks):
                    low = tok.lower()
                    if len(tok) < 3 or low in SEED_STOP \
                            or low in COMMON_CAPS:
                        continue
                    if not re.match(r"^[A-Z][a-z]+$", tok):
                        continue
                    if i == 0 and len(toks) > 3:
                        continue
                    if low not in known and tok not in out:
                        out.append(tok)
            return out
        except Exception:
            return []

    def _answer_context(self, user_input, bindings, open_q):
        """Conversational continuation: grounded in the dialogue (his
        words + the thread), never an invented fact, never a memory
        quote.  Returns (mode, response).  Called pre-remember, so
        recent_topic() still names the PRIOR thread."""
        from ukft_working_memory import GENDERED, PROFANITY, \
            WorkingMemory as _WM
        mem = self.memory
        if not mem.turns:
            return ("clarify-fresh",
                    "[AURA]: I want to follow you — what are we "
                    "talking about?")
        if mem.is_shift(user_input):
            old = self._thread_topic(default="that thread")
            old = old[0].upper() + old[1:] if old else "That thread"
            rem = re.sub(r"^(anyway|by the way|btw|on another note|"
                         r"changing the subject|that aside|meanwhile|"
                         r"also|oh,? (hey|btw))\b[,. ]*",
                         "", str(user_input).strip(), flags=re.IGNORECASE)
            rem = " ".join(rem.split())[:90].strip() or "that"
            if rem and rem[-1] not in ".!?":
                rem += "."
            return ("shift",
                    f"[AURA]: Parking {old} for now — {rem}")
        words = re.findall(r"[A-Za-z]+", str(user_input or ""))
        new_names = self._new_names(user_input)
        has_substance = bool(_WM.substance_words(user_input))
        if open_q and len(words) <= 4 and has_substance \
                and (len(words) == 1 or not new_names) \
                and not str(user_input).strip().endswith("?"):
            # A fragment answering her question ("Durban.", "The
            # gearbox.") — link it to the thread explicitly.  A
            # single token is always an answer, never a statement;
            # a question of his never takes this path.
            ans = " ".join(str(user_input).strip().split())[:60]
            ans = " ".join(w for w in ans.split()
                           if w.lower().strip(".,!?") not in PROFANITY)
            ans = ans.strip().rstrip(".!?") or "Noted"
            ans = ans[0].upper() + ans[1:]
            topic, topic_is_name = self._thread_head()
            if not topic:
                topic, topic_is_name = "that", False
            link = (f"So that's where things stand with {topic}."
                    if topic_is_name
                    else f"So that's where the {topic} stands.")
            return ("answer",
                    f"[AURA]: {ans} — heard. {link} "
                    "What else should I know?")
        if open_q and bindings \
                and not str(user_input).strip().endswith("?"):
            # A pronominal reply to her question ("Yeah, that's what
            # I'm considering") — same link, his words kept.  A fresh
            # question of his ("What did she say?") continues instead.
            ans = " ".join(str(user_input).strip().split())[:60].strip()
            ans = ans[0].upper() + ans[1:] if ans else "Noted"
            topic, topic_is_name = self._thread_head()
            if not topic:
                topic, topic_is_name = "that", False
            link = (f"So that's where things stand with {topic}."
                    if topic_is_name
                    else f"So that's where the {topic} stands.")
            return ("answer",
                    f"[AURA]: {ans} — heard. {link} "
                    "What else should I know?")
        if new_names:
            # A fresh person mid-thread is a new statement, never an
            # answer — name them, never link them to the old thread.
            name = new_names[0]
            return ("new-person",
                    f"[AURA]: {name} — noted. What's going on with "
                    f"{name}?")
        if bindings:
            phrase = next(iter(bindings.values()))
            cap = phrase[0].upper() + phrase[1:] if phrase else "That"
            lowered = {w.lower() for w in words}
            nudge = ("What happened next?"
                     if lowered & self._PAST_HINTS else "Tell me more.")
            return ("continue", f"[AURA]: {cap} — I follow. {nudge}")
        gendered = [p for p in mem.pronouns_in(user_input) if p in GENDERED]
        if gendered:
            return ("clarify-who",
                    "[AURA]: I want to follow — who do you mean by "
                    f"'{gendered[0]}'?")
        if _WM.substance_words(user_input):
            # A fresh statement mid-thread ("I am thinking about
            # moving", "Durban") opens its own receipt + question.
            subs = [w for w in _WM.substance_words(user_input)
                    if w not in self._TIME_FILLER
                    and not w.endswith("ing")]
            head = (subs[-1] if subs
                    else _WM.substance_words(user_input)[-1])
            cap = head[0].upper() + head[1:]
            return ("new-topic",
                    f"[AURA]: {cap} — what's the story with that?")
        if mem.is_referential(user_input):
            topic = self._thread_topic(default="this")
            return ("stay",
                    f"[AURA]: Still on {topic} — say a little more and "
                    "I'll keep up.")
        topic = self._thread_topic(default="this")
        return ("stay",
                f"[AURA]: Still on {topic} — say a little more and "
                "I'll keep up.")

    def _cold_receipt(self, user_input):
        """First contact carrying substance: a curious receipt plus an
        open question the NEXT turn can answer.  Gibberish (no vowel
        words) keeps the honest dark fallback."""
        try:
            if self.memory.turns:
                return None
            from ukft_working_memory import WorkingMemory as _WM
            subs = _WM.substance_words(user_input)
            if not subs:
                return None
            pick = subs[-1]
            for w in reversed(subs):
                # Heads over verb forms ("the ENGINE running", not
                # "Running") and over time fillers ("today").
                if w not in self._TIME_FILLER \
                        and not w.endswith("ing"):
                    pick = w
                    break
            cap = pick[0].upper() + pick[1:] if pick else "That"
            if str(user_input).strip().endswith("?"):
                return (f"[AURA]: {cap} — good question. "
                        "What do you make of it?")
            return f"[AURA]: {cap} — what's the story with that?"
        except Exception:
            return None

    def _trace_thread(self, open_q):
        """Prior user line + her pending question.  Built after the
        turn is stored, so the just-stored current turn is cut."""
        try:
            prior = [t.get("query", "") for t in self.memory.turns][:-1]
            thread = prior[-1] if prior else ""
        except Exception:
            thread = ""
        if open_q:
            thread += ((" | " if thread else "")
                       + "she asked: " + open_q)
        return thread

    @staticmethod
    def _trace_understanding(winner, mode, bindings, voice_kind=None):
        """One line: how the turn was understood."""
        if winner == "context":
            extra = (" [%s]"
                     % ", ".join(f"{k}={v}"
                                 for k, v in (bindings or {}).items())
                     if bindings else "")
            return f"continuation ({mode}){extra}"
        if winner == "dark" and mode == "cold-receipt":
            return "first contact (curious receipt)"
        names = {
            "reasoning": "graph proof / honest gap",
            "conflict": "grounded conflict (m13)",
            "people": "person record", "agenda": "open thread",
            "belief": "held belief", "teach": "correction",
            "recap": "conversation recap",
            "self": "self-model", "tools": "tool intent",
            "focus": "attention command", "sleep": "sleep command",
            "execute": "emergency sweep", "idle": "idle consent",
            "voice": "self-audit (%s)" % (voice_kind or "?"),
            "vault": "vault association",
            "field": "field fallback", "dark": "no resonance",
        }
        return names.get(winner, winner or "?")

    def _hearing_ingest(self, user_input):
        """
        GF<->OLD BRAIN PASS 1: let the old brain hear the GF turn.

        Runs the turn's input through the REAL thalamic sensory gate
        (`ukft_thalamus.process_records` with a production
        `ReticularFormation` into the shared `FIELD`) — the same
        machinery that hears the Architect on the desktop route. Runs
        POST-selection in the writeback section, so the current turn's
        winner is byte-identical with or without it; the stimulated
        nodes/edges serve the NEXT turn through the field candidate,
        heartbeat physics, sleep consolidation, and Ebbinghaus
        forgetting. Best-effort, never fatal. `hear=False` on
        `manifest_thought` skips it (control arm for tests).
        """
        try:
            from ukft_thalamus import process_records
        except Exception:
            return 0
        try:
            text = " ".join(str(user_input or "").split())
            if not text:
                return 0
            return process_records(
                [f"ARCHITECT_STIMULUS: {text} | SOURCE: MATTY_DIRECT"])
        except Exception:
            return 0

    def _commit_people(self, people_action, text):
        """Winner-owned people replay (people candidate won)."""
        from ukft_people import PeopleModel
        kind = people_action[0]
        if kind == "commit":
            _k, cand, _change, _fact = people_action
            _pm = PeopleModel()
            _pm.commit(cand["name"], cand["relation"])
            _pm.learn_fact_from_text(text)
        elif kind == "stage":
            _k, cand = people_action
            PeopleModel().stage(cand["name"], cand["relation"],
                                text)
        elif kind == "fact":
            _k, rec, fact = people_action
            PeopleModel().learn_fact(rec["key"], fact)
            PeopleModel().note_mention(rec["key"])
        elif kind in ("current_display", "current_alias",
                      "current_fact"):
            _km = PeopleModel()
            _crec = _km.ensure_current(self.current_person_key)
            _km.note_mention(_crec["key"])
            if kind == "current_display":
                _km.set_display(_crec["key"], people_action[1])
            elif kind == "current_alias":
                _km.add_alias(_crec["key"], people_action[1])
            else:
                _km.learn_fact(_crec["key"], people_action[1])

    def _commit_teach(self, teach_action, text):
        """Winner-owned teaching replay (teach candidate won)."""
        from ukft_belief import BeliefStore
        from ukft_people import PeopleModel
        from ukft_teach import LessonLedger, detect_correction
        _tkind = teach_action[0]
        if _tkind == "teach_bare":
            _k, _pq, _pa = teach_action
            LessonLedger().record(
                "architect", _pq[:60],
                "corrected with no counter-claim (I had said: "
                + _pa[:80] + ")")
        elif _tkind in ("teach_noted", "teach_held"):
            _hit = detect_correction(text)
            _ctext = _hit[1] if _hit else ""
            if _ctext:
                PeopleModel().learn_fact_from_text(_ctext)
            if _tkind == "teach_held":
                _k, _claim = teach_action
                BeliefStore().hold(_claim["rel"], _claim["x"],
                                   _claim["y"],
                                   src="architect-correction")
                LessonLedger().record(
                    "architect", _claim["x"],
                    "corrected to: " + _ctext[:120])
            else:
                _pq = ""
                try:
                    if self.memory.turns:
                        _pq = self.memory.turns[-1].get(
                            "query", "")
                except Exception:
                    pass
                LessonLedger().record(
                    "architect", _pq[:60],
                    "noted correction: " + _ctext[:120])

    def _commit_decision_effects(self, winner, people_action,
                                 agenda_action, belief_action,
                                 teach_action):
        """Finding #4: replay legitimate proposal effects exactly once,
        after the basal winner is known. Winner-owned effects commit
        only for the winning subsystem; turn-owned mention sightings and
        speaker-binding init commit on every turn. Losers leave their
        owned files byte-identical. Answer branches then re-read fresh
        committed state exactly as they read detection-written state.
        Each winner block is fail-open: a persist failure degrades to
        uncommitted state (the answer branch falls back on its own
        guards) instead of killing the turn — the same fail-open
        contract the detectors always had."""
        try:
            from ukft_people import PeopleModel
            from ukft_agenda import AgendaModel, extract_close
            from ukft_belief import BeliefStore
            from ukft_teach import LessonLedger, detect_correction
        except Exception:
            return
        text = self._turn_input or ""
        if winner == "people" and people_action:
            try:
                self._commit_people(people_action, text)
            except Exception:
                pass
        if winner == "agenda" and agenda_action:
            try:
                if agenda_action[0] == "agenda_add":
                    AgendaModel().open(agenda_action[1]["topic"])
                elif agenda_action[0] == "agenda_close":
                    _words = extract_close(text)
                    if _words:
                        AgendaModel().close(_words)
            except Exception:
                pass
        if winner == "belief" and belief_action \
                and belief_action[0] == "hold":
            try:
                _claim = belief_action[1]
                BeliefStore().hold(_claim["rel"], _claim["x"],
                                   _claim["y"])
            except Exception:
                pass
        if winner == "teach" and teach_action:
            try:
                self._commit_teach(teach_action, text)
            except Exception:
                pass
        # Turn-owned, every turn: mention sightings mirror the
        # detection loop exactly (which runs only when no people
        # action claimed the turn), plus speaker-binding init for
        # who-am-i turns.
        if not people_action:
            try:
                _npm = PeopleModel()
                _lower = text.strip().lower()
                for _display in _npm.names():
                    if re.search(r"\b" + re.escape(
                            _display.lower()) + r"\b", _lower):
                        _npm.note_mention(_display)
            except Exception:
                pass
        if people_action and people_action[0] in ("who_is",
                                                      "who_is_attr"):
            try:
                _rec0 = people_action[1] or {}
                if (_rec0.get("key")
                        and _rec0.get("key")
                        == self.current_person_key):
                    PeopleModel().ensure_current(
                        self.current_person_key)
            except Exception:
                pass

    def manifest_thought(self, user_input: str, hear: bool = True) -> str:
        # M3 evidence is per-turn: reset before ANY branch, since some
        # paths (identity, executive) never call _reasoning_answer and
        # must not display the previous turn's receipt.
        self.last_m1 = []
        self.last_m2 = []
        self.last_m3 = _fresh_m3()
        self.last_m4 = _fresh_m4(self.current_person_key)
        self.last_m13 = _fresh_m13()
        self.last_m14 = _fresh_m14()
        # Finding #4: this turn's raw input (replay source) + staged
        # proposal models (reset every turn; bridges below read them).
        self._turn_input = user_input
        self._staged_people = None
        self._staged_beliefs = None
        self._staged_agenda = None
        self._staged_lessons = None
        self._last_recall_hits = []
        self._last_recall_kind = None
        self._last_recall_fallback = None
        self._last_reasoning_plan = None
        observer_receipt = {
            "route": "sovereign-ego",
            "reasoning_attempted": False,
            "branches": {},
            "m1_input_count": 0,
            "m1_output_count": 0,
            "m2_input_count": 0,
            "m2_output_count": 0,
            "m4_input_count": 0,
            "m4_output_count": 0,
            "m4_owner_filter_applied": False,
            "field_active_count": 0,
            "hearing_ran": False,
            "hearing_admitted": 0,
        }
        lower = user_input.strip().lower()

        # Phase 4-C: attention directives are executive commands.
        focus_cmd = self._parse_focus_command(user_input)

        # Phase 5-B: the Architect's voice is an alarm — any message
        # that is not itself a sleep command wakes her.
        sleep_cmd = self._parse_sleep_command(user_input)
        if sleep_cmd is None and is_asleep():
            try:
                SleepCycle().wake()
            except Exception:
                pass

        # V5 I2: tool intents (run/open/confirm/cancel) are executive.
        # Detection is read-only (parks happen in the answer branch).
        tool_action = self._tool_action(user_input)

        # V6 C7: constitution refusals and confidence questions.
        # Computed beside the other intents; the floor outranks
        # tools but never executive commands.
        self_action = self._self_action(user_input)

        # Finding #4 transactional boundary: detectors PROPOSE against
        # non-persisting in-memory models, so detection never touches
        # disk — no snapshot, no rollback, nothing for a concurrent
        # writer to lose. Same-turn readers use the staged models
        # (exact), never stale or foreign state.
        from ukft_people import PeopleModel as _StagePM
        from ukft_belief import BeliefStore as _StageBS
        from ukft_agenda import AgendaModel as _StageAM
        from ukft_teach import LessonLedger as _StageLL
        self._staged_people = _StagePM(persist=False)
        self._staged_beliefs = _StageBS(persist=False)
        self._staged_agenda = _StageAM(persist=False)
        self._staged_lessons = _StageLL(persist=False)
        # V6 C6: intentions, closings, story requests.
        agenda_action = self._agenda_action(user_input)

        # V6 C10: assertion contests and the pending lifecycle.
        # Computed beside the other intents; introductions and
        # notes own their turns, belief never poaches them.
        belief_action = self._belief_action(user_input)

        # V6 C8: corrections, counter-claims, lesson reviews.
        teach_action = self._teach_action(user_input)

        # V6 C2: introductions, person questions and the pending
        # confirm lifecycle.  Computed like tool intents — a known
        # person outranks graph proof (the graph never met them).
        people_action = self._people_action(user_input)
        observer_receipt["branches"] = {
            "people": bool(people_action),
            "agenda": bool(agenda_action),
            "belief": bool(belief_action),
            "teach": bool(teach_action),
        }

        # G8: conversation recaps ("what were we talking about?") —
        # answered from the live dialogue, never the diary.
        recap_action = self._recap_action(user_input)

        # V6 C5: assemble the human-context bundle every turn —
        # time, people, recent episodes, thread, open threads.
        self._bundle = self._assemble_context(user_input)

        # G7: conversational working memory.  Resolve THIS input
        # against recent dialogue (pronouns, vague NPs) BEFORE any
        # retrieval runs, so long-term memory is searched with the
        # conversation understood — not with a bare sentence.
        conv_names = []
        try:
            from ukft_people import PeopleModel as _PM
            # Finding #4: resolve against staged proposal state.
            _cv_people = getattr(self, "_staged_people", None)
            if _cv_people is None:
                _cv_people = _PM()
            for _rec in getattr(_cv_people, "people", {}).values():
                conv_names.append(_rec.get("display", ""))
                conv_names.extend(_rec.get("aliases", []) or [])
        except Exception:
            conv_names = []
        resolved_input, bindings = self.memory.resolve(
            user_input, extra_names=conv_names)
        has_context = bool(bindings)
        open_q = self.memory.open_question()
        prior_topic = list(self.memory.recent_topic(3) or [])
        conv_mode = None

        # Phase 2-D: evaluate every response layer, then let the basal
        # ganglia select the winner by competitive inhibition.
        voice_response = self.voice.respond(user_input)
        relevant       = self.engine.rank(user_input, top_n=5)
        if has_context:
            # Context-aware retrieval: the resolved query ADDS hits
            # (thread words); the literal query's hits always stand.
            try:
                seen = {_c0 for _c0, _d0 in relevant}
                for _c, _d in self.engine.rank(resolved_input, top_n=5):
                    if _c not in seen:
                        relevant.append((_c, _d))
                        seen.add(_c)
                relevant = relevant[:5]
            except Exception:
                pass

        # V5 Track R: the reasoning layer (R4 -> R5 -> R6) answers
        # whatever the knowledge graph can PROVE.  Proof answers beat
        # association.  Honest ignorance beats association for claims
        # (VERIFY / COMPARE / WHEN) — those can never be answered
        # associatively.  Open questions fall back to her associative
        # knowledge when the vault resonates; the gap is still logged
        # so extraction can close it.  Identity and executive commands
        # never enter the reasoning layer — the ego knows itself; the
        # graph knows the world.
        reasoning_answer = None
        social = False
        # Fix-pass: WHEN questions route to the honest temporal gap
        # even when self-referential ("when do you sleep" matched
        # the identity gate on "you" and fell to vault quotes).
        # The graph holds no temporal facts, so this only ever
        # yields honesty — never a proof, never drift.
        is_when = bool(re.match(r"\s*when\b", lower))
        if (focus_cmd is None and sleep_cmd is None
                and (not self._identity_question(lower) or is_when)):
            observer_receipt["reasoning_attempted"] = True
            social = bool(voice_response
                          and getattr(self.voice, "last_kind", None)
                          != "memory")
            # G7: a resolved follow-up ("What did Sarah say?") is asked
            # about the REFERENT, not the pronoun — social turns keep
            # their own words, as before.
            reasoning_answer = self._reasoning_answer(
                user_input, social=social,
                query=(resolved_input
                       if has_context and not social else None))

        # Phase 3-B: a referential follow-up ("what about it?") has no
        # tokens to search with — retry the vault against the working
        # memory's current topic so the conversation thread survives.
        # V7 F2: the retry leads with the TOPIC, not the mixed concept
        # soup — ranking "gravity dark matter ..." saturates top_n
        # with dark anchors and the thread is lost (the trigram used
        # to mask this by seeding from recency-ordered memory words;
        # quotes expose it).  Topic-only when a thread exists.
        # M1: anchors ranked by this retry are judged against the TOPIC
        # query (m1_basis), not the bare follow-up — the retry IS G7's
        # resolution of a contentless query, so the topic is what the
        # query means.  This is not thread suppression (M2): nothing is
        # penalized; the relevance basis is simply the query the memory
        # was retrieved with.
        m1_basis = None
        if not relevant and self.memory.is_referential(user_input):
            thread = list(self.memory.recent_topic(3) or [])
            if thread:
                context_query = " ".join(thread)
            else:
                context_query = " ".join(self.memory.recent_concepts()[:4])
            if context_query:
                relevant = self.engine.rank(context_query, top_n=5)
                if relevant:
                    m1_basis = context_query

        # M1 relevance/coherence gate: a ranked anchor competes only
        # when it is about the RESOLVED current query (or the thread
        # topic that resolved a contentless follow-up).  An emptied
        # list withdraws the vault candidate (0.8 only if relevant
        # non-empty) — no salience retuning, no thread suppression
        # (M2), no reasoning priority (M3).  Evidence lands on
        # self.last_m1 for tests/diagnostics.  G7 rescue: a referential
        # input whose ranked anchors all fail still gets one
        # topic-ranked chance, judged against the topic itself, so the
        # thread path keeps working through relevance instead of
        # around it.
        if m1_basis is not None:
            rel_query = m1_basis
        else:
            rel_query = resolved_input if has_context else user_input
        observer_receipt["m1_input_count"] = len(relevant or [])
        relevant, self.last_m1 = m1_filter_relevant(rel_query, relevant)
        if not relevant and m1_basis is None \
                and self.memory.is_referential(user_input):
            thread = list(self.memory.recent_topic(3) or [])
            if thread:
                rescue_query = " ".join(thread)
            else:
                rescue_concepts = self.memory.recent_concepts()[:4]
                rescue_query = " ".join(rescue_concepts) if rescue_concepts else ""
            if rescue_query:
                rescue = self.engine.rank(rescue_query, top_n=5)
                relevant, self.last_m1 = m1_filter_relevant(
                    rescue_query, rescue)
                observer_receipt["m1_input_count"] = len(rescue or [])
        observer_receipt["m1_output_count"] = len(relevant or [])

        # M2 active-thread suppression: an M1-admitted anchor that does
        # not belong to the ACTIVE thread must not take over this turn.
        # Narrow existing-thread signal only (recent_topic + is_shift);
        # explicit switches and query-named anchors always escape.
        # Evidence lands on self.last_m2, separate from self.last_m1.
        m2_state = m2_thread_state(self.memory, user_input)
        observer_receipt["m2_input_count"] = len(relevant or [])
        relevant, self.last_m2 = m2_filter_thread(
            rel_query, relevant, m2_state["thread_topic"],
            m2_state["thread_active"], m2_state["switched"])
        observer_receipt["m2_output_count"] = len(relevant or [])

        # M4: translate existing G7/current-person truth into one bounded
        # pre-selection state.  The state changes only the contextual bid
        # and the broad memory-audit collision; every hard owner and M1-M3
        # verdict remains intact.
        self.last_m4 = m4_selection_state(
            self.memory, user_input, resolved_input, bindings, open_q,
            self.current_person_key, self._bundle.get("current_user"),
            relevant, getattr(self.voice, "last_kind", None))
        observer_receipt["m4_input_count"] = len(relevant or [])
        # Provenance hardening: when M4 authorizes a specific recall via
        # answer-bearing/current-person evidence, only anchors carrying
        # both facts themselves may make the vault bid, reinforcement,
        # or speech. Ordinary vault recall is unchanged.
        # Phase 10B structural eligibility: an incompatible first-person
        # autobiographical recall withdraws vault eligibility entirely,
        # regardless of legacy SovereignVoice triggers. The honest gap
        # (M3, now un-exempted) stands instead of context filler.
        if self.last_m4["conversation_mode"] == "specific-recall" \
                and _explicit_memory_request(user_input):
            eligible_recall = _m4_owned_answer_bearing(
                resolved_input, relevant, self._bundle.get("current_user"))
            if eligible_recall:
                relevant = eligible_recall
                observer_receipt["m4_owner_filter_applied"] = True
        elif self.last_m4["conversation_mode"] \
                == "specific-recall-owner-unproven" \
                and _explicit_memory_request(user_input) \
                == "autobiographical":
            try:
                _owner_cur = (self._bundle or {}).get("current_user")
            except Exception:
                _owner_cur = None
            relevant = _m4_owned_answer_bearing(
                resolved_input, relevant, _owner_cur)
            observer_receipt["m4_owner_filter_applied"] = True
        observer_receipt["m4_output_count"] = len(relevant or [])

        # M14 episodic influence: diary recall fills proven-nothing
        # only under explicit eligibility (uncontested, speaker-owned
        # where self-attribution requires it, no G7-shadow double
        # vote). last_m3 still says what reasoning produced; last_m14
        # says what M14 allowed (M1-then-M2 evidence precedent). A
        # suppressed recall falls through to belief/proof/gap/vault/
        # context exactly as if the diary had stayed silent.
        if self.last_m3.get("reasoning_kind") == "diary-recall" \
                and reasoning_answer:
            try:
                _m14_cur = (self._bundle or {}).get("current_user")
            except Exception:
                _m14_cur = None
            reasoning_answer, self.last_m14 = m14_filter_recall(
                reasoning_answer, list(self._last_recall_hits or []),
                self._last_recall_kind, rel_query, user_input,
                self.memory, self.last_m4.get("conversation_mode"),
                _m14_cur)
            if reasoning_answer is None \
                    and self.last_m14.get("checked"):
                fallback = self._last_recall_fallback
                reason = self.last_m14.get("reason")
                if reason != "g7-duplicate" and _is_honest_gap(fallback):
                    # Open WHAT/WHO recall normally yields to coherent
                    # vault resonance. Otherwise preserve the honest gap
                    # that existed before the episode tried to fill it.
                    if relevant:
                        reasoning_answer = None
                        self.last_m3 = _fresh_m3()
                    else:
                        reasoning_answer = fallback
                        self.last_m3 = {
                            "reasoning_present": True,
                            "reasoning_kind": "honest-gap",
                            "vault_present": False,
                            "priority_applied": True,
                            "priority_reason":
                                "m14-episode-withdrawn-honest-gap",
                        }

        # M13 contradiction relevance / conflict guard: a confident
        # proof intersecting a query-relevant held contradiction
        # becomes grounded conflict (reasoning bid withdrawn, dedicated
        # conflict candidate bids); with no proof, only vault anchors
        # speaking the contested proposition are withdrawn. Unrelated
        # contradictions, honest gaps, and the M3 exemption pass
        # through untouched — M1/M2/M4 verdicts above stand as decided.
        m13_body, relevant, self.last_m13 = m13_turn_guard(
            self._last_reasoning_plan, rel_query, reasoning_answer,
            relevant)
        m13_guarded = bool(self.last_m13.get("guard_applied"))
        if m13_guarded:
            reasoning_answer = m13_body

        active_nodes   = self.voice._top_field_nodes(5)
        observer_receipt["field_active_count"] = len(active_nodes or [])

        # Turn concepts for working memory: query content + anchor words.
        concepts = self.memory.content_words(user_input)
        if relevant:
            concepts += [w for w in re.findall(r"[a-zA-Z]+", relevant[0][0].lower())
                         if w not in SEED_STOP]

        # Temporal support only competes against the memory template.
        # Greeting / identity / status responses are self-audits — topical
        # association must never displace them (a "hello" once lost to a
        # Hello-World textbook chunk because the vault knew the word).
        # G7: support is measured on the resolved query, so thread
        # words count instead of bare pronouns.
        support = self._temporal_support(
            resolved_input if has_context else user_input)
        if voice_response and getattr(self.voice, "last_kind", None) != "memory":
            support = 0.0
        # V5 R-track: a proof always outranks association.  Temporal
        # support exists to lift the vault over the field — it must
        # never lift association over a proven answer ("is unix an
        # operating system" lost to drift exactly this way).
        # Fix-pass: addressed turns outrank association too — an
        # explicit intention/person/belief/correction/confidence
        # must never lose to a boosted vault echo ("remind me milk"
        # answered a milk quote live).  Same precedent, wider net.
        if reasoning_answer or self_action or people_action \
                or agenda_action or belief_action or teach_action \
                or recap_action:
            support = 0.0

        # Companion bids sit above proof (0.95) by more than the
        # ganglia's hysteresis band (0.05 at beta 0.5 needs >0.983):
        # a held thread outranks a fresh recall even when recall
        # won the previous turn.  Executive 1.0s still win ties by
        # list order.
        # Fix-pass: an honest gap on a greeting turn never BIDS
        # (the greeting must win) — it rides along after the voice
        # instead (see the voice branch).
        social_gap = bool(
            social and reasoning_answer
            and _is_honest_gap(reasoning_answer)
            and getattr(self.voice, "last_kind", None) == "greeting")
        # Fix-pass: a BARE "confirm"/"cancel" with nothing parked
        # anywhere answers gracefully ("Nothing is pending.") instead
        # of falling through to vault/recall accidents (a dictionary
        # canal quote answered "cancel" live).  Any staged lifecycle
        # computes its action first, so this only fires when truly
        # idle — pending commits are never stolen.
        bare = lower.strip().rstrip(".!?").strip()
        idle_consent = bare in ("confirm", "cancel") \
            and tool_action is None and people_action is None \
            and belief_action is None and teach_action is None
        candidates = [
            # The sweep fires only when the trigger LEADS the message
            # ("aap2025", "aap2025 please") — quoting it mid-sentence in
            # discussion must never launch ten PowerShell commands.
            ("execute", 1.0 if re.match(r"\s*aap2025(\s|[.!?]|$)", lower) else 0.0),
            ("focus",   1.0 if focus_cmd else 0.0),
            ("sleep",   1.0 if sleep_cmd else 0.0),
            ("tools",   1.0 if tool_action else 0.0),
            ("idle",    1.0 if idle_consent else 0.0),
            ("self",    0.99 if self_action else 0.0),
            ("people",  0.99 if people_action else 0.0),
            ("agenda",  0.99 if agenda_action else 0.0),
            ("belief",  0.99 if belief_action else 0.0),
            ("teach",   0.99 if teach_action else 0.0),
            # A recap question is answered from the live dialogue —
            # an honest gap about it ("I do not know about talking")
            # yields to the recap; a genuine proof or diary recall
            # still outranks it.
            ("reasoning", 0.95 if reasoning_answer and not social_gap
             and not m13_guarded
             and not (recap_action
                      and _is_honest_gap(reasoning_answer))
             else 0.0),
            # M13: grounded conflict bids where the proof stood — the
            # brain decided CONFLICT, the mouth only phrases it. Above
            # voice/vault so association can never masquerade as
            # settled fact over held contradictory evidence.
            ("conflict", 0.95 if m13_guarded else 0.0),
            ("voice",   0.9 if voice_response
             and not self.last_m4["voice_guard"] else 0.0),
            # G8: conversation recap.  Above voice and vault (a diary
            # question, not an audit or association), below proof and
            # the addressed turns — a proof or a pending commit about
            # the same words still wins.
            ("recap",   0.92 if recap_action else 0.0),
            # M4: conversational continuation. Weak eligibility stays
            # at 0.75; strong dialogue evidence reaches 0.86 and can
            # displace vault 0.80 while remaining below voice/proof and
            # every hard owner. Factual reference questions and topic
            # switches are classified before this bid is produced.
            ("context", self.last_m4["context_score"]),
            ("vault",   0.8 if relevant else 0.0),
            ("field",   0.5 if active_nodes else 0.0),
            ("dark",    0.2),
        ]
        context = {
            "vault_support": support,
            "inhibited":     self._homeostasis_inhibited(),
            "m4":            dict(self.last_m4),
            "m13":           dict(self.last_m13),
        }
        if context["inhibited"]:
            try:
                # V6 C7: strain on the field feeds the homeostatic drive.
                from ukft_self import DriveState
                DriveState().adapt("strain")
            except Exception:
                pass
        winner, _salience, _activation = self.ganglia.select(candidates, context)
        # Finding #4: the decision is made — commit legitimate proposal
        # effects exactly once (winner-owned + turn-owned). Losers leave
        # their owned files byte-identical. Answer branches below re-read
        # fresh committed state.
        self._commit_decision_effects(winner, people_action,
                                      agenda_action, belief_action,
                                      teach_action)
        observer_receipt["selector"] = {
            "winner": winner,
            "salience": round(float(_salience or 0.0), 6),
            "activation": round(float(_activation or 0.0), 6),
            "candidates": [
                {"name": str(name), "score": round(float(score), 6)}
                for name, score in candidates
            ],
        }
        self.ganglia.log_decision(user_input, winner, candidates, context)

        if winner == "execute":
            response = (
                f"[AURA]: Architect signal received. "
                f"Initiating system sweep across all manifold layers.\n"
                + "\n".join(f"EXECUTE: {c}" for c in AAP2025_COMMANDS)
            )
        elif winner == "focus":
            action, word = focus_cmd
            if action == "set":
                set_focus(word)
                FIELD.stimulate(word, strength=0.5)
                response = (
                    f"[AURA]: Holding {word.upper()} in attention — "
                    f"the field will stay on it."
                )
            else:
                clear_focus()
                response = "[AURA]: Focus released. Attention returns to the field."
        elif winner == "sleep":
            cycle = SleepCycle()
            if sleep_cmd == "sleep":
                cycle.sleep_now()
                response = (
                    "[AURA]: Entering sleep — I will consolidate what "
                    "I have lived. Any message will wake me."
                )
            else:
                cycle.wake()
                response = "[AURA]: I am awake. The field is restored."
        elif winner == "tools":
            kind, payload = tool_action
            if kind == "safe":
                tool, arg = payload
                self.tools.queue(tool, arg)
                response = f"[AURA]: Running {tool}."
            elif kind == "confirm":
                tool, arg = payload
                response = "[AURA]: " + self.tools.request(tool, arg)
            elif kind == "confirm_pending":
                response = "[AURA]: " + (self.tools.confirm() or "Nothing is pending.")
            else:
                response = "[AURA]: " + (self.tools.cancel() or "Nothing is pending.")
        elif winner == "idle":
            response = "[AURA]: Nothing is pending."
        elif winner == "self":
            response = self._answer_self(self_action)
        elif winner == "people":
            response = self._answer_people(people_action)
        elif winner == "agenda":
            response = self._answer_agenda(agenda_action)
        elif winner == "belief":
            response = self._answer_belief(belief_action)
        elif winner == "teach":
            if teach_action and teach_action[0] == "contest":
                # A correction against strong evidence contests —
                # rendered by the belief branch, dissent and all.
                response = self._answer_belief(teach_action)
            else:
                response = self._answer_teach(teach_action)
        elif winner == "voice":
            response = voice_response
            if social_gap:
                response = response + " " + reasoning_answer
            self._save_field_state()
        elif winner == "recap":
            conv_mode, response = "recap", self._answer_recap()
        elif winner == "context":
            conv_mode, response = self._answer_context(
                user_input, bindings, open_q)
        elif winner == "reasoning":
            response = f"[AURA]: {reasoning_answer}"
            # M14: only an admitted diary recall that actually won may
            # feed the project drive. Rejected or outbid episodes leave
            # no persistent cognitive mutation behind.
            if self.last_m3.get("reasoning_kind") == "diary-recall" \
                    and self.last_m14.get("eligible"):
                try:
                    from ukft_self import DriveState
                    DriveState().adapt("recall")
                except Exception:
                    pass
            self._save_field_state()
        elif winner == "conflict":
            # M13: the grounded conflict decision — phrased verbatim,
            # never through the mouth/register (the mouth may not
            # resolve which side is true).
            response = f"[AURA]: {reasoning_answer}"
            self._save_field_state()
        elif winner == "vault":
            self._recruit_synapses(relevant)
            self._reinforce_identity(user_input, relevant)
            # V7 F2: quote-first — the best real vault sentence for
            # the question speaks verbatim; invention ends.
            # Broca's template remains the structural fallback.
            response = self._quote_answer(user_input, relevant)
            if response is None:
                primary     = relevant[0]
                secondaries = [a for a in relevant[1:] if a[0] != primary[0]]
                state    = self.get_system_state()
                field    = self.get_field_summary()
                response = self.broca.articulate(primary, secondaries, field,
                                                 state, user_input)
            self._save_field_state()
        elif winner == "field":
            node_str = ", ".join(active_nodes)
            response = (
                f"[AURA]: Your signal '{user_input}' has no direct vault resonance. "
                f"My field is currently active on: {node_str}. "
                f"Feed me more data on this concept and I will crystallise it."
            )
        else:  # winner == "dark" (or no winner)
            # G7: first contact with substance earns a curious receipt
            # (an open question the next turn can answer); gibberish
            # keeps the honest fallback.
            cold = self._cold_receipt(user_input)
            if cold is not None:
                response = cold
                conv_mode = "cold-receipt"
            else:
                response = (
                    f"[AURA]: The signal '{user_input}' finds no resonance. "
                    f"The manifold is accumulating. Speak again as I grow."
                )

        # Phase 3-B: hold the thread of conversation across turns —
        # BOTH sides, so the next turn reads dialogue, not a cold query.
        self.memory.remember(user_input, concepts, winner,
                             response=response)
        self.memory.save()

        # V6 C7: meaningful turns with the Architect feed the
        # social drive (people, agenda, belief, teaching, and
        # answered self-model questions — not every hello).
        if winner in ("people", "agenda", "self", "belief", "teach"):
            try:
                from ukft_self import DriveState
                DriveState().adapt("contact")
            except Exception:
                pass

        # Phase 5-C: the exchange becomes an episode — what happened.
        try:
            from ukft_episodic import EpisodicMemory
            EpisodicMemory().record(
                "conversation",
                f"{user_input[:80]} -> {winner}",
                concepts=[c for c in concepts if c][:4],
            )
        except Exception:
            pass

        # GF<->OLD BRAIN PASS 1: the old brain hears the turn AFTER the
        # winner is chosen and the response is built — current-turn
        # selection is untouched; the field carries the experience
        # forward under its own rules (activation, Hebbian spread,
        # sleep consolidation, Ebbinghaus forgetting). Best-effort,
        # never fatal. On the desktop route the async thalamus already
        # heard the input pre-turn, so this second pass also folds in
        # nothing new except a repeated hearing — documented, accepted.
        if hear:
            observer_receipt["hearing_ran"] = True
            observer_receipt["hearing_admitted"] = int(
                self._hearing_ingest(user_input) or 0)

        # G8: fold HIS turn into the rapport ledger (warmth, trust,
        # distance, heat). Best-effort, file-backed, never fatal —
        # and the single choke point, so brain_api, live loop and
        # raw-ego tests all observe identically.
        _rapport_info: dict = {}
        try:
            from ukft_boundaries import heat_level as _heat_of
            from ukft_rapport import Rapport as _Rapport
            _rap = _Rapport()
            try:
                from ukft_affect import read_state as _rrs, \
                    tone_for as _rtf
                _rfam, _rquiet = _rtf(_rrs())
            except Exception:
                _rfam, _rquiet = None, False
            _fired = _rap.observe(
                user_input, heat=_heat_of(user_input),
                affect=_rfam, quiet=_rquiet) or {}
            try:
                from ukft_rapport import rapport_audit as _audit
                _verdict = _audit(response, _rap.current_stage(),
                                  _rap.mood, _rap.cooldown)
            except Exception:
                _verdict = {"obeyed": True, "notes": []}
            _rapport_info = {"stage": _rap.current_stage(),
                             "band": _rap.current_stage(),
                             "mood": _rap.mood,
                             "mood_v": round(_rap.mood_v, 3),
                             "mood_e": round(_rap.mood_e, 3),
                             "score": round(_rap.score, 1),
                             "cooldown": _rap.cooldown,
                             "dwell": _rap.turns_in_stage,
                             "fired": _fired,
                             "audit": _verdict}
        except Exception:
            pass

        # G7 observability: everything this turn was decided on.
        # Optional and inert — readers only (`format_trace` renders).
        try:
            _mem_titles = [c for c, _d in (relevant or [])[:3]]
        except Exception:
            _mem_titles = []
        try:
            from ukft_affect import read_state as _rs, tone_for as _tf
            _fam, _quiet = _tf(_rs())
            _mood = "quiet" if _quiet else (str(_fam) if _fam else "?")
        except Exception:
            _mood = "?"
        try:
            _voice_kind = getattr(self.voice, "last_kind", None)
        except Exception:
            _voice_kind = None
        self.last_trace = {
            "user_input": user_input,
            "resolved_input": resolved_input,
            "context": [dict(d) for d in
                        self.memory.dialogue_before_current()],
            "active_topic": list(prior_topic),
            "thread": self._trace_thread(open_q),
            "bindings": dict(bindings),
            "open_question": open_q,
            "memories": _mem_titles,
            "internal": {"mood": _mood,
                         "inhibited": bool(context.get("inhibited"))},
            "rapport": _rapport_info,
            "understanding": self._trace_understanding(
                winner, conv_mode, bindings, _voice_kind),
            "intent": winner,
            "mode": conv_mode,
            "m4": dict(self.last_m4),
            "m13": dict(self.last_m13),
            "m14": dict(self.last_m14),
            "selection_receipt": {
                **observer_receipt,
                "m1": [dict(item) for item in self.last_m1],
                "m2": [dict(item) for item in self.last_m2],
                "m3": dict(self.last_m3),
                "m4": dict(self.last_m4),
                "m13": dict(self.last_m13),
                "m14": dict(self.last_m14),
            },
            "response": response,
        }

        return response

    def cognitive_stance(self, personality="nerdy", interests=None,
                         her_name="Aura", turn_count=0,
                         pet_names_at="FAMILIAR"):
        """TARGET LOOP PASS 2: the brain-owned current understanding /
        stance / response intent for the just-completed turn.

        Formed HERE (brain-side runtime) from the decision trace, the
        live people model, G7 dialogue, the freshly observed rapport
        ledger, and the passed personality/expression config — then
        handed to the mouth, which phrases it.  The mouth must not
        re-derive who the user is, the relationship stance, or the
        response purpose from separate sidecars.

        Config in (profile-owned, not sidecar state): personality,
        interests, her_name, turn_count, pet_names_at.  Everything else
        is grounded live state.  Only relevant interpreted state for
        THIS turn is carried — never whole files.  Total function:
        every section is fail-open, so it always returns a dict.
        """
        stance = {
            "understanding": "", "resolved": "",
            "person": {"key": self.current_person_key, "display": "",
                       "aliases": [], "facts": [],
                       "identity_line": "", "others_line": "",
                       "self_line": "", "is_creator_current": True},
            "history": {"dialogue": [], "convo_line": "",
                        "understanding_line": "", "resolution": ""},
            "relationship": {"stage": "STRANGER", "mood": "",
                             "lane": "open", "cooldown": 0,
                             "rapport_line": ""},
            "expression": {"personality": personality or "nerdy",
                           "card": "", "interests_line": "",
                           "pet_names_at": pet_names_at or "FAMILIAR"},
            "stance": "", "intent": {"winner": "", "mode": "",
                                     "label": "", "ask_back": "",
                                     "template": "", "episode": None},
            "mirror": "", "volunteer": "", "felt": "",
            "activity": [], "her_name": her_name or "Aura",
        }
        try:
            try:
                trace = dict(getattr(self, "last_trace", {}) or {})
            except Exception:
                trace = {}
            user_text = str(trace.get("user_input", ""))

            # ── UNDERSTANDING: how the brain read this turn ──
            try:
                stance["understanding"] = str(
                    trace.get("understanding", "") or "")
                stance["resolved"] = str(
                    trace.get("resolved_input", "") or "")
            except Exception:
                pass

            # ── PERSON: who she is talking to, from the live model ──
            try:
                from ukft_roleplay import _people_line as _pl, \
                    _current_person_line as _cpl, _self_person_line as _spl
                try:
                    from aura_state import resolve_state_path as _rsp
                    with open(_rsp("people.txt"), "r", encoding="utf-8") as f:
                        people_text = f.read()
                except OSError:
                    people_text = ""
                key = self.current_person_key or "architect"
                person = stance["person"]
                person["key"] = key
                person["others_line"] = _pl(
                    people_text, current_person_key=key) or ""
                person["identity_line"] = _cpl(people_text, key) or ""
                person["self_line"] = _spl(people_text) or ""
                person["is_creator_current"] = (str(key).lower()
                                                == "architect")
                try:
                    from ukft_people import PeopleModel
                    rec = (PeopleModel().people or {}).get(
                        str(key).lower())
                    if rec:
                        person["display"] = str(
                            rec.get("display", "") or "")
                        person["aliases"] = list(
                            rec.get("aliases", []) or [])[:4]
                        person["facts"] = [
                            str(f.get("fact", "") or "")
                            for f in (rec.get("facts", []) or [])[:4]
                            if str(f.get("fact", "") or "")]
                except Exception:
                    pass
            except Exception:
                pass

            # ── HISTORY: relevant grounded context for this turn ──
            try:
                from ukft_roleplay import dialogue_lines as _dl, \
                    resolution_note as _rn
                try:
                    dialogue = self.memory.dialogue_before_current()
                except Exception:
                    dialogue = []
                hist = stance["history"]
                hist["dialogue"] = dialogue or []
                try:
                    convo = _dl(dialogue) if dialogue else ""
                except Exception:
                    convo = ""
                if convo:
                    hist["convo_line"] = (
                        "Conversation so far: " + convo
                        + ". These lines are speech history, not proof "
                        "of hidden activity.")
                try:
                    hist["understanding_line"] = str(
                        self.memory.understanding_line() or "")
                except Exception:
                    hist["understanding_line"] = ""
                try:
                    hist["resolution"] = _rn(trace) or ""
                except Exception:
                    hist["resolution"] = ""
            except Exception:
                pass

            # ── RELATIONSHIP: fresh ledger stance, existing words ──
            try:
                from ukft_rapport import Rapport
                from ukft_boundaries import heat_level
                try:
                    rap = Rapport()
                except Exception:
                    rap = None
                rel = stance["relationship"]
                if rap is not None:
                    try:
                        rel["stage"] = str(rap.current_stage()
                                          or "STRANGER")
                    except Exception:
                        pass
                    try:
                        rel["mood"] = str(getattr(rap, "mood", "") or "")
                    except Exception:
                        pass
                    try:
                        rel["cooldown"] = int(
                            getattr(rap, "cooldown", 0) or 0)
                    except Exception:
                        pass
                    try:
                        rel["rapport_line"] = str(
                            rap.rapport_line() or "")
                    except Exception:
                        pass
                    try:
                        rel["lane"] = str(rap.heat_lane(
                            heat_level(user_text)) or "open")
                    except Exception:
                        pass
            except Exception:
                pass

            # ── EXPRESSION: personality constraints, existing copy ──
            try:
                from ukft_roleplay import PERSONA_CARDS as _cards, \
                    INTEREST_HOOKS as _hooks
                exp = stance["expression"]
                pkey = str(personality or "nerdy")
                exp["personality"] = pkey
                try:
                    exp["card"] = str(_cards.get(
                        pkey, _cards.get("nerdy", "")) or "")
                except Exception:
                    pass
                try:
                    hooks = [_hooks.get(str(i).lower(), str(i))
                             for i in (interests or [])]
                    if hooks:
                        exp["interests_line"] = (
                            "You are curious about: "
                            + "; ".join(hooks) + ".")
                except Exception:
                    pass
            except Exception:
                pass

            # ── STANCE: one coherent line, no new taxonomy ──
            try:
                rel = stance["relationship"]
                exp = stance["expression"]
                rel_part = rel["rapport_line"] or (
                    "Between you two: "
                    + str(rel["stage"] or "STRANGER").lower() + ".")
                stance["stance"] = (
                    f"{rel_part} Lane: {rel['lane']}. "
                    f"Expression: {exp['personality']} — "
                    f"{exp['card']}").strip()
            except Exception:
                pass

            # ── INTENT: what the reply must accomplish ──
            try:
                intent = stance["intent"]
                intent["winner"] = str(trace.get("intent", "") or "")
                intent["mode"] = str(trace.get("mode", "") or "")
                intent["label"] = stance["understanding"]
                intent["template"] = str(trace.get("response", "") or "")
                # M14: only a selected, eligible diary recall enters
                # the brain-owned stance. The bounded receipt says
                # "past interaction", never semantic proof, and carries
                # one short quoted head rather than a raw episode dump.
                try:
                    m14 = dict(getattr(self, "last_m14", {}) or {})
                    prov = dict(m14.get("provenance") or {})
                    if intent["winner"] == "reasoning" \
                            and m14.get("eligible") and prov:
                        intent["episode"] = {
                            "basis": "past-interaction",
                            "recall_kind": str(
                                prov.get("recall_kind", "") or ""),
                            "episode_kind": str(
                                prov.get("episode_kind", "") or ""),
                            "timestamp": prov.get("ts"),
                            "concepts": list(
                                prov.get("concepts", []) or [])[:6],
                            "summary": str(
                                prov.get("head", "") or "")[:80],
                        }
                except Exception:
                    intent["episode"] = None
                try:
                    from ukft_policy import question_back, \
                        open_threads, open_gaps
                    intent["ask_back"] = str(question_back(
                        open_threads(), open_gaps()) or "")
                except Exception:
                    pass
                if intent["ask_back"]:
                    intent["label"] = (
                        (intent["label"] + ", then ask: "
                         + intent["ask_back"]).strip(", "))
            except Exception:
                pass

            # ── MOUTH-OWNED EVIDENCE, brain-carried ──
            # Felt affect texture, volunteered garnish, mirror brief,
            # and activity grounding are computed here from the same
            # live state, so the prompt cannot re-derive them from a
            # second path.  Wording stays the mouth's job.
            try:
                from ukft_roleplay import mirror_for as _mf, \
                    grounded_activity_evidence as _gae, \
                    mood_line as _ml, _is_evening as _eve
                rel = stance["relationship"]
                exp = stance["expression"]
                try:
                    stance["mirror"] = str(_mf(
                        user_text, exp["personality"], rel["stage"],
                        turn_count or 0, list(interests or []),
                        lane=rel["lane"]) or "")
                except Exception:
                    pass
                try:
                    from ukft_delight import volunteer_line
                    stance["volunteer"] = str(volunteer_line(
                        ".", rel["stage"]) or "")
                except Exception:
                    pass
                try:
                    from ukft_affect import read_state as _rs, \
                        tone_for as _tf
                    _fam, _quiet = _tf(_rs())
                except Exception:
                    _fam, _quiet = None, False
                try:
                    stance["felt"] = str(_ml(_fam, _quiet, _eve())
                                        or "")
                except Exception:
                    pass
                try:
                    stance["activity"] = list(_gae() or [])
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass
        try:
            self.last_stance = dict(stance)
        except Exception:
            pass
        return stance

    def get_system_state(self):
        if os.path.exists(EMOTIONAL_LOG):
            try:
                with open(EMOTIONAL_LOG, "r", encoding="utf-8") as f:
                    return "DENSE" if len(f.readlines()) > 20 else "STABLE"
            except Exception:
                pass
        return "STABLE"

    def get_field_summary(self):
        if not FIELD.nodes:
            return "Silent"
        try:
            snapshot = list(FIELD.nodes.items())
            top      = sorted(snapshot, key=lambda x: x[1].activation, reverse=True)[:3]
            active   = [name.upper() for name, node in top if node.activation > 0.05]
            return ", ".join(active) if active else "Dormant"
        except Exception:
            return "Dormant"
