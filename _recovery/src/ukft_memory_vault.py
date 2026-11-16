import os
import time

from aura_state import resolve_state_path

VAULT_FILE   = "locked_patterns.txt"
COMPACT_FLAG = "vault_compacted_v2.flag"


def _p(name):
    return resolve_state_path(name)


def stabilize_data():
    print("Memory Vault Stabilizer Active in Local Manifold...")
    vault = _p(VAULT_FILE)
    flag = _p(COMPACT_FLAG)
    try:
        os.makedirs(os.path.dirname(vault), exist_ok=True)
    except Exception:
        pass

    if not os.path.exists(vault):
        with open(vault, "w") as f:
            f.write("--- AURA SOVEREIGN VAULT INITIALIZED ---\n")

    if not os.path.exists(flag):
        # Phase 0.6 one-time migration.  The old comment claimed the
        # 120 s sleep made this race-free — it does not: sleeping holds
        # no lock, and every reader/writer runs during and after it.
        # Safety now comes from compact_vault itself (locked temp-file
        # rewrite), not from waiting.
        time.sleep(120)
        compacted = False
        try:
            from aura_vault_io import compact_vault
            stats = compact_vault(vault, _p("locked_patterns_legacy.txt"))
            print(f"[Vault] One-time compaction done: {stats}")
            compacted = True
        except Exception as e:
            print(f"[Vault] Compaction friction: {e}")
        if compacted:
            try:
                with open(flag, "w") as f:
                    f.write("done")
            except Exception:
                pass

    while True:
        # Ensure the file exists and stays healthy. Append-side dedup is
        # handled by aura_vault_io.append_anchor; PATTERN noise is gone
        # since Phase 0.6 (dream state writes to dream_log.txt).
        if not os.path.exists(vault):
            with open(vault, "w") as f:
                f.write("--- AURA SOVEREIGN VAULT INITIALIZED ---\n")
        time.sleep(60)  # Runs once a minute


if __name__ == "__main__":
    stabilize_data()
