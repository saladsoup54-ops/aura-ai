# ukft_synapse.py — AURA Sensory Input / Internet Connection
# ============================================================
# REVISION: Added WEB_RESONANCE alongside WIKI_RESONANCE.
# Phase 1: checks hypothalamus_signal.txt and pfc_signal.txt
# before writing to the sensory buffer.
# ============================================================

import time
import requests
import os
import random
import hashlib
from collections import deque

from aura_bus import append as bus_append, read as bus_read
from aura_state import resolve_state_path as _sp
from ukft_sleep import is_asleep

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("[Synapse] WARNING: beautifulsoup4 not installed. Run: pip install beautifulsoup4")
    print("[Synapse] Falling back to WIKI_RESONANCE only.")


class CaptureFilter:
    """
    FIFO hash filter: the same feed page is captured once per session.
    Re-feeding identical pages every cycle wasted sensory-buffer slots,
    cortex judgements and field stimulation — the vault-side dedup only
    caught the final write.  True FIFO eviction (not set.pop) so recent
    pages stay deduped while old ones may legitimately reappear.
    """

    def __init__(self, maxlen=500):
        self.maxlen = maxlen
        self._seen = set()
        self._order = deque()

    def is_new(self, key):
        digest = hashlib.md5(key.encode("utf-8", "ignore")).hexdigest()
        if digest in self._seen:
            return False
        self._seen.add(digest)
        self._order.append(digest)
        if len(self._order) > self.maxlen:
            self._seen.discard(self._order.popleft())
        return True


_capture_filter = CaptureFilter()

WEB_FEEDS = [
    "https://phys.org/space-news/",
    "https://www.sciencedaily.com/news/space_time/",
    "https://news.ycombinator.com",
    "https://www.quantamagazine.org",
    "https://arxiv.org/list/gr-qc/recent",
    "https://arxiv.org/list/astro-ph/recent",
]

WEB_BROWSE_RATIO  = 0.6
VAULT_FILE        = "sensory_buffer.txt"
# Backpressure that can actually trip: the old 90 GB ceiling could never
# fire before the disk did.  50 MB of unprocessed sensory backlog means
# the pipeline is behind — rest instead of piling on.
MAX_MASS          = 50000000
HYPO_SIGNAL_FILE  = "hypothalamus_signal.txt"
PFC_SIGNAL_FILE   = "pfc_signal.txt"


def read_signal(filepath):
    return bus_read(filepath).strip()


def check_saturation():
    if os.path.exists(VAULT_FILE):
        if os.path.getsize(VAULT_FILE) >= MAX_MASS:
            return True
    return False


def fetch_web_feed(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        return None, None
    soup       = BeautifulSoup(response.text, "html.parser")
    title_tag  = soup.find("title")
    anchor     = title_tag.get_text(strip=True)[:60] if title_tag else url
    paragraphs = soup.find_all("p")
    raw_text   = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)
    clean_text = " ".join(raw_text.split())
    summary    = clean_text[:150] if clean_text else "No readable content found."
    return anchor, summary


def run_synapse_cycle():
    print("AURA Synapse: CONNECTING TO WIKI_RESONANCE + WEB_RESONANCE...")

    wiki_url     = "https://en.wikipedia.org/api/rest_v1/page/random/summary"
    wiki_headers = {"User-Agent": "AuraCognitionSystem/1.1 (Learning Project)"}

    while True:
        if os.path.exists(_sp("aura_is_thinking.lock")):
            time.sleep(1)
            continue

        # Phase 5-B: the internet rests while she sleeps.
        if is_asleep():
            time.sleep(5)
            continue

        # Respect homeostasis and PFC directives
        hypo = read_signal(HYPO_SIGNAL_FILE)
        pfc  = read_signal(PFC_SIGNAL_FILE)
        if "INHIBIT" in hypo or "THROTTLE" in pfc:
            time.sleep(2)
            continue

        if check_saturation():
            print("Synapse: Manifold full. Sleeping.")
            time.sleep(3600)
            continue

        use_web = (
            BS4_AVAILABLE
            and len(WEB_FEEDS) > 0
            and random.random() < WEB_BROWSE_RATIO
        )

        if use_web:
            target_url = random.choice(WEB_FEEDS)
            try:
                anchor, summary = fetch_web_feed(target_url)
                if anchor and summary:
                    if not _capture_filter.is_new(f"WEB|{anchor}|{summary}"):
                        print(f"[Synapse] Web repeat skipped: {anchor[:50]}")
                    else:
                        entry = (
                            f"ANCHOR: {anchor} | "
                            f"DATA: {summary} | "
                            f"SOURCE: WEB_RESONANCE"
                        )
                        bus_append(VAULT_FILE, entry)
                        print(f"[Synapse] Web Captured: {anchor[:50]}")
                else:
                    print(f"[Synapse] Web Friction: {target_url} returned no content.")
            except Exception as e:
                print(f"[Synapse] Web Friction: {e} — falling back to Wiki next cycle.")
        else:
            try:
                response = requests.get(wiki_url, headers=wiki_headers, timeout=10)
                if response.status_code == 200:
                    data    = response.json()
                    anchor  = data.get("title", "Unknown")
                    summary = data.get("extract", "No data")[:100]
                    if not _capture_filter.is_new(f"WIKI|{anchor}|{summary}"):
                        print(f"Synapse repeat skipped: {anchor[:50]}")
                    else:
                        entry   = (
                            f"ANCHOR: {anchor} | "
                            f"DATA: {summary} | "
                            f"SOURCE: WIKI_RESONANCE"
                        )
                        bus_append(VAULT_FILE, entry)
                        print(f"Synapse Captured: {anchor}")
                else:
                    print(f"Synapse Friction: Wikipedia blocked us (Status: {response.status_code})")
            except Exception:
                print("Synapse Friction: Connection Lost or Timeout. Resting...")

        time.sleep(10)


if __name__ == "__main__":
    run_synapse_cycle()
