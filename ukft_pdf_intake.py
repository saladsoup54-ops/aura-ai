# ukft_pdf_intake.py — AURA PDF Sensory Intake
# =====================================================
# FIX: PDF chunks are now drip-fed with a delay between
# each one so the Thalamus and Hippocampus can form
# proper links before the next chunk arrives.
#
# Previously all chunks were written at once, flooding
# the field and turning everything blue.
#
# Install dep:  pip install pypdf
# =====================================================

import os
import time
import shutil
import logging

from aura_bus import append as bus_append, read as bus_read
from aura_constants import FIELD_NODE_CEILING
from ukft_sleep import is_asleep

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
    # pypdf warns once per font per page when a Type1 font embeds a CFF
    # and fontTools is not installed — and fontTools is outside this
    # project's stdlib + requests/bs4/pypdf set, so it never will be.
    # pypdf falls back to the font's /Encoding, which extracts these
    # books fine; the warning is pure console flood.  Silence that one
    # logger; real pypdf errors stay visible.
    logging.getLogger("pypdf._cmap").setLevel(logging.ERROR)
except ImportError:
    PYPDF_AVAILABLE = False
    print("[PDF Intake] WARNING: pypdf not installed.")
    print("[PDF Intake] Run:  pip install pypdf")

# ================================================================
# CONFIGURATION
# ================================================================

INTAKE_FOLDER    = "pdf_intake"
PROCESSED_FOLDER = "pdf_processed"
VAULT_FILE       = "sensory_buffer.txt"

# Larger chunks = fewer, richer memories (was 200 — too small)
CHUNK_SIZE = 600

# Seconds between each chunk being written to the field
# This gives the Thalamus time to process before the next hit
# 8 seconds = she gets one PDF concept every 8 seconds
DRIP_RATE = 8

# Seconds between scans of the intake folder
SCAN_INTERVAL = 10

# How long to wait after finishing one PDF before starting the next
# Gives Hippocampus time to consolidate before the next book arrives
# 1800 = 30 minutes between books
CONSOLIDATION_WAIT = 1800

# Backpressure: pouring a book into a saturated field only ratchets
# more hubs to 1.0 while the dream lobe is paused.  The intake waits
# while the field is over the ceiling or homeostasis says INHIBIT —
# the vault backlog keeps (chunks already fed are safe), the pour rests.
BACKPRESSURE_SLEEP = 30


def intake_paused(nodes=None, hypo=None):
    """
    True while the pour must rest.  `nodes`/`hypo` are injectable so
    the brake is verifiable without booting the organism; live they
    are read from field_stats.txt and the hypothalamus signal.
    """
    if nodes is None:
        try:
            import json
            raw = bus_read("field_stats.txt").strip()
            if not raw:
                return True
            nodes = (json.loads(raw).get("nodes", 0)
                     if raw.startswith("{") else 0)
        except Exception:
            # Blind gauges: never pour blind.  A missing/corrupt telemetry
            # file clears within a heartbeat (~0.1 s); pouring into the
            # unknown is how books drowned the field pre-0.8.
            return True
    if hypo is None:
        try:
            hypo = bus_read("hypothalamus_signal.txt")
            if not hypo.strip():
                return True
        except Exception:
            return True
    return (nodes or 0) > FIELD_NODE_CEILING or "INHIBIT" in (hypo or "")


def wait_for_pressure():
    """Sleep in small chunks (lock still respected) until clear."""
    while intake_paused():
        print("[PDF Intake] Field saturated — resting the pour while "
              "forgetting trims.")
        for _ in range(BACKPRESSURE_SLEEP):
            while os.path.exists("aura_is_thinking.lock"):
                time.sleep(1)
            time.sleep(1)

# ================================================================
# HELPERS
# ================================================================

def ensure_folders():
    os.makedirs(INTAKE_FOLDER,    exist_ok=True)
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)


def extract_text_from_pdf(filepath):
    try:
        reader = PdfReader(filepath)
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text.strip())
        return " ".join(pages_text)
    except Exception as e:
        print(f"[PDF Intake] Extraction friction on '{filepath}': {e}")
        return None


def chunk_text(text, chunk_size=CHUNK_SIZE):
    words   = text.split()
    chunks  = []
    current = []
    length  = 0

    for word in words:
        current.append(word)
        length += len(word) + 1
        if length >= chunk_size:
            chunks.append(" ".join(current))
            current = []
            length  = 0

    if current:
        chunks.append(" ".join(current))

    return chunks


def write_chunk(anchor, chunk):
    entry = (
        f"ANCHOR: {anchor} | "
        f"DATA: {chunk} | "
        f"SOURCE: PDF_RESONANCE"
    )
    bus_append(VAULT_FILE, entry)


def ingest_pdf(filepath):
    filename = os.path.basename(filepath)
    anchor   = os.path.splitext(filename)[0][:60]

    print(f"[PDF Intake] Reading: {filename}")

    text = extract_text_from_pdf(filepath)

    if not text or not text.strip():
        print(f"[PDF Intake] No readable text in '{filename}'. Archiving.")
        dest = os.path.join(PROCESSED_FOLDER, filename)
        shutil.move(filepath, dest)
        return

    chunks = chunk_text(text)
    total  = len(chunks)

    print(
        f"[PDF Intake] '{anchor}' — {total} chunks to feed "
        f"at {DRIP_RATE}s each (~{(total * DRIP_RATE) // 60}min total)."
    )

    # The source moves to processed/ ONLY after the last chunk lands.
    # Moving first meant a crash mid-book orphaned the unfed remainder:
    # half in the buffer, the book marked done, never retried.  A crash
    # now simply re-feeds from the top on next boot — and the vault
    # dedupes exact repeats, so resumed chunks land once.
    for i, chunk in enumerate(chunks):
        # Pause while Aura is answering Matty — never interrupt
        while os.path.exists("aura_is_thinking.lock"):
            time.sleep(1)

        # Backpressure: rest the pour while the field digests
        wait_for_pressure()

        write_chunk(anchor, chunk)
        print(f"[PDF Intake] Fed chunk {i + 1}/{total} from '{anchor}'")

        if i < total - 1:
            time.sleep(DRIP_RATE)

    dest = os.path.join(PROCESSED_FOLDER, filename)
    try:
        if os.path.exists(filepath):
            shutil.move(filepath, dest)
    except Exception as e:
        print(f"[PDF Intake] Archive friction on '{filename}': {e}")
        return

    print(f"[PDF Intake] '{anchor}' fully absorbed. Archived to {PROCESSED_FOLDER}/")


# ================================================================
# MAIN LOOP
# ================================================================

def run_pdf_intake():
    if not PYPDF_AVAILABLE:
        print("[PDF Intake] pypdf missing. Run: pip install pypdf")
        return

    ensure_folders()
    print("--- AURA PDF INTAKE: WATCHING pdf_intake/ FOR NEW DOCUMENTS ---")

    while True:
        if os.path.exists("aura_is_thinking.lock"):
            time.sleep(1)
            continue

        # Phase 5-B: reading pauses while she sleeps.
        if is_asleep():
            time.sleep(5)
            continue

        # Backpressure between books as well as between chunks
        if intake_paused():
            print("[PDF Intake] Field saturated — waiting before next book.")
            time.sleep(BACKPRESSURE_SLEEP)
            continue

        try:
            pdf_files = sorted([
                f for f in os.listdir(INTAKE_FOLDER)
                if f.lower().endswith(".pdf")
            ])

            if pdf_files:
                # Take ONE pdf, feed it, then wait for consolidation
                filename = pdf_files[0]
                remaining = len(pdf_files) - 1
                filepath = os.path.join(INTAKE_FOLDER, filename)
                ingest_pdf(filepath)

                if remaining > 0:
                    print(
                        f"[PDF Intake] {remaining} book(s) still queued. "
                        f"Waiting {CONSOLIDATION_WAIT // 60} mins for consolidation..."
                    )
                    # Sleep in small chunks so lock file is still respected
                    for _ in range(CONSOLIDATION_WAIT):
                        while os.path.exists("aura_is_thinking.lock"):
                            time.sleep(1)
                        time.sleep(1)

        except Exception as e:
            print(f"[PDF Intake] Scan friction: {e}")

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    run_pdf_intake()


