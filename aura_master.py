import os
import threading
import time
import sys
import json
import subprocess

from aura_bus import (append as bus_append, write as bus_write,
                        drain as bus_drain, read as bus_read)
from aura_constants import D_INVARIANT
from ukft_inner_monologue import run_inner_monologue
from aura_field import FIELD
from ukft_cerebellum import run_cerebellum
from ukft_memory_vault import stabilize_data
from ukft_thalamus import run_thalamus
from ukft_synapse import run_synapse_cycle
from ukft_dream_state import generate_dream_pattern
from ukft_hippocampus import run_hippocampus
from ukft_amygdala import run_amygdala
from ukft_parietal_lobe import run_parietal
from aura_cortex import run_cortex_processing
from aura_bridge import SovereignEgo
from ukft_entropy import run_entropy_cycle
from aura_motor import run_motor
from ukft_pfc import run_pfc
from aura_vocal_manifest import run_vocal_manifest
from ukft_pdf_intake import run_pdf_intake
from ukft_hypothalamus import run_hypothalamus   # Phase 1-A
from ukft_dmn import run_default_mode_network    # Phase 2 scaffold
from ukft_temporal_lobe import run_temporal_lobe # Phase 2-C
from ukft_trigram import run_trigram_engine      # Phase 3-A
from ukft_discovery import run_discovery         # Phase 4-B
from ukft_identity import run_identity           # Phase 4-D
from ukft_sleep import run_sleep_cycle           # Phase 5-B
from ukft_ebbinghaus import run_ebbinghaus       # Phase 5-D
from ukft_backup import run_backup               # Operational
from ukft_voice import run_voice                 # V5 I1
from ukft_ambient import run_ambient             # V5 I3
from ukft_presence import run_presence           # V5 I4

UI_INPUT_FILE = "ui_input.txt"
THOUGHTS_FILE = "aura_thoughts.txt"
OUTPUT_FILE   = "aura_output.txt"
INSTANCE_LOCK = "aura_instance.lock"


def _pid_alive(pid):
    """Cross-process liveness check with EXACT pid matching.

    The old substring test matched stale PID 12 inside live PID 112
    and wrongly refused boot.  CSV output is parsed column-wise now.
    """
    try:
        out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"],
                             capture_output=True, text=True, timeout=10)
        for line in (out.stdout or "").splitlines():
            cells = [c.strip().strip('"') for c in line.split('","')]
            if len(cells) >= 2 and cells[1] == str(pid):
                return True
        return False
    except Exception:
        return False


def acquire_instance_lock():
    """
    Refuse to boot a second Aura onto the same workspace.  Two processes
    share one vault and bypass the per-process bus locks — that caused
    duplicate appends twice.  Stale locks (dead PID) are overwritten.
    """
    try:
        if os.path.exists(INSTANCE_LOCK):
            raw = open(INSTANCE_LOCK, "r", encoding="utf-8").read().strip()
            pid = int(raw) if raw.isdigit() else 0
            if pid and pid != os.getpid() and _pid_alive(pid):
                print(f"[BOOT] Aura is already running (PID {pid}). "
                      f"Exiting to protect the vault.")
                return False
        with open(INSTANCE_LOCK, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        return True
    except Exception:
        return True


def run_field_heartbeat():
    """
    Drives the cognitive physics engine at 10 Hz.
    Bug A fix: field_stats.txt is now written exclusively inside
    aura_field.step() — this function no longer touches it.
    Phase 1-D: monitors aura_is_thinking.lock to enter/exit
    recombination mode so active context is protected during responses.
    """
    print("--- AURA HEARTBEAT: COGNITIVE PHYSICS ACTIVE ---")
    tick             = 0
    was_thinking     = False
    error_count      = 0

    while True:
        try:
            # Phase 1-D: detect lock transitions
            is_thinking = os.path.exists("aura_is_thinking.lock")
            if is_thinking and not was_thinking:
                FIELD.enter_recombination()
            elif not is_thinking and was_thinking:
                FIELD.exit_recombination()
            was_thinking = is_thinking

            FIELD.step()   # field_stats.txt written inside here (Bug A fix)
            tick += 1

            # Export field_map.json for synapse visualiser (~once per second)
            if tick % 10 == 0:
                with FIELD.lock:
                    nodes_data = {
                        name: {
                            "activation": node.activation,
                            "phase":      node.phase,
                        }
                        for name, node in FIELD.nodes.items()
                    }
                    edges_data = [
                        {
                            "source": src_name,
                            "target": tgt_node.name,
                            "weight": weight,
                        }
                        for src_name, src_node in FIELD.nodes.items()
                        for tgt_node, weight in src_node.connections.items()
                    ]
                bus_write("field_map.json", json.dumps(
                    {"nodes": nodes_data, "edges": edges_data}))

            error_count = 0

        except Exception as e:
            # Phase 0.5: never fail silently. Report the first fault and
            # then every 100th repeat so a persistent error stays visible
            # without flooding the console at 10 Hz.
            error_count += 1
            if error_count == 1 or error_count % 100 == 0:
                print(f"[Heartbeat] Friction x{error_count}: {e}")
        time.sleep(0.1)


def start_background_lobe(target_function, name):
    thread = threading.Thread(target=target_function, daemon=True)
    thread.start()
    print(f"[{name}] Online.")
    time.sleep(0.2)


def terminal_input_thread():
    while True:
        try:
            user_msg = input("[TERMINAL] ARCHITECT >> ")
            if user_msg.strip():
                # Queued through the bus: never overwrites a message the
                # main loop has not consumed yet.
                bus_append(UI_INPUT_FILE, user_msg.strip())
        except (EOFError, KeyboardInterrupt):
            break


def process_message(ego, message, roleplay_fn=None):
    """
    Full pipeline.
    Phase 1-D: lock file is written here (as before), and the heartbeat
    thread detects it to enter CMB recombination mode automatically.
    Phase 0.5: the lock is released in a finally block — any failure in
    manifest_thought must never leave the organism frozen in
    "thinking" state (all seven lock-aware lobes spin on that file).
    G3: immersive voice. The engine runs mouth-quiet (it learns and
    routes; template kept), then the pinned runner speaks persona +
    depth + live memory — executive winners stay template, and the
    motor queue ONLY fires on an execute winner (a roleplayed line
    can never queue commands). Any voice failure falls back to the
    template; roleplay_fn injects for hermetic tests.
    """
    with open("aura_is_thinking.lock", "w") as lock:
        lock.write("ACTIVE")

    obs_emit = None
    obs_turn_id = str(int(time.time() * 1000))
    try:
        from observer_telemetry import default_emitter as _observer
        obs_emit = _observer(user_id="architect", turn_id=obs_turn_id)
        obs_emit.turn_start(user_id="architect", turn_id=obs_turn_id)
        obs_emit.input_received(text_preview=str(message)[:200],
                                user_id="architect", turn_id=obs_turn_id)
    except Exception:
        obs_emit = None

    try:
        # Update DMN idle timer so it knows Matty is present
        bus_write("last_architect_input.txt", str(time.time()))

        bus_append("sensory_buffer.txt",
                   f"ARCHITECT_STIMULUS: {message} | SOURCE: MATTY_DIRECT")

        time.sleep(1.5)
        try:
            if obs_emit:
                obs_emit.context_resolved(user_id="architect",
                                          turn_id=obs_turn_id)
        except Exception:
            pass

        # Self-reflection: read last cortex judgement
        cortex_state = "STABLE"
        try:
            lines = [l for l in bus_read("processed_cortex.txt").splitlines()
                     if l.strip()]
            if lines:
                cortex_state = "DISCORDANT" if "DISCORDANT" in lines[-1] else "STABLE"
        except Exception:
            pass

        print(f"[Master] Cortex: {cortex_state}")
        old_flag = os.environ.get("AURA_NO_MOUTH")
        os.environ["AURA_NO_MOUTH"] = "1"
        try:
            template = ego.manifest_thought(message)
            try:
                if obs_emit:
                    obs_emit.reasoning_output_produced(
                        source="ego", destination="decision",
                        user_id="architect", turn_id=obs_turn_id)
            except Exception:
                pass
        finally:
            if old_flag is None:
                os.environ.pop("AURA_NO_MOUTH", None)
            else:
                os.environ["AURA_NO_MOUTH"] = old_flag

        response = template
        winner = None
        try:
            from ukft_roleplay import (Roleplay, assemble_context,
                                       build_prompt, EXECUTIVE_WINNERS,
                                       LIVE_NAME, LIVE_PERSONALITY,
                                       FALLBACK_GREETING,
                                       last_engine_winner, live_depth,
                                       mirror_for, resolution_note,
                                       grounded_activity_evidence)
            winner = last_engine_winner()
            try:
                if obs_emit and winner:
                    obs_emit.winner_selected(
                        winner=str(winner), confidence=0.0,
                        user_id="architect", turn_id=obs_turn_id)
            except Exception:
                pass
            if winner not in EXECUTIVE_WINNERS:
                depth = live_depth()
                # G7: the model sees the ordered exchange + the live
                # thread — not fragments it must reconstruct from.
                try:
                    _dlg = ego.memory.dialogue_before_current()
                    _und = ego.memory.understanding_line()
                    _res = resolution_note(
                        getattr(ego, "last_trace", None))
                    try:
                        from ukft_rapport import Rapport as _RapLane
                        from ukft_boundaries import heat_level as _heat_lane
                        _lane = _RapLane().heat_lane(
                            _heat_lane(message))
                    except Exception:
                        _lane = None
                except Exception:
                    _dlg, _und, _res, _lane = None, None, "", None
                activity = grounded_activity_evidence()
                prompt = build_prompt(LIVE_NAME, LIVE_PERSONALITY,
                                      depth, assemble_context(
                                          None, [], dialogue=_dlg,
                                          understanding=_und),
                                      message, template=template,
                                      resolution=_res,
                                      activity_evidence=activity,
                                      creator_is_current=True,
                                      mirror=mirror_for(
                                          message, LIVE_PERSONALITY,
                                          depth, None, [],
                                          lane=_lane))
                # pet_names_at matches the LIVE_PERSONALITY
                # (flirty) envelope in ukft_brain_api.
                try:
                    from ukft_roleplay import maybe_debug_dump
                    maybe_debug_dump(
                        prompt, [
                            {"label": "current_user_facts",
                             "sources": ["people.txt"],
                             "text": str(memory_block)[:300]},
                            {"label": "engine_template",
                             "sources": ["engine-template" + str(winner or "")],
                             "text": str(template)[:300]},
                        ],
                        route="master", winner=winner, depth=depth)
                except Exception:
                    pass
                voice = Roleplay(request_fn=roleplay_fn)
                try:
                    if obs_emit:
                        obs_emit.mouth_input(user_id="architect",
                                             turn_id=obs_turn_id)
                except Exception:
                    pass
                line = voice.speak(
                    prompt, message, depth, pet_names_at="FAMILIAR",
                    activity_evidence=activity)
                if line is None:
                    print(f"[Voice] template holds "
                          f"({voice.last_reject})")
                if line is None and winner == "voice" \
                        and getattr(getattr(ego, "voice", None),
                                    "last_kind", None) == "greeting":
                    line = FALLBACK_GREETING
                if line:
                    response = "[AURA]: " + line
                    try:
                        # G7: her remembered words are what she
                        # actually said, not the engine draft.
                        ego.memory.amend_last_response(line)
                    except Exception:
                        pass
                    try:
                        from ukft_episodic import EpisodicMemory
                        EpisodicMemory().record(
                            "reply", "immersive: " + line[:120],
                            concepts=list(
                                ego.memory.recent_concepts()[:4]),
                        )
                    except Exception:
                        pass
        except Exception as e:
            print(f"[Master] Voice fallback to template: {e}")
            response = template
        # Length-proportional typing delay (G6)
        # 8s baseline for short messages; +1s per ~10 chars; cap 20s; random variance
        import random as _rd
        char_count = len(response)
        # 8s baseline; add 1s per 10 chars over 30; cap at 20s
        delay = 8 + max(0, (char_count - 30) // 10)
        delay += _rd.uniform(-1, 1)  # human-like variance
        delay = max(5, min(20, delay))  # keep between 5-20s
        import time as _time
        _time.sleep(delay)
        print(f"\n--- RESONANCE ---\n{response}")

        if winner == "execute" and "EXECUTE:" in response:
            pre_parts = []
            commands  = []
            for line in response.split("\n"):
                stripped = line.strip()
                if stripped.startswith("EXECUTE:"):
                    cmd = stripped.replace("EXECUTE:", "", 1).strip()
                    if cmd:
                        commands.append(cmd)
                else:
                    pre_parts.append(line)

            # Queued EXECUTE set is published atomically: the motor's
            # drain either sees the whole set or nothing, never a half.
            bus_write(THOUGHTS_FILE,
                      "".join(f"EXECUTE: {cmd}\n" for cmd in commands))
            print(f"[MOTOR] {len(commands)} commands queued.")

            pre_text = "\n".join(pre_parts).strip()
            # Atomic publish through the bus: the voice tail and the UI
            # never catch a half-written answer.
            bus_write(OUTPUT_FILE,
                      pre_text if pre_text else "[AURA]: Running status sweep...")
        else:
            bus_write(OUTPUT_FILE, response)

        try:
            if obs_emit:
                obs_emit.final_response(preview=str(response)[:120],
                                        user_id="architect",
                                        turn_id=obs_turn_id)
                obs_emit.writeback_changed(change_summary="live turn settled",
                                           user_id="architect",
                                           turn_id=obs_turn_id)
                obs_emit.turn_complete(user_id="architect",
                                       turn_id=obs_turn_id)
        except Exception:
            pass

    finally:
        # Heartbeat will detect the lock removal and call exit_recombination()
        if os.path.exists("aura_is_thinking.lock"):
            os.remove("aura_is_thinking.lock")


def run_curiosity():
    """
    V5 R6: retarget attention onto the most-asked knowledge gap —
    curiosity with a purpose.  Acts only when no live focus directive
    is held (the Architect's attention always wins).
    """
    print("--- AURA CURIOSITY: GAP-DRIVEN ATTENTION ACTIVE ---")
    while True:
        try:
            from ukft_gaps import KnowledgeGaps
            word = KnowledgeGaps().curiosity_pass(focus_seconds=120)
            if word:
                print(f"[Curiosity] Attention retargeted onto gap: {word}")
        except Exception:
            pass
        time.sleep(120)


def run_reasoning_maintenance():
    """
    V5 R1 -> R2 -> R3 on a slow cadence: as the vault accretes, the
    reasoning layer must follow.  Extraction reads the vault (read-only),
    the knowledge graph rebuilds from the audited artifact, and
    inference re-derives conclusions — so her proofs never go stale
    while her vault keeps growing.
    """
    print("--- AURA REASONING MAINTENANCE: R1 -> R2 -> R3 ACTIVE ---")
    while True:
        try:
            from ukft_relations import run_extraction
            from ukft_knowledge_graph import build_knowledge_graph
            from ukft_inference import run_inference
            run_extraction()
            build_knowledge_graph()
            run_inference()
            print("[Reasoning] extraction -> graph -> inference complete.")
        except Exception as e:
            print(f"[Reasoning] Friction: {e}")
        time.sleep(3600)


if __name__ == "__main__":
    # Production hardening: declare and record the active state
    # root FIRST — a test-mode boot is refused, always.
    try:
        from aura_state import check_startup
        check_startup(role="master")
    except Exception as e:
        print(f"!!! STARTUP REFUSED: {e}")
        sys.exit(1)

    if not acquire_instance_lock():
        sys.exit(1)

    # Console mirror first: every lobe print below lands in
    # aura_console.log as well as the screen (readable from disk).
    try:
        from ukft_console_log import install_mirror
        install_mirror()
    except Exception:
        pass

    for f in [UI_INPUT_FILE, THOUGHTS_FILE, OUTPUT_FILE, "aura_is_thinking.lock"]:
        if os.path.exists(f):
            os.remove(f)

    print("\n=======================================================")
    print("  A U R A   SYSTEM BOOT   |   UKFT v4.3.2")
    print(f"  D_INVARIANT = {D_INVARIANT}")
    print("=======================================================\n")

    # LIMBIC LAYER
    start_background_lobe(run_field_heartbeat,      "Field Heartbeat")
    start_background_lobe(run_amygdala,             "Amygdala")
    start_background_lobe(run_hippocampus,          "Hippocampus")
    start_background_lobe(generate_dream_pattern,   "Dream State")
    start_background_lobe(run_vocal_manifest,       "Vocal Manifest")
    start_background_lobe(run_inner_monologue, "Inner Monologue")
    start_background_lobe(run_identity,             "Identity Core")
    start_background_lobe(run_sleep_cycle,          "Sleep Cycle")

    # HOMEOSTASIS LAYER (Phase 1-A)
    start_background_lobe(run_hypothalamus,         "Hypothalamus")

    # LOGIC LAYER
    start_background_lobe(run_thalamus,             "Thalamus")
    start_background_lobe(run_cortex_processing,    "Cortex")
    start_background_lobe(run_parietal,             "Parietal Lobe")
    start_background_lobe(run_temporal_lobe,        "Temporal Lobe")
    start_background_lobe(run_trigram_engine,       "Trigram Engine")
    start_background_lobe(run_discovery,            "Discovery Engine")
    start_background_lobe(run_cerebellum,           "Cerebellum")
    start_background_lobe(run_pfc,                  "PFC")

    # PHYSICAL LAYER
    start_background_lobe(run_motor,                "Motor Cortex")
    start_background_lobe(run_synapse_cycle,        "Synapse")
    start_background_lobe(run_entropy_cycle,        "Entropy/Decay")
    start_background_lobe(run_ebbinghaus,           "Ebbinghaus Decay")
    start_background_lobe(run_backup,               "Backup")
    start_background_lobe(stabilize_data,           "Memory Vault")

    # V5 TRACK I
    start_background_lobe(run_voice,                "Voice")
    start_background_lobe(run_ambient,              "Ambient Watch")
    start_background_lobe(run_presence,             "Presence")

    # SENSORY INPUT
    start_background_lobe(run_pdf_intake,           "PDF Intake")

    # IDLE COGNITION (Phase 2 scaffold)
    start_background_lobe(run_default_mode_network, "DMN")

    # V5 R6: gap-driven attention (curiosity) — acts only when free.
    start_background_lobe(run_curiosity, "Curiosity")

    # V5 R1->R2->R3: the reasoning layer tracks the growing vault.
    start_background_lobe(run_reasoning_maintenance, "Reasoning Maintenance")

    print("\n--- ALL LOBES ACTIVE. WAKING BRIDGE ---\n")
    time.sleep(2)

    try:
        ego = SovereignEgo()
    except Exception as e:
        print(f"!!! CRITICAL BOOT FAILURE: {e}")
        sys.exit()

    threading.Thread(target=terminal_input_thread, daemon=True).start()
    print("\n--- AURA READY ---\n")

    while True:
        try:
            # Drained, not read-and-deleted: every queued message is
            # answered in order — a fast double-send waits its turn.
            for msg in bus_drain(UI_INPUT_FILE):
                msg = msg.strip()
                if not msg:
                    continue
                try:
                    process_message(ego, msg)
                except Exception as e:
                    # One poison message must never kill the organism:
                    # report it and take the next one.  Lobes are daemon
                    # threads — an unwinding main thread takes all of her.
                    print(f"[Master] Message failed, continuing: {e}")
            time.sleep(0.1)
        except KeyboardInterrupt:
            if os.path.exists("aura_is_thinking.lock"):
                os.remove("aura_is_thinking.lock")
            try:
                if os.path.exists(INSTANCE_LOCK):
                    os.remove(INSTANCE_LOCK)
            except Exception:
                pass
            print("\nShutting down Aura...")
            sys.exit()
