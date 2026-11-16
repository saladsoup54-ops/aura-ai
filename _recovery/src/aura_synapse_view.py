"""AURA Synapse Visualiser — modernised with type hints & clean structure.
Run headless:  SDL_VIDEODRIVER=dummy python -m aura_synapse_view
or with --selftest to render frames + tab checks.
"""
from __future__ import annotations

import os
import sys
import json
import math
import random
import warnings
import pygame
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple

# ── CONFIG ────────────────────────────────────────────────────────
DATA_FILE       = "field_map.json"
GRAPH_FILE      = "knowledge_graph.txt"   # V5: glossary definitions
IDENTITY_FILE   = "identity_core.txt"     # V5: earned identity strengths
WIDTH, HEIGHT   = 1200, 800
FPS             = 30                      # 30fps is plenty for a brain visualiser
FOV             = 600
CAMERA_DIST     = 800
MAX_PHYSICS     = 60                      # Only run physics on the N most active nodes
RELOAD_EVERY    = 6                       # Reload field_map.json every N frames
GLOSSARY_EVERY  = 90                      # Reload knowledge graph / identity every N frames
PANEL_ALPHA     = 225
HOVER_RADIUS    = 18                      # px: node under the mouse
CLICK_RADIUS    = 26                      # px: click-to-select tolerance
CLICK_SLOP      = 6                       # px: below this a click is not a drag

COLOR_VOID      = (2,   2,   8)
COLOR_SEARCH    = (255, 220, 0)
COLOR_HUD       = (0,   180, 160)
COLOR_PANEL_BG  = (8,  10,  18)
COLOR_PANEL_EDGE = (0, 90,  80)
COLOR_HOVER     = (255, 255, 255)

CONTROLS = [
    "L-DRAG  rotate",
    "CLICK   inspect node",
    "R-DRAG  pan",
    "SCROLL  zoom",
    "R  reset",
    "F  fit all",
    "/  search",
    "T  top memories",
    "L  colour legend",
    "E  edges on/off",
    "SPACE pause spin",
    "TAB/1-0 switch view",
    "H  hide this help",
    "Q  quit",
]

# ── TAB CONFIG ─────────────────────────────────────────────────────
# Every live stream of hers, in one window.  Number keys 1-9/0 select
# the first ten; the rest are clickable or TAB-reachable.
# kind: "tail" (plain file tail), "chat", "alerts" or "progress" (computed).
@dataclass(frozen=True)
class TabSpec:
    name: str
    path: Optional[str]          # None = computed/view kind
    col: Tuple[int, int, int]    # RGB accent colour
    kind: str                    # "tail" | "chat" | "alerts" | "progress"

TABS: Tuple[TabSpec, ...] = (
    TabSpec("CONNECTOME", None,        (0, 200, 180), "graph"),
    TabSpec("MONOLOGUE",  "inner_monologue.txt", (0, 220, 170), "tail"),
    TabSpec("DECISIONS",  "basal_ganglia_log.txt", (255, 200, 80), "tail"),
    TabSpec("DISCOVERY",  "discoveries.txt",     (120, 200, 255), "tail"),
    TabSpec("GAPS",       "knowledge_gaps.txt",  (255, 140, 90), "tail"),
    TabSpec("EPISODES",   "episodic_memory.txt", (200, 160, 255), "tail"),
    TabSpec("EMOTION",    "emotional_core.txt",  (255, 120, 120), "tail"),
    TabSpec("REASONING",  "inferences.txt",      (150, 230, 150), "tail"),
    TabSpec("ACTIONS",    "action_log.txt",      (255, 220, 150), "tail"),
    TabSpec("IDENTITY",   "identity_core.txt",   (230, 210, 140), "tail"),
    TabSpec("PEOPLE",     "people.txt",          (140, 230, 220), "tail"),
    TabSpec("BELIEFS",    "beliefs.txt",         (230, 170, 220), "tail"),
    TabSpec("THREADS",    "threads.txt",         (170, 220, 170), "tail"),
    TabSpec("LESSONS",    "lessons.txt",         (220, 220, 150), "tail"),
    TabSpec("CHAT",       None,                  (120, 255, 200), "chat"),
    TabSpec("ALERTS",     None,                  (255, 90, 90),   "alerts"),
    TabSpec("PROGRESS",   None,                  (150, 180, 255), "progress"),
)
TAB_LINE_H = 16
TAB_READ_EVERY = 15      # frames between file re-reads (~0.5s at 30fps)
TAIL_BYTES = 96 * 1024   # only read the end of big logs

# ── COLOUR SPECTRUM ───────────────────────────────────────────────
def activation_color(act: float) -> Tuple[int, int, int]:
    """Map activation [0.0..1.0] to an RGB colour using fixed anchors."""
    act = max(0.0, min(1.0, act))
    anchors: List[Tuple[float, Tuple[int, int, int]]] = [
        (0.00, (200,   0,   0)),
        (0.25, (255, 140,   0)),
        (0.50, (160,   0, 255)),
        (0.75, (0,   100, 255)),
        (1.00, (0,   255, 230)),
    ]
    for i in range(len(anchors) - 1):
        t0, c0 = anchors[i]
        t1, c1 = anchors[i + 1]
        if t0 <= act <= t1:
            t = (act - t0) / (t1 - t0)
            return (
                int(c0[0] + (c1[0] - c0[0]) * t),
                int(c0[1] + (c1[1] - c0[1]) * t),
                int(c0[2] + (c1[2] - c0[2]) * t),
            )
    return anchors[-1][1]

# ── GLOSSARY / IDENTITY LOADERS (pure, testable) ──────────────────
def load_glossary(path: str = GRAPH_FILE) -> Dict[str, Dict[str, List[Tuple[str, str, float]]]]:
    """Parse knowledge_graph.txt into {word: {"out": [(rel, y, conf)], "in": [(rel, x, conf)]}}."""
    out: Dict[str, Dict[str, List[Tuple[str, str, float]]]] = {}
    try:
        if not os.path.exists(path):
            return out
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.startswith("EDGE: "):
                    continue
                parts = line[len("EDGE: "):].split(" | ")
                if len(parts) < 3:
                    continue
                x, rel, y = parts[0], parts[1], parts[2]
                conf = 0.0
                for p in parts[3:]:
                    if p.startswith("CONF: "):
                        try:
                            conf = float(p[len("CONF: "):])
                        except ValueError:
                            conf = 0.0
                out.setdefault(x, {"out": [], "in": []})["out"].append((rel, y, conf))
                out.setdefault(y, {"out": [], "in": []})["in"].append((rel, x, conf))
    except Exception:
        pass
    return out


def load_identity(path: str = IDENTITY_FILE) -> Dict[str, float]:
    """{word: strength} from identity_core.txt."""
    ident: Dict[str, float] = {}
    try:
        if not os.path.exists(path):
            return ident
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.startswith("CORE: "):
                    continue
                parts = line[len("CORE: "):].split()
                if len(parts) >= 2:
                    try:
                        ident[parts[0]] = float(parts[1])
                    except ValueError:
                        pass
    except Exception:
        pass
    return ident


def degree_map(edges: List[Dict[str, str]]) -> Dict[str, int]:
    """{node: degree} over the rendered edge list."""
    deg: Dict[str, int] = {}
    for e in edges:
        src, tgt = e.get("source"), e.get("target")
        if src:
            deg[src] = deg.get(src, 0) + 1
        if tgt:
            deg[tgt] = deg.get(tgt, 0) + 1
    return deg


def neighbours_of(edges: List[Dict[str, str]], node: str, limit: int = 5) -> List[Tuple[str, float]]:
    """Strongest neighbours of `node`: [(other, weight)]."""
    pairs: List[Tuple[str, float]] = []
    for e in edges:
        if e.get("source") == node:
            pairs.append((e.get("target", ""), e.get("weight", 0)))
        elif e.get("target") == node:
            pairs.append((e.get("source", ""), e.get("weight", 0)))
    pairs.sort(key=lambda p: p[1], reverse=True)
    return pairs[:limit]


def pick_node(projected: Dict[str, Tuple[float, float, float]], pos: Tuple[int, int], radius: int = CLICK_RADIUS) -> Optional[str]:
    """Nearest projected node to a screen point (None when out of range)."""
    best: Optional[str] = None
    best_d = radius * radius
    for nid, (sx, sy, _sc) in projected.items():
        d = (sx - pos[0]) ** 2 + (sy - pos[1]) ** 2
        if d <= best_d:
            best, best_d = nid, d
    return best

# ── PRE-BAKED GLOW CACHE ──────────────────────────────────────────
_glow_cache: Dict[Tuple[int, Tuple[int, int, int]], pygame.Surface] = {}
_GLOW_CACHE_MAX = 512


def get_glow(radius: int, color: Tuple[int, int, int]) -> pygame.Surface:
    """Return a cached glow surface. Creates it once, reuses forever."""
    key = (int(radius), tuple(int(c) // 16 * 16 for c in color))
    if key not in _glow_cache:
        size = int(radius) * 4
        if size < 4:
            size = 4
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        for r in range(int(radius), 0, -max(1, int(radius) // 4)):
            alpha = int(60 * (r / int(radius)) ** 0.5)
            pygame.draw.circle(surf, (*color, alpha), (size // 2, size // 2), r)
        _glow_cache[key] = surf
        while len(_glow_cache) > _GLOW_CACHE_MAX:
            _glow_cache.pop(next(iter(_glow_cache)))
    return _glow_cache[key]

# ── 3D MATH ───────────────────────────────────────────────────────
def rotate_y(x: float, y: float, z: float, c: float, s: float) -> Tuple[float, float, float]:
    return x * c + z * s, y, -x * s + z * c


def rotate_x(x: float, y: float, z: float, c: float, s: float) -> Tuple[float, float, float]:
    return x, y * c - z * s, y * s + z * c


def project(x: float, y: float, z: float, W: int, H: int, zoom: float, pan_x: float, pan_y: float) -> Optional[Tuple[int, int, float]]:
    z_cam = z + CAMERA_DIST / zoom
    if z_cam <= 10:
        return None, None, 0
    scale = (FOV / zoom) / z_cam
    return int(x * scale + W / 2 + pan_x), int(-y * scale + H / 2 + pan_y), scale


# ── VISUALISER ────────────────────────────────────────────────────
class SynapseVisualizer:
    def __init__(self):
        self.pos: Dict[str, List[float]] = {}      # nid -> [x, y, z]
        self.vel: Dict[str, List[float]] = {}      # nid -> [vx, vy, vz]

        self.yaw: float = 0.0
        self.pitch: float = 0.0
        self.zoom: float = 1.0
        self.pan_x: float = 0.0
        self.pan_y: float = 0.0

        self.rotating: bool = False
        self.panning: bool = False
        self.mouse_prev: Tuple[int, int] = (0, 0)
        self.auto_spin: bool = True

        self.search_mode: bool = False
        self.search_text: str = ""
        self.search_result: Optional[str] = None

        self.frame: int = 0
        self.cached_data: Dict[str, Dict] = {"nodes": {}, "edges": []}
        self.projected: Dict[str, Tuple[float, float, float]] = {}   # nid -> (sx, sy, sc)

        # V5 enhancements
        self.selected: Optional[str] = None          # inspected node
        self.hovered: Optional[str] = None
        self.mouse_pos: Tuple[int, int] = (-100, -100)
        self.drag_start: Optional[Tuple[int, int]] = None
        self.show_help: bool = True
        self.show_top: bool = True
        self.show_legend: bool = True
        self.show_edges: bool = True
        self._top_rects: List[Tuple[pygame.Rect, str]] = []
        self.glossary: Dict = {}
        self.identity: Dict = {}
        self._degrees: Dict = {}

        # Monitor tabs
        self.tab: int = 0
        self.tab_scroll: Dict[int, int] = {}     # tab index -> lines scrolled up
        self._tail_cache: Dict[str, List[str]] = {}   # path -> list of lines
        self._tab_rects: List[pygame.Rect] = []
        self._tail_frame: int = 0

    def get_pos(self, nid: str) -> List[float]:
        if nid not in self.pos:
            self.pos[nid] = [
                random.uniform(-250, 250),
                random.uniform(-250, 250),
                random.uniform(-250, 250),
            ]
            self.vel[nid] = [0.0, 0.0, 0.0]
        return self.pos[nid]

    def fit_all(self):
        if not self.pos:
            return
        xs = [v[0] for v in self.pos.values()]
        ys = [v[1] for v in self.pos.values()]
        zs = [v[2] for v in self.pos.values()]
        span = max(
            max(xs) - min(xs),
            max(ys) - min(ys),
            max(zs) - min(zs), 1
        )
        self.yaw = 0.3
        self.pitch = -0.2
        self.zoom = 350 / span
        self.pan_x = 0.0
        self.pan_y = 0.0

    def world_to_screen(self, wx: float, wy: float, wz: float, W: int, H: int) -> Optional[Tuple[int, int, float]]:
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        cx, sx = math.cos(self.pitch), math.sin(self.pitch)
        x, y, z = rotate_y(wx, wy, wz, cy, sy)
        x, y, z = rotate_x(x, y, z, cx, sx)
        return project(x, y, z, W, H, self.zoom, self.pan_x, self.pan_y)

    # ── PANELS ────────────────────────────────────────────────────
    def panel(self, x: int, y: int, w: int, h: int, title: Optional[str] = None):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((*COLOR_PANEL_BG, PANEL_ALPHA))
        screen.blit(surf, (x, y))
        pygame.draw.rect(screen, COLOR_PANEL_EDGE, (x, y, w, h), 1)
        if title:
            screen.blit(font_panel_bold.render(title, True, COLOR_HUD),
                        (x + 10, y + 8))

    # ── MONITOR TABS ──────────────────────────────────────────────
    def _read_tail(self, path: Optional[str], n: int = 400) -> List[str]:
        """Last `n` lines of a file, reading only the file's tail."""
        if not path or not os.path.exists(path):
            return []
        try:
            size = os.path.getsize(path)
            with open(path, "rb") as f:
                if size > TAIL_BYTES:
                    f.seek(size - TAIL_BYTES)
                    f.readline()   # drop the partial first line
                data = f.read().decode("utf-8", errors="replace")
            return data.splitlines()[-n:]
        except Exception:
            return []

    def _refresh_tails(self):
        for t in TABS:
            if t.kind == "tail" and t.path:
                self._tail_cache[t.path] = self._read_tail(t.path)

    def select_tab(self, index: int):
        self.tab = index % len(TABS)

    def next_tab(self):
        self.select_tab(self.tab + 1)

    def draw_tab_bar(self, W: int):
        x = 0
        self._tab_rects = []
        for i, t in enumerate(TABS):
            if i < 9:
                key = str(i + 1)
            elif i == 9:
                key = "0"
            else:
                key = ">>"
            label = f"{key} {t.name}"
            txt = font_tab.render(label, True,
                                  (10, 14, 18) if i == self.tab else t.col)
            tw = txt.get_width() + 18
            rect = pygame.Rect(x, 0, tw, 26)
            self._tab_rects.append(rect)
            if i == self.tab:
                pygame.draw.rect(screen, t.col, rect)
            else:
                pygame.draw.rect(screen, (14, 18, 26), rect)
                pygame.draw.rect(screen, (40, 55, 65), rect, 1)
            screen.blit(txt, (x + 9, 6))
            x += tw + 2
        pygame.draw.line(screen, (40, 55, 65), (0, 26), (W, 26), 1)

    def _draw_lines(self, lines: List[str], col: Tuple[int, int, int],
                    header: Optional[str], W: int, H: int, top: int = 34):
        """Shared scrolling text renderer."""
        if header:
            screen.blit(font_small.render(header, True, (110, 130, 140)),
                        (12, top))
            top += 20
        body_top = top
        visible = max(1, (H - body_top - 12) // TAB_LINE_H)
        offset = self.tab_scroll.get(self.tab, 0)
        start = max(0, len(lines) - visible - offset)
        for i, line in enumerate(lines[start:start + visible]):
            text = line.rstrip()
            max_chars = (W - 24) // 8
            if len(text) > max_chars:
                text = text[:max_chars - 1] + "…"
            shade = 1.0 if i >= visible - 3 else 0.82
            c = tuple(int(v * shade) for v in col)
            screen.blit(font_small.render(text, True, c),
                        (12, body_top + i * TAB_LINE_H))
        if not lines:
            screen.blit(font_small.render("(nothing here yet)",
                                          True, (90, 100, 110)),
                        (12, body_top))

    def draw_text_tab(self, W: int, H: int):
        """A scrolling tail of one live stream — or a computed view."""
        t = TABS[self.tab]
        if t.kind == "chat":
            lines = self._chat_lines()
            self._draw_lines(lines, t.col, "CHAT — recent exchanges "
                             "(winner in brackets)", W, H)
            return
        if t.kind == "alerts":
            lines = self._alert_lines()
            self._draw_lines(lines, t.col, "ALERTS — things needing you "
                             "(Y confirm / N cancel)", W, H)
            return
        if t.kind == "progress":
            lines = self._progress_lines()
            self._draw_lines(lines, t.col, "PROGRESS — growth and health",
                             W, H)
            return
        lines = self._tail_cache.get(t.path, [])
        if not t.path:
            return
        header = (f"{t.path}   —   {len(lines)} lines   "
                  f"(wheel scrolls, {self.tab_scroll.get(self.tab, 0)} up)")
        screen.blit(font_small.render(header, True, (110, 130, 140)),
                    (12, 34))
        self._draw_lines(lines, t.col, None, W, H, top=54)

    def _chat_lines(self) -> List[str]:
        """Return recent chat exchange lines (placeholder — integrate with actual chat bus)."""
        return []

    def _alert_lines(self) -> List[str]:
        """Return alert lines from basal ganglia log."""
        path = next((t.path for t in TABS if t.kind == "alerts"), None)
        return self._read_tail(path) if path else []

    def _progress_lines(self) -> List[str]:
        """Compute progress summary lines from field state."""
        # Placeholder — integrate with actual field metrics
        return ["Progress monitoring not yet connected to live metrics."]

    def draw_hud(self, nc: int, ec: int, top_node: Optional[str], top_act: float, W: int, H: int):
        if self.show_help:
            for i, line in enumerate(CONTROLS):
                screen.blit(font_hud.render(line, True, (55, 75, 95)),
                            (12, 12 + i * 18))
        stats = [
            f"NODES : {nc}",
            f"EDGES : {ec}",
            f"ZOOM  : {self.zoom:.2f}x",
            f"TOP   : {top_node.upper() if top_node else '---'} ({top_act:.3f})",
        ]
        for i, line in enumerate(stats):
            screen.blit(font_hud.render(line, True, COLOR_HUD),
                        (12, H - 20 - (len(stats) - i) * 18))
        if self.search_mode:
            s = font_search.render(f"SEARCH: {self.search_text}_", True, COLOR_SEARCH)
            screen.blit(s, (W // 2 - s.get_width() // 2, H - 36))
        elif self.search_result:
            s = font_search.render(
                f"→ {self.search_result.upper()}  (ESC to clear)", True, COLOR_SEARCH)
            screen.blit(s, (W // 2 - s.get_width() // 2, H - 36))

    def draw_legend(self, W: int, H: int):
        x, y, w, h = 12, H - 110, 200, 66
        self.panel(x, y, w, h, "ACTIVATION")
        bar_x, bar_y, bar_w, bar_h = x + 12, y + 30, w - 24, 10
        for i in range(bar_w):
            col = activation_color(i / bar_w)
            pygame.draw.line(screen, col, (bar_x + i, bar_y),
                             (bar_x + i, bar_y + bar_h))
        pygame.draw.rect(screen, (60, 60, 70),
                         (bar_x, bar_y, bar_w, bar_h), 1)
        screen.blit(font_small.render("0.0", True, (120, 120, 130)),
                    (bar_x, bar_y + 13))
        screen.blit(font_small.render("0.5", True, (120, 120, 130)),
                    (bar_x + bar_w // 2 - 8, bar_y + 13))
        screen.blit(font_small.render("1.0", True, (120, 120, 130)),
                    (bar_x + bar_w - 16, bar_y + 13))

    def draw_top_list(self, nodes: Dict[str, Dict], W: int, H: int):
        rows = 10
        x, w = W - 262, 250
        y, h = 12, 30 + rows * 17
        self.panel(x, y, w, h, "TOP MEMORIES")
        ranked = sorted(nodes.items(),
                        key=lambda kv: kv[1].get("activation", 0),
                        reverse=True)[:rows]
        self._top_rects = []
        for i, (nid, info) in enumerate(ranked):
            act = info.get("activation", 0)
            ry = y + 30 + i * 17
            rect = pygame.Rect(x + 6, ry, w - 12, 16)
            self._top_rects.append((rect, nid))
            if self.selected == nid:
                pygame.draw.rect(screen, (30, 60, 70), rect)
            col = activation_color(act)
            pygame.draw.circle(screen, col, (x + 16, ry + 8), 4)
            name = nid.upper()
            if len(name) > 22:
                name = name[:21] + "…"
            screen.blit(font_small.render(name, True, (200, 210, 215)),
                        (x + 26, ry + 1))
            screen.blit(font_small.render(f"{act:.3f}", True, col),
                        (x + w - 48, ry + 1))

    def draw_inspector(self, nodes: Dict, edges: List, W: int, H: int):
        """The glossary panel: what the selected memory IS."""
        if not self.selected or self.selected not in nodes:
            return
        nid = self.selected
        info = nodes.get(nid, {})
        act = info.get("activation", 0)
        phase = info.get("phase", "?")
        w, h = 350, 250
        x, y = W - w - 12, H - h - 12
        self.panel(x, y, w, h, "MEMORY INSPECTOR")
        tx = x + 12
        screen.blit(font_panel_bold.render(nid.upper()[:26], True, (240, 240, 245)),
                    (tx, y + 30))
        screen.blit(font_small.render(
            f"activation {act:.3f}   phase {phase}   "
            f"links {self._degrees.get(nid, 0)}", True, activation_color(act)),
                    (tx, y + 50))

        # Glossary: her own typed knowledge about this memory (V5 R2/R3)
        entry = self.glossary.get(nid)
        gy = y + 72
        if entry:
            for rel, other, conf in entry["out"][:3]:
                screen.blit(font_small.render(
                    f"  {rel} → {other}  ({conf:.2f})", True, (150, 220, 200)),
                    (tx, gy))
                gy += 15
            for rel, other, conf in entry["in"][:2]:
                screen.blit(font_small.render(
                    f"  {other} → {rel}  ({conf:.2f})", True, (140, 190, 220)),
                    (tx, gy))
                gy += 15
        else:
            screen.blit(font_small.render("  no typed knowledge yet — a gap",
                                          True, (150, 120, 120)), (tx, gy))
            gy += 15

        ident = self.identity.get(nid)
        if ident is not None:
            screen.blit(font_small.render(
                f"  identity strength {ident:.3f}", True, (220, 200, 140)),
                (tx, gy))
            gy += 15

        # Strongest associations from the live field
        screen.blit(font_small.render("strongest links:", True, (120, 140, 150)),
                    (tx, gy))
        gy += 16
        for other, weight in neighbours_of(edges, nid, 3):
            screen.blit(font_small.render(
                f"  {other}  w={weight:.2f}", True, (170, 170, 180)),
                (tx, gy))
            gy += 15

    # ── FRAME ─────────────────────────────────────────────────────
    def run(self, max_frames: Optional[int] = None):
        _ensure_display()
        frames = 0
        while True:
            W, H = screen.get_size()
            screen.fill(COLOR_VOID)

            # ── Events ───────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN:
                    if self.search_mode:
                        if event.key == pygame.K_RETURN:
                            self.search_mode = False
                            self.search_result = self.search_text.lower().strip() or None
                            if self.search_result:
                                self.selected = self.search_result
                        elif event.key == pygame.K_ESCAPE:
                            self.search_mode = False
                            self.search_text = ""
                            self.search_result = None
                        elif event.key == pygame.K_BACKSPACE:
                            self.search_text = self.search_text[:-1]
                        else:
                            self.search_text += event.unicode
                    else:
                        # Tab switching works from every view.
                        if event.key == pygame.K_TAB:
                            self.next_tab()
                        elif pygame.K_1 <= event.key <= pygame.K_9:
                            self.select_tab(event.key - pygame.K_1)
                        elif event.key == pygame.K_0:
                            self.select_tab(9)
                        elif event.key == pygame.K_q:
                            return
                        elif self.tab == 0:
                            if event.key == pygame.K_r:
                                self.yaw = self.pitch = self.pan_x = self.pan_y = 0.0
                                self.zoom = 1.0
                            elif event.key == pygame.K_f:
                                self.fit_all()
                            elif event.key == pygame.K_h:
                                self.show_help = not self.show_help
                            elif event.key == pygame.K_t:
                                self.show_top = not self.show_top
                            elif event.key == pygame.K_l:
                                self.show_legend = not self.show_legend
                            elif event.key == pygame.K_e:
                                self.show_edges = not self.show_edges
                            elif event.key == pygame.K_SPACE:
                                self.auto_spin = not self.auto_spin
                            elif event.key == pygame.K_SLASH:
                                self.search_mode = True
                                self.search_text = ""
                                self.auto_spin = False
                            elif event.key == pygame.K_ESCAPE:
                                self.search_result = None
                                self.selected = None

                elif event.type == pygame.MOUSEWHEEL:
                    if self.tab == 0:
                        self.zoom = max(0.05, min(10.0,
                                   self.zoom * (1.12 if event.y > 0 else 0.89)))
                    else:
                        off = self.tab_scroll.get(self.tab, 0) + event.y * 3
                        self.tab_scroll[self.tab] = max(0, off)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and event.pos[1] <= 26:
                        for i, rect in enumerate(self._tab_rects):
                            if rect.collidepoint(event.pos):
                                self.select_tab(i)
                                break
                    elif self.tab == 0:
                        if event.button == 1:
                            self.rotating = True
                            self.auto_spin = False
                            self.mouse_prev = event.pos
                            self.drag_start = event.pos
                        elif event.button == 3:
                            self.panning = True
                            self.mouse_prev = event.pos

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.rotating = False
                        # A click (no drag) selects a node or a top-list row
                        if self.tab == 0 and self.drag_start and \
                                abs(event.pos[0] - self.drag_start[0]) < CLICK_SLOP and \
                                abs(event.pos[1] - self.drag_start[1]) < CLICK_SLOP:
                            picked = None
                            for rect, nid in self._top_rects:
                                if rect.collidepoint(event.pos):
                                    picked = nid
                                    break
                            if picked is None:
                                picked = pick_node(self.projected, event.pos)
                            self.selected = picked
                        self.drag_start = None
                    elif event.button == 3:
                        self.panning = False

                elif event.type == pygame.MOUSEMOTION:
                    self.mouse_pos = event.pos
                    dx = event.pos[0] - self.mouse_prev[0]
                    dy = event.pos[1] - self.mouse_prev[1]
                    self.mouse_prev = event.pos
                    if self.rotating:
                        self.yaw += 0.005 * dx
                        self.pitch = max(-1.5, min(1.5, self.pitch + 0.005 * dy))
                    elif self.panning:
                        self.pan_x += dx
                        self.pan_y += dy

            if self.auto_spin:
                self.yaw += 0.003

            # ── Reload data every N frames (not every frame) ──────
            if self.frame % RELOAD_EVERY == 0:
                try:
                    if os.path.exists(DATA_FILE):
                        with open(DATA_FILE, "r") as f:
                            self.cached_data = json.load(f)
                except Exception:
                    pass
            if self.frame % GLOSSARY_EVERY == 0:
                self.glossary = load_glossary()
                self.identity = load_identity()
            self.frame += 1

            # ── Text monitor tabs (no 3D work needed) ─────────────
            if self.tab != 0:
                if self._tail_frame % TAB_READ_EVERY == 0:
                    self._refresh_tails()
                self._tail_frame += 1
                self.draw_text_tab(W, H)
                self.draw_tab_bar(W)
                pygame.display.flip()
                clock.tick(FPS)
                frames += 1
                if max_frames is not None and frames >= max_frames:
                    return
                continue

            nodes = self.cached_data.get("nodes", {})
            edges = self.cached_data.get("edges", [])
            ids = list(nodes.keys())
            if self.frame % GLOSSARY_EVERY == 1:
                self._degrees = degree_map(edges)

            # ── Physics — only on the most active nodes ────────────
            active_ids = sorted(
                ids,
                key=lambda n: nodes.get(n, {}).get("activation", 0),
                reverse=True
            )[:MAX_PHYSICS]

            for id_a in active_ids:
                p1 = self.get_pos(id_a)
                for axis in range(3):
                    self.vel[id_a][axis] += -p1[axis] * 0.003
                for id_b in active_ids:
                    if id_a == id_b:
                        continue
                    p2 = self.get_pos(id_b)
                    dx = p1[0] - p2[0]; dy = p1[1] - p2[1]; dz = p1[2] - p2[2]
                    dist = math.sqrt(dx * dx + dy * dy + dz * dz) or 1
                    if dist < 180:
                        f = 0.5 / dist
                        self.vel[id_a][0] += dx * f
                        self.vel[id_a][1] += dy * f
                        self.vel[id_a][2] += dz * f

            physics_set = set(active_ids)
            for edge in edges:
                src, tgt = edge.get("source"), edge.get("target")
                if src in physics_set and tgt in physics_set:
                    if src in self.pos and tgt in self.pos:
                        p1 = self.pos[src]; p2 = self.pos[tgt]
                        w = edge.get("weight", 0.1) * 0.002
                        for axis in range(3):
                            d = (p2[axis] - p1[axis]) * w
                            self.vel[src][axis] += d
                            self.vel[tgt][axis] -= d

            for nid in active_ids:
                for axis in range(3):
                    self.pos[nid][axis] += self.vel[nid][axis]
                    self.vel[nid][axis] *= 0.85

            for nid in ids:
                self.get_pos(nid)

            # ── Project all nodes ─────────────────────────────────
            projected = {}
            for nid in ids:
                sx, sy, sc = self.world_to_screen(*self.pos[nid], W, H)
                if sx is not None:
                    projected[nid] = (sx, sy, sc)
            self.projected = projected

            self.hovered = pick_node(projected, self.mouse_pos, HOVER_RADIUS)

            draw_order = sorted(projected.items(), key=lambda x: x[1][2])

            # ── Top node ──────────────────────────────────────────
            top_node, top_act = None, 0.0
            for nid, info in nodes.items():
                a = info.get("activation", 0)
                if a > top_act:
                    top_act, top_node = a, nid

            # ── Draw edges ────────────────────────────────────────
            if self.show_edges:
                for edge in edges:
                    src, tgt = edge.get("source"), edge.get("target")
                    if src in projected and tgt in projected:
                        sx1, sy1, sc1 = projected[src]
                        sx2, sy2, sc2 = projected[tgt]
                        w = edge.get("weight", 0)
                        a_s = nodes.get(src, {}).get("activation", 0)
                        a_t = nodes.get(tgt, {}).get("activation", 0)
                        fade = max(0.08, min(1.0, (sc1 + sc2) * 0.4))
                        if w > 0.4:
                            ec = activation_color((a_s + a_t) / 2)
                            ec = tuple(int(c * fade * 0.35) for c in ec)
                            pygame.draw.line(screen, ec, (sx1, sy1), (sx2, sy2),
                                             max(1, int(w * 2)))
                        else:
                            g = int(25 * fade)
                            pygame.draw.line(screen, (g, g, g + 8),
                                             (sx1, sy1), (sx2, sy2), 1)

            # ── Draw nodes ────────────────────────────────────────
            for nid, (sx, sy, scale) in draw_order:
                info = nodes.get(nid, {})
                act = info.get("activation", 0)
                col = activation_color(act)
                fade = max(0.15, min(1.0, scale * 1.8))
                is_result = (self.search_result and
                             nid.lower() == self.search_result.lower())
                is_sel = (self.selected == nid)
                is_hover = (self.hovered == nid)

                if is_result or is_sel:
                    pygame.draw.circle(screen, COLOR_SEARCH, (sx, sy), 18, 2)
                if is_hover and not (is_result or is_sel):
                    pygame.draw.circle(screen, COLOR_HOVER, (sx, sy), 12, 1)

                if act > 0.05:
                    gr = max(4, min(40, int((5 + act * 14) * scale * 0.7)))
                    fc = tuple(int(c * fade) for c in col)
                    gsurf = get_glow(gr, fc)
                    screen.blit(gsurf,
                                (sx - gsurf.get_width() // 2,
                                 sy - gsurf.get_height() // 2),
                                special_flags=pygame.BLEND_RGBA_ADD)
                    dot_r = max(2, int((3 + act * 4) * scale * 0.5))
                    pygame.draw.circle(screen, (255, 255, 255), (sx, sy), dot_r)
                    if scale > 0.85 or is_result or is_sel or is_hover:
                        lc = COLOR_SEARCH if (is_result or is_sel) else col
                        txt = font_active.render(nid.upper(), True, lc)
                        screen.blit(txt, (sx + dot_r + 4, sy - 8))
                else:
                    fc = tuple(int(c * fade * 0.5) for c in col)
                    dot_r = max(1, int(2 * scale * 0.5))
                    pygame.draw.circle(screen, fc, (sx, sy), dot_r)
                    if scale > 1.3 or is_result or is_sel or is_hover:
                        lc = COLOR_SEARCH if (is_result or is_sel) else (70, 25, 25)
                        txt = font_locked.render(nid.lower(), True, lc)
                        screen.blit(txt, (sx + dot_r + 3, sy - 5))

            # ── Panels ────────────────────────────────────────────
            self.draw_hud(len(nodes), len(edges), top_node, top_act, W, H)
            if self.show_legend:
                self.draw_legend(W, H)
            if self.show_top:
                self.draw_top_list(nodes, W, H)
            self.draw_inspector(nodes, edges, W, H)

            self.draw_tab_bar(W)
            pygame.display.flip()

            frames += 1
            if max_frames is not None and frames >= max_frames:
                return




# ── BOOT (lazy — importing this module must never open a display) ────
# The old code ran pygame.init() + set_mode() at import, so every
# importer got a window.  Display objects are created on first run()
# instead; headless self-tests init the dummy driver with no window.
screen: Optional[pygame.Surface] = None
clock: Optional[pygame.time.Clock] = None
font_active: Optional[pygame.font.Font] = None
font_locked: Optional[pygame.font.Font] = None
font_hud: Optional[pygame.font.Font] = None
font_small: Optional[pygame.font.Font] = None
font_panel_bold: Optional[pygame.font.Font] = None
font_search: Optional[pygame.font.Font] = None
font_tab: Optional[pygame.font.Font] = None


def _ensure_display():
    """Create the display + fonts once, on first run()."""
    global screen, clock
    global font_active, font_locked, font_hud, font_small
    global font_panel_bold, font_search, font_tab
    if screen is not None:
        return
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("AURA: LIVE NEURAL CONNECTOME  [3D]")
    clock = pygame.time.Clock()
    font_active = pygame.font.SysFont("Verdana", 14, bold=True)
    font_locked = pygame.font.SysFont("Verdana", 10)
    font_hud = pygame.font.SysFont("Consolas", 12)
    font_search = pygame.font.SysFont("Consolas", 16, bold=True)
    font_panel_bold = pygame.font.SysFont("Consolas", 13, bold=True)
    font_small = pygame.font.SysFont("Consolas", 11)
    font_tab = pygame.font.SysFont("Consolas", 12, bold=True)


# ── M16 ROUTE EVIDENCE (explicit receipts, observer-only) ────────
ROUTE_SYSTEMS: Tuple[Tuple[str, str], ...] = (
    ("m1", "M1 relevance"),
    ("m2", "M2 thread suppression"),
    ("m3", "M3 reasoning priority"),
    ("m4", "M4 context / current person"),
    ("m13", "M13 contradiction gating"),
    ("m14", "M14 episodic influence"),
    ("old_brain_field", "Old-brain field restore"),
    ("hearing_bridge", "Pass 1 hearing writeback"),
    ("people", "People branch"),
    ("belief", "Belief branch"),
    ("agenda", "Agenda branch"),
    ("teach", "Teach branch"),
    ("basal", "Selected basal winner"),
    ("stance", "Pass-2 cognitive stance"),
    ("mouth", "Mouth phrasing"),
)
_ROUTE_LABEL = dict(ROUTE_SYSTEMS)

# Influence is only representable when the receipt names a basis that
# proves it for that system.  Everything else is capped at OUTPUT USED.
_PROVEN_BASES: Dict[str, frozenset] = {
    "m3": frozenset({"selected-reasoning-candidate",
                     "explicit-memory-exemption"}),
    "m4": frozenset({"m4-context-selected", "m4-current-person-guard"}),
    "m13": frozenset({"guard-selected-conflict"}),
    "m14": frozenset({"episode-admission-selected", "g7-duplicate-guard"}),
    "old_brain_field": frozenset({"field-selected-after-restore"}),
    "basal": frozenset({"selected-winner"}),
}


def _route_receipt(raw: Dict) -> Dict:
    """Normalise one raw receipt, enforcing the evidence hierarchy."""
    system = str(raw.get("system") or "unknown")
    basis = str(raw.get("influence_basis") or "not-proven")
    influenced = (bool(raw.get("influenced_decision"))
                  and basis in _PROVEN_BASES.get(system, frozenset()))
    used = bool(raw.get("output_used")) or influenced
    produced = bool(raw.get("output_produced")) or used
    ran = bool(raw.get("ran")) or produced
    level = ("INFLUENCED DECISION" if influenced else
             "OUTPUT USED" if used else
             "OUTPUT PRODUCED" if produced else
             "RAN" if ran else "DORMANT")
    return {
        "system": system,
        "label": str(raw.get("label") or _ROUTE_LABEL.get(system, system)),
        "evidence_level": level,
        "ran": ran,
        "output_produced": produced,
        "output_used": used,
        "influenced_decision": influenced,
        "influence_basis": basis,
        "source_stage": str(raw.get("source_stage") or system),
        "destination_stage": str(raw.get("destination_stage") or "basal"),
        "details": dict(raw.get("details") or {}),
    }


def evidence_receipts(events: List[Dict]) -> Dict[str, Dict]:
    """Latest explicit receipt per system for one turn's events."""
    receipts: Dict[str, Dict] = {}
    for event in events or []:
        if event.get("event_type") != "system_evidence":
            continue
        raw = event.get("advanced_raw") or {}
        if not isinstance(raw, dict):
            continue
        if not raw.get("system") and event.get("subsystem"):
            raw = dict(raw, system=event["subsystem"])
        if not raw.get("system"):
            continue
        receipt = _route_receipt(raw)
        receipts[receipt["system"]] = receipt
    return receipts


def export_real_turns(events: List[Dict]) -> List[Tuple[str, str, List[Dict]]]:
    """Group events into (user, turn, events); same turn id stays isolated."""
    grouped: Dict[Tuple[str, str], List[Dict]] = {}
    for event in events or []:
        turn_id = str(event.get("turn_id") or "")
        if not turn_id:
            continue
        uid = str(event.get("_user_id") or event.get("user_id") or "unknown")
        grouped.setdefault((uid, turn_id), []).append(event)
    return [(uid, tid, evs) for (uid, tid), evs in grouped.items()]


def format_evidence_table(events: List[Dict]) -> List[str]:
    """Render one turn's receipts as aligned, explicit lines."""
    receipts = evidence_receipts(events)
    lines = ["system                      level                basis"]
    for system, label in ROUTE_SYSTEMS:
        receipt = receipts.get(system)
        if not receipt:
            continue
        lines.append(f"{label:<27} {receipt['evidence_level']:<20} "
                     f"{receipt['influence_basis']}")
    return lines


def _active_root() -> str:
    try:
        from aura_state import active_root as _ar
        return str(_ar())
    except Exception:
        return os.getcwd()


def _trace_files(root: Optional[str] = None) -> List[str]:
    root = root or _active_root()
    found: List[str] = []
    for base, _dirs, names in os.walk(root):
        if os.path.basename(base) != "observer_trace":
            continue
        for name in names:
            if name.endswith(".jsonl"):
                found.append(os.path.join(base, name))
    return sorted(found)


def build_diagnostics_text(root: Optional[str] = None) -> str:
    """Explicit M16 route evidence for every recorded turn."""
    lines = ["=== M16 ROUTE EVIDENCE ==="]
    files = _trace_files(root)
    if not files:
        lines.append("(no observer traces yet — all routes DORMANT)")
        for _system, label in ROUTE_SYSTEMS:
            lines.append(f"{label:<27} DORMANT")
        return "\n".join(lines)
    for path in files:
        events = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except ValueError:
                            continue
        except OSError:
            continue
        if not events:
            continue
        for uid, tid, turn_events in export_real_turns(events):
            lines.append("")
            lines.append(f"user={uid} turn={tid}")
            lines.extend("  " + line for line in format_evidence_table(turn_events))
    return "\n".join(lines)


def export_diagnostics(path: str = "diagnostics.txt") -> str:
    """Write the route-evidence export; returns the path written."""
    text = build_diagnostics_text()
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return path


if __name__ == "__main__":
    viz = SynapseVisualizer()
    if "--selftest" in sys.argv:
        viz.run(max_frames=40)
        rendered_tabs = 0
        for i in range(len(TABS)):
            viz.select_tab(i)
            viz.run(max_frames=2)
            rendered_tabs += 1
        print("SELFTEST OK: rendered 40 connectome frames + "
              f"{rendered_tabs} monitor tabs "
              f"({len(viz.cached_data.get('nodes', {}))} nodes, "
              f"{len(viz.glossary)} glossary terms)")
    else:
        viz.run()