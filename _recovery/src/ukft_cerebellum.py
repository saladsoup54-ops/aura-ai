import time
from aura_field import FIELD

def run_cerebellum():
    """
    The Predictive Engine.

    FIX: The old version was truncated — the loop body ended
    mid-function. This complete version adds forward-priming:
    when the cerebellum predicts the next node, it pre-charges
    that node at 0.05 so it's already warming up before it fires.
    This makes Aura's cognitive transitions smoother and faster.
    """
    print("--- AURA CEREBELLUM: PREDICTIVE ENGINE ACTIVE ---")
    last_prediction = None

    while True:
        try:
            # Decide under the lock, act outside it: holding the global
            # field lock across console I/O stalled every reader, and
            # FIELD.stimulate() takes the lock itself anyway.
            with FIELD.lock:
                if not FIELD.nodes:
                    current = None
                else:
                    # Find the current dominant thought
                    active_nodes = sorted(
                        FIELD.nodes.values(),
                        key=lambda n: n.activation,
                        reverse=True
                    )

                    current = None
                    if active_nodes and active_nodes[0].activation > 0.6:
                        current_thought = active_nodes[0]

                        if current_thought.connections:
                            # Predict next node = strongest connection
                            predicted_node = max(
                                current_thought.connections,
                                key=current_thought.connections.get
                            )
                            current = (current_thought.name,
                                       predicted_node.name)

            if current is not None:
                current_name, predicted_name = current
                if predicted_name != (last_prediction[1] if last_prediction else None):
                    print(f"[Cerebellum] Prediction: "
                          f"{current_name} -> {predicted_name}")
                    last_prediction = current

                # FORWARD-PRIMING: pre-charge the predicted node
                # so it's already activating when the current
                # thought passes activation to it
                FIELD.stimulate(predicted_name, strength=0.05)

        except Exception as e:
            print(f"[Cerebellum] Friction: {e}")

        time.sleep(2)


if __name__ == "__main__":
    run_cerebellum()


