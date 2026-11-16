import requests

from aura_vault_io import append_anchor

try:
    from urllib.parse import quote as _urlquote
except Exception:
    def _urlquote(s, safe=""):
        return s.replace(" ", "_")

VAULT_FILE = "locked_patterns.txt"
target_concept = "Humanity"


def inject_specific_synapse(concept):
    print(f"AURA Directed Synapse: FOCUSING ON {concept}...")
    url = ("https://en.wikipedia.org/api/rest_v1/page/summary/"
           f"{_urlquote(str(concept), safe='')}")

    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print(f"Synapse Friction: HTTP {response.status_code} "
                  f"for {concept}")
            return
        data = response.json()
        anchor = data.get("title", "Unknown")
        summary = data.get("extract", "No data")[:100]

        written = append_anchor(VAULT_FILE, anchor, summary,
                                source="DIRECTED_WIKI_RESONANCE")

        print(f"Synapse Locked: {anchor}" if written
              else f"Synapse Skipped (duplicate): {anchor}")
    except Exception as e:
        print(f"Synapse Friction: {e}")


if __name__ == "__main__":
    inject_specific_synapse(target_concept)
