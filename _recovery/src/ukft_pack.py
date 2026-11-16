# ukft_pack.py — Character packs (G2, G8: ten starters)
# ==========================================================
# One folder per character under characters/<id>/:
#   pack.json — id, name, personality, interests, voice, knobs
#   seed.md   — "- " bullets become GIVEN vault anchors at birth
#   boundaries.md (optional) — per-pack overlay; the global floor
#               (gf_boundaries.md) always wins conflicts.
#
# The loader validates and fills defaults; the brain consumes
# personality + interests + name today, knobs are contract for
# G3/G4 (documented, not silently ignored).
# ==========================================================

import json
import os

try:
    from aura_state import asset_path as _asset_path
    PACK_DIR = _asset_path("characters")
except Exception:
    PACK_DIR = os.path.join(os.path.dirname(__file__), "characters")

PERSONALITIES = ("nerdy", "shy", "bossy", "flirty", "bold", "gentle",
                 "playful", "earnest", "fierce", "dreamy")

PACK_DEFAULTS = {
    "voice_model": "aura-mouth-3b-cpu",
    "voice_temperature": 0.7,
    "question_back": 0.5,
    "initiative": "medium",
    "version": 1,
}


def pack_path(pack_id):
    safe = "".join(c if c.isalnum() or c in "-_" else "_"
                   for c in str(pack_id or ""))
    return os.path.join(PACK_DIR, safe)


def list_packs(base_dir=PACK_DIR):
    """Sorted pack ids with a valid pack.json."""
    try:
        names = sorted(os.listdir(base_dir))
    except OSError:
        return []
    return [n for n in names
            if os.path.isfile(os.path.join(base_dir, n, "pack.json"))]


def load_pack(pack_id, base_dir=PACK_DIR):
    """Validated pack dict. Raises ValueError naming the problem."""
    path = os.path.join(base_dir, str(pack_id), "pack.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        raise ValueError(f"pack not found or unreadable: {pack_id}")
    if not isinstance(data, dict):
        raise ValueError(f"pack is not an object: {pack_id}")
    personality = str(data.get("personality", "")).lower()
    if personality not in PERSONALITIES:
        raise ValueError(
            f"pack {pack_id}: personality must be one of "
            f"{', '.join(PERSONALITIES)}")
    pack = dict(PACK_DEFAULTS)
    pack.update({k: v for k, v in data.items()
                 if v is not None})
    pack["id"] = str(pack_id)
    pack["personality"] = personality
    pack["name"] = str(pack.get("name", "Aura")).strip() or "Aura"
    interests = pack.get("interests", [])
    pack["interests"] = [str(i) for i in interests
                         if str(i).strip()][:8]
    # Boundaries overlay: floor file always wins; overlay only adds.
    overlay = os.path.join(base_dir, str(pack_id), "boundaries.md")
    pack["boundaries_overlay"] = overlay if os.path.isfile(overlay) \
        else None
    return pack


def seed_anchors(pack_id, base_dir=PACK_DIR):
    """'- ' bullets from seed.md as canonical GIVEN anchors."""
    path = os.path.join(base_dir, str(pack_id), "seed.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        s = line.strip()
        if s.startswith("- ") and len(s) > 2:
            clean = s[2:].strip().replace("|", "/")[:220]
            if clean:
                out.append(f"ANCHOR: Founding Seed | DATA: {clean} "
                           f"| SOURCE: GIVEN")
    return out
