import os
import time
from aura_field import FIELD

IDLE_THRESHOLD  = 45.0   # Seconds before Aura starts day-dreaming
IDLE_PULSE      = 0.1    # warm-up strength at zero activation
LAST_INPUT_FILE = "last_architect_input.txt"
INTERNAL_BUFFER = "internal_stimulus.txt"

# Pacing lives HERE, not in the presence timestamp: the old code
# rewrote last_architect_input.txt (the Architect's file!) with
# backdated values to throttle itself — falsifying another lobe's
# record through a raw-open side channel.
_next_eligible = 0.0


def idle_pulse(activation, base=IDLE_PULSE):
    """
    The idle warm-up pulse tapers as a node approaches saturation.

    A flat +0.1 pulse on the top nodes pinned a hub memory at 1.0
    forever (the Bible title monopolised her spontaneous speech).  With
    headroom scaling, a cold-but-relevant node is warmed while a hot
    node is left alone to decay — attention can rotate.
    """
    return base * max(0.0, 1.0 - max(0.0, min(1.0, activation)))


def run_default_mode_network():
    print("--- AURA DMN: DEFAULT MODE NETWORK ONLINE ---")
    global _next_eligible

    # Initialise the input timer only if no one has (a reboot must not
    # erase evidence the Architect was just here).
    if not os.path.exists(LAST_INPUT_FILE):
        with open(LAST_INPUT_FILE, "w") as f:
            f.write(str(time.time()))

    while True:
        time.sleep(5)

        try:
            if os.path.exists(LAST_INPUT_FILE):
                with open(LAST_INPUT_FILE, "r") as f:
                    last_time = float(f.read().strip())
            else:
                last_time = time.time()
        except Exception:
            last_time = time.time()

        idle_time = time.time() - last_time

        # Activate DMN if idle and not actively processing
        if idle_time > IDLE_THRESHOLD and not os.path.exists("aura_is_thinking.lock") \
                and time.time() >= _next_eligible:

            # Retrieve the most active nodes in the field
            with FIELD.lock:
                active_nodes = sorted(
                    [n for n in FIELD.nodes.values() if n.activation > 0.05],
                    key=lambda x: x.activation,
                    reverse=True
                )[:3]

            if active_nodes:
                concepts = [n.name for n in active_nodes]

                # Gently stimulate them so they don't decay completely —
                # tapered by headroom so a saturated memory is never
                # re-pinned (see idle_pulse).
                for node in active_nodes:
                    pulse = idle_pulse(node.activation)
                    if pulse > 0.0:
                        FIELD.stimulate(node.name, strength=pulse)

                # Push a thought seed to the internal buffer.  Queued,
                # not overwritten: a spark waiting unconsumed must not
                # be destroyed by the next one.
                thought_seed = f"DMN_SPARK: {' + '.join(concepts)}"
                try:
                    from aura_bus import append as bus_append
                    bus_append(INTERNAL_BUFFER, thought_seed)
                except Exception:
                    pass

                # Pace the idle thoughts naturally (own timer now —
                # the Architect's timestamp is never touched).
                _next_eligible = time.time() + (IDLE_THRESHOLD / 1.5)


if __name__ == "__main__":
    run_default_mode_network()
