"""AURA regression suite runner.

Runs every verification script in its own throwaway temp sandbox with
PYTHONPATH pointed at the repo root, so no workspace state is touched.

Usage:
    python tests/run_all.py
"""
import os
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(REPO, "tests")

SUITES = [
    ("Pass 0.5 - unblock the organism", "verify_pass05.py"),
    ("Pass 0.6 - vault contract",       "verify_pass06.py"),
    ("Pass 0.7 - pipeline hygiene",     "verify_pass07.py"),
    ("Phase 2-E - reticular formation", "verify_2e.py"),
    ("Phase 2-C - temporal co-occurrence", "verify_2c.py"),
    ("Phase 2-D - basal ganglia selection", "verify_2d.py"),
    ("Phase 3-A - vault-trained trigram", "verify_3a.py"),
    ("Phase 3-B - working memory buffer", "verify_3b.py"),
    ("Phase 3-C - grammar skeleton",      "verify_3c.py"),
    ("Phase 3 - full integration battery", "verify_3full.py"),
    ("Phase 4-A - spontaneous output",   "verify_4a.py"),
    ("Phase 4-B - conceptual discovery", "verify_4b.py"),
    ("Phase 4-C - attention director",   "verify_4c.py"),
    ("Phase 4-D - self-modifying identity", "verify_4d.py"),
    ("Phase 5-B - sleep/wake cycle",     "verify_5b.py"),
    ("Phase 5-C - episodic/semantic split", "verify_5c.py"),
    ("Phase 5-D - Ebbinghaus decay",     "verify_5d.py"),
    ("Phase 5-A - message bus",          "verify_5a.py"),
    ("Backup & restore",                 "verify_backup.py"),
    ("V5 R1 - relation extraction",      "verify_r1.py"),
    ("V5 R2 - knowledge graph store",    "verify_r2.py"),
    ("V5 R3 - inference engine",         "verify_r3.py"),
    ("V5 R4 - question understanding",   "verify_r4.py"),
    ("V5 R5 - answer composition",       "verify_r5.py"),
    ("V5 R6 - honest ignorance",        "verify_r6.py"),
    ("V5 R7 - evaluation harness",      "verify_r7.py"),
    ("V5 I1 - voice",                   "verify_i1.py"),
    ("V5 I2 - tool registry",           "verify_i2.py"),
    ("V5 I3 - ambient watch",           "verify_i3.py"),
    ("V5 I4 - presence",                "verify_i4.py"),
    ("Synapse view helpers",            "verify_view.py"),
    ("Hebbian + connect() proof",       "proof_hebbian.py"),
    ("Pass 0.8 - field breathing room",  "verify_pass08.py"),
    ("Pass 0.9 - organic mornings",      "verify_pass09.py"),
    ("Execution safety (audit 1)",       "verify_safety.py"),
    ("Race contracts (audit 2)",         "verify_races.py"),
    ("Upkeep (audit 5)",                 "verify_upkeep.py"),
    ("Console mirror",                   "verify_console.py"),
    ("V6 C1 - time & situation",         "verify_c1.py"),
    ("V6 C2 - people model",             "verify_c2.py"),
    ("V6 C3 - architect model",          "verify_c3.py"),
    ("V6 C4 - recall",                   "verify_c4.py"),
    ("V6 C5 - context assembly",         "verify_c5.py"),
    ("V6 C7 - self-model",               "verify_c7.py"),
    ("V6 C6 - agenda",                   "verify_c6.py"),
    ("V6 C10 - belief & trust",          "verify_c10.py"),
    ("V6 C9 - mouth (swappable)",        "verify_c9.py"),
    ("V6 C8 - self-teaching",            "verify_c8.py"),
    ("V6 C11 - perpetual engineering",   "verify_c11.py"),
    ("Diagnostics sweep",                "verify_diag.py"),
    ("V7 F1 - register overhaul",        "verify_f1.py"),
    ("V7 F2 - quote-first fallback",     "verify_f2.py"),
    ("V7 F3 - affect mapping",           "verify_f3.py"),
    ("V7 F4 - conversational policy",    "verify_f4.py"),
    ("V7 F5 - claim-level verification", "verify_f5.py"),
    ("V7 F7 - neural voice driver",      "verify_f7.py"),
    ("G1 - multi-instance leakage proof", "verify_g1_leakage.py"),
    ("G3 - immersive roleplay voice", "verify_g_roleplay.py"),
    ("Live loop voice (master + runner)", "verify_g_livevoice.py"),
    ("G5 - safety & boundaries", "verify_g5_safety.py"),
    ("G2 - character packs", "verify_g2_packs.py"),
    ("G4 - discord adapter", "verify_g4_discord.py"),
    ("G6 - memory delight", "verify_g6_delight.py"),
    ("Growth readout + mirror", "verify_g_growth.py"),
    ("Observer telemetry contract", "verify_observatory_contract.py"),
    ("G7 - conversational context", "verify_g7_context.py"),
    ("G8 - rapport engine", "verify_g8_rapport.py"),
    ("G9 - interlocutor + grounded activity", "verify_g9_interlocutor.py"),
    ("M5 - causal influence harness", "verify_m5_causal.py"),
    ("M1 - memory relevance gate", "verify_m1_relevance.py"),
    ("M2 - thread suppression", "verify_m2_thread_suppression.py"),
    ("M3 - reasoning priority", "verify_m3_reasoning_priority.py"),
    ("M4 - real selection context", "verify_m4_selection_context.py"),
    ("M13 - contradiction gating", "verify_m13_contradiction_gating.py"),
    ("GF-OLD BRAIN PASS 1 - experience enters old brain", "verify_brain_gf_pass1.py"),
    ("GF-OLD BRAIN PASS 1A - real turn persistence", "verify_brain_gf_pass1a.py"),
    ("TARGET LOOP PASS 2 - brain-owned stance/intent", "verify_loop_pass2.py"),
    ("M14 - episodic influence policy", "verify_m14_episodic_influence.py"),
    ("M16 - full-route observability", "verify_m16_full_route_observability.py"),
    ("Finding #1 - empty-state copyback", "verify_finding01_empty_copyback.py"),
    ("Finding #2 - partition ownership", "verify_finding02_partition_ownership.py"),
    ("Finding #4 - transactional writeback", "verify_finding04_transactional_writeback.py"),
    ("Finding #6 - shadow context", "verify_finding06_shadow_context.py"),
    ("Finding #8 - lesson correction", "verify_finding08_lessons_correction.py"),
    ("Finding #9 - trust importance", "verify_finding09_trust_importance.py"),
    ("Finding #10 - memory writes journal", "verify_finding10_memory_writes_journal.py"),
    ("Finding #11 - personality / boundary authority", "verify_finding11_personality_boundary_authority.py"),
    ("Finding #12 - amygdala causality", "verify_finding12_amygdala_causality.py"),
    ("Finding #14 - pack-knob product contract", "verify_finding14_pack_knob_contract.py"),
    ("CN0 - conversational baseline trace", "verify_cn0_conversation_trace.py"),
    ("Production isolation proof", "verify_isolation.py"),
]


def main():
    env = dict(os.environ)
    env["PYTHONPATH"] = REPO + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    # V6 C9: suites prove the template path and the mouth through
    # fakes — no suite may depend on (or wait for) a live daemon.
    env["AURA_NO_MOUTH"] = "1"

    # Production hardening: every suite gets its OWN declared temp
    # state root (test mode). Live-state proof afterwards:
    #   HARD gate .... no new files at repo root (tests never create
    #                  root files; backups/ snapshots legitimately
    #                  appear, so that tree is pinned separately).
    #   HARD gate .... people.txt hash pinned (only live dialogue
    #                  writes it — precondition: don't chat with her
    #                  mid-run; ambient lobes never touch it).
    #   REPORTED ..... vault/graph/episodic/backups drift (her own
    #                  ambient intake churns these during any long
    #                  run; the isolation suite pins attack-impotence
    #                  in millisecond windows instead).
    sys.path.insert(0, REPO)
    from aura_state import live_state_hashes
    import hashlib as _hl

    def _root_files():
        try:
            return sorted(f for f in os.listdir(REPO)
                          if os.path.isfile(os.path.join(REPO, f)))
        except OSError:
            return []

    def _sha1_file(path):
        try:
            with open(path, "rb") as f:
                return _hl.sha1(f.read()).hexdigest()
        except OSError:
            return "<missing>"

    root_before = _root_files()
    people_before = _sha1_file(os.path.join(REPO, "people.txt"))
    drift_before = live_state_hashes()

    failed = 0
    for label, script in SUITES:
        with tempfile.TemporaryDirectory(prefix="aura_test_") as sandbox:
            print("=" * 62)
            print(f"RUN  {label}  ({script})")
            print("=" * 62)
            suite_env = dict(env)
            suite_env["AURA_TEST_MODE"] = "1"
            suite_env["AURA_STATE_ROOT"] = sandbox
            proc = subprocess.run(
                [sys.executable, os.path.join(TESTS, script)],
                cwd=sandbox, env=suite_env,
                capture_output=True, text=True,
                encoding="utf-8", errors="replace",
            )
            tail = proc.stdout.strip().splitlines()[-3:]
            for line in tail:
                print(line)
            # Live-state probe: check if locked_patterns.txt was touched
            locked_path = os.path.join(REPO, "locked_patterns.txt")
            if os.path.exists(locked_path):
                locked_h = _sha1_file(locked_path)
                if locked_h != drift_before.get("locked_patterns.txt"):
                    print(f"  *** PROBE: locked_patterns.txt modified by {label}")
            if proc.returncode != 0:
                failed += 1
                if proc.stderr.strip():
                    print("STDERR:", proc.stderr.strip()[-600:])

    print("=" * 62)
    print(f"RESULT: {len(SUITES) - failed}/{len(SUITES)} suites passed")
    live_ok = True
    root_after = _root_files()
    litter = sorted(set(root_after) - set(root_before))
    if litter:
        print(f"LIVE-STATE VIOLATION: new root files: {litter}")
        live_ok = False
    if _sha1_file(os.path.join(REPO, "people.txt")) != people_before:
        print("LIVE-STATE VIOLATION: people.txt changed "
              "(no test may write it; live dialogue also writes it — "
              "do not chat with her mid-run).")
        live_ok = False
    drift_after = live_state_hashes()
    for key in drift_before:
        if drift_before[key] != drift_after.get(key):
            print(f"LIVE DRIFT (ambient, reported): {key}")
    if live_ok:
        print("LIVE STATE: clean (no litter, people.txt pinned).")
    else:
        return 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

