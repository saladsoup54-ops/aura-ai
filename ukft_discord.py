# ukft_discord.py — First channel: Discord (G4)
# ==========================================================
# Stdlib-only adapter (stack law: no new dependencies).
# Raw Gateway over a minimal RFC6455 client + REST via
# requests. One Discord user = one brain partition
# ("discord:<id>"); the brain API does everything else.
#
# Safety: DMs + mentions + allowlisted channels only, never
# other bots, per-user cooldown, operator kill-switch.
# Token: env DISCORD_TOKEN, else discord_config.json (never
# committed, never logged, never echoed). No token? Clean exit.
#
# Run:  python ukft_discord.py   (needs token + intents incl.
#       MESSAGE_CONTENT enabled in the developer portal)
# ==========================================================

import base64
import hashlib
import json
import os
import random
import select
import socket
import ssl
import struct
import threading
import time

GATEWAY_URL = "gateway.discord.gg"
GATEWAY_PATH = "/?v=10&encoding=json"
REST_BASE = "https://discord.com/api/v10"
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# GUILDS | GUILD_MESSAGES | DIRECT_MESSAGES | MESSAGE_CONTENT
INTENTS = 1 | 512 | 4096 | 32768

OP_DISPATCH = 0
OP_HEARTBEAT = 1
OP_IDENTIFY = 2
OP_RESUME = 6
OP_RECONNECT = 7
OP_INVALID_SESSION = 9
OP_HELLO = 10
OP_HEARTBEAT_ACK = 11

CONFIG_FILE = "discord_config.json"
EXAMPLE_FILE = "discord_config.EXAMPLE.json"

DEFAULT_CONFIG = {
    "token": "",
    "operators": [],
    "channels": [],
    "default_pack": "flirty",
    "cooldown_s": 8,
    "respond_mentions": True,
    "respond_dm": True,
}


# ─── Minimal RFC6455 client ──────────────────────────────────

def _accept_key(key):
    return base64.b64encode(hashlib.sha1(
        (key + WS_GUID).encode()).digest()).decode()


def encode_frame(text):
    """Client text frame (always masked, RFC6455 §5.3)."""
    data = text.encode("utf-8")
    mask = bytes(random.getrandbits(8) for _ in range(4))
    if len(data) < 126:
        header = bytes([0x81, 0x80 | len(data)]) + mask
    elif len(data) < (1 << 16):
        header = bytes([0x81, 0xFE]) + struct.pack("!H", len(data)) + mask
    else:
        header = bytes([0x81, 0xFF]) + struct.pack("!Q", len(data)) + mask
    return header + bytes(b ^ mask[i % 4] for i, b in enumerate(data))


def encode_close():
    return bytes([0x88, 0x80, 0x00, 0x00, 0x00, 0x00])


class FrameReader:
    """Incremental server-frame parser (server frames unmasked)."""

    def __init__(self):
        self.buf = bytearray()

    def feed(self, data):
        self.buf += data

    def messages(self):
        """Yield ("text", str) / ("ping", b"") / ("close", None)."""
        out = []
        while True:
            if len(self.buf) < 2:
                return out
            b0, b1 = self.buf[0], self.buf[1]
            opcode = b0 & 0x0F
            length = b1 & 0x7F
            idx = 2
            if length == 126:
                if len(self.buf) < 4:
                    return out
                length = struct.unpack("!H", self.buf[2:4])[0]
                idx = 4
            elif length == 127:
                if len(self.buf) < 10:
                    return out
                length = struct.unpack("!Q", self.buf[2:10])[0]
                idx = 10
            mask = None
            if b1 & 0x80:
                if len(self.buf) < idx + 4:
                    return out
                mask = bytes(self.buf[idx:idx + 4])
                idx += 4
            if len(self.buf) < idx + length:
                return out
            payload = bytes(self.buf[idx:idx + length])
            if mask is not None:
                payload = bytes(b ^ mask[i % 4]
                                for i, b in enumerate(payload))
            del self.buf[:idx + length]
            if opcode == 0x1:
                out.append(("text", payload.decode("utf-8", "replace")))
            elif opcode == 0x9:
                out.append(("ping", payload))
            elif opcode == 0x8:
                out.append(("close", None))
            elif opcode == 0xA:
                continue


def gateway_connect():
    """Blocking TLS socket, WebSocket handshake done. Raises."""
    raw = socket.create_connection((GATEWAY_URL, 443), timeout=20)
    sock = ssl.create_default_context().wrap_socket(
        raw, server_hostname=GATEWAY_URL)
    key = base64.b64encode(os.urandom(16)).decode()
    req = (f"GET {GATEWAY_PATH} HTTP/1.1\r\nHost: {GATEWAY_URL}\r\n"
           f"Upgrade: websocket\r\nConnection: Upgrade\r\n"
           f"Sec-WebSocket-Key: {key}\r\n"
           f"Sec-WebSocket-Version: 13\r\n\r\n")
    sock.sendall(req.encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("handshake: connection closed")
        resp += chunk
    head = resp.split(b"\r\n\r\n", 1)[0].decode("latin-1")
    if " 101 " not in head.splitlines()[0]:
        raise ConnectionError("handshake refused: "
                              + head.splitlines()[0][:80])
    if _accept_key(key) not in head:
        raise ConnectionError("handshake: bad accept key")
    return sock


# ─── REST ────────────────────────────────────────────────────

class DiscordREST:
    def __init__(self, token, request_fn=None):
        self.token = token
        self._request_fn = request_fn

    def _headers(self):
        return {"Authorization": "Bot " + self.token,
                "Content-Type": "application/json",
                "User-Agent": "AURA_GF (ukft_discord, 1.0)"}

    def _post(self, path, payload, timeout=20):
        import requests
        if self._request_fn is not None:
            return self._request_fn(path, payload, timeout)
        return requests.post(REST_BASE + path, headers=self._headers(),
                             json=payload, timeout=timeout)

    def _get(self, path, timeout=20):
        import requests
        if self._request_fn is not None:
            return self._request_fn(path, None, timeout)
        return requests.get(REST_BASE + path, headers=self._headers(),
                            timeout=timeout)

    def me(self):
        return self._get("/users/@me").json()

    def send(self, channel_id, content):
        for chunk in chunk_message(content):
            self._post(f"/channels/{channel_id}/messages",
                       {"content": chunk})

    def typing(self, channel_id):
        try:
            self._post(f"/channels/{channel_id}/typing", {})
        except Exception:
            pass


def bubble_base(text):
    """Deterministic pacing core: longer bubbles breathe longer."""
    return 1.0 + min(len(str(text or "")) / 80.0, 3.0)


def bubble_delay(text):
    """Human texting rhythm: length-based pause plus a little jitter."""
    return bubble_base(text) + random.uniform(0.0, 1.5)


def chunk_message(text, limit=1900):
    """Split for Discord's 2000-char cap, preferring newlines."""
    text = str(text or "")
    if len(text) <= 2000 and len(text) <= limit or not text:
        return [text] if text else []
    out, rest = [], text
    while rest:
        if len(rest) <= limit:
            out.append(rest)
            break
        cut = rest.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = rest.rfind(" ", 0, limit)
        if cut < limit // 2:
            cut = limit
        out.append(rest[:cut])
        rest = rest[cut:].lstrip()
    return out


# ─── Routing (pure, unit-tested) ─────────────────────────────

def is_own(msg, self_id):
    try:
        return str(msg.get("author", {}).get("id")) == str(self_id)
    except Exception:
        return True


def should_reply(msg, self_id, config):
    """DMs, mentions, or allowlisted channels. Never bots/own."""
    try:
        author = msg.get("author", {}) or {}
        if author.get("bot") or is_own(msg, self_id):
            return False
        if not str(msg.get("content", "")).strip():
            return False
        if "guild_id" not in msg:
            return bool(config.get("respond_dm", True))
        if config.get("respond_mentions", True):
            for key in ("<@" + str(self_id) + ">",
                        "<@!" + str(self_id) + ">"):
                if key in msg.get("content", ""):
                    return True
        return str(msg.get("channel_id", "")) in {
            str(c) for c in config.get("channels", [])}
    except Exception:
        return False


def strip_mention(text, self_id):
    out = str(text or "")
    for key in ("<@" + str(self_id) + ">", "<@!" + str(self_id) + ">"):
        out = out.replace(key, "")
    return " ".join(out.split())


class Cooldown:
    """Per-user rate limit with injectable clock (tests)."""

    def __init__(self, seconds, clock=None):
        self.seconds = seconds
        self._clock = clock or time.time
        self._last = {}

    def allow(self, uid):
        now = self._clock()
        last = self._last.get(uid)
        if last is not None and now - last < self.seconds:
            return False
        self._last[uid] = now
        return True


# ─── Adapter (brain wiring) ──────────────────────────────────

def load_config(path=CONFIG_FILE):
    cfg = dict(DEFAULT_CONFIG)
    token = os.environ.get("DISCORD_TOKEN", "")
    if token:
        cfg["token"] = token
    try:
        with open(path, "r", encoding="utf-8") as f:
            file_cfg = json.load(f) or {}
        for k in cfg:
            if file_cfg.get(k) not in (None, ""):
                cfg[k] = file_cfg[k]
        if not token and file_cfg.get("token"):
            cfg["token"] = file_cfg["token"]
    except (OSError, ValueError):
        pass
    cfg["operators"] = {str(o) for o in cfg.get("operators", [])}
    cfg["channels"] = {str(c) for c in cfg.get("channels", [])}
    return cfg


class DiscordAdapter:
    """Gateway <-> brain. All I/O injected for hermetic tests."""

    def __init__(self, brain, rest, config, clock=None):
        self.brain = brain
        self.rest = rest
        self.config = config
        self.cooldown = Cooldown(float(config.get("cooldown_s", 8)),
                                 clock=clock)
        self.self_id = None
        self._stop = threading.Event()
        self._started_at = (clock or time.time)()

    # ── commands (no brain turn spent) ──
    def handle_command(self, msg):
        """Returns handled-bool. Operator kill-switch enforced."""
        text = str(msg.get("content", "")).strip()
        uid = str(msg.get("author", {}).get("id", ""))
        channel = str(msg.get("channel_id", ""))
        if text == "!aura-stop":
            if uid in self.config.get("operators", set()):
                self.rest.send(channel, "Sleeping. Dream of me.")
                self._stop.set()
            return True
        if text == "!aura-status":
            if uid in self.config.get("operators", set()):
                users = len(self.brain.list_users())
                self.rest.send(
                    channel,
                    f"Awake. {users} known souls. "
                    f"Cooldown {self.cooldown.seconds:g}s.")
            return True
        if text.startswith("!choose"):
            parts = text.split()
            if len(parts) == 2:
                from ukft_pack import list_packs, load_pack
                try:
                    load_pack(parts[1])
                    profile = self.brain.onboard(
                        "discord:" + uid, parts[1])
                    self.rest.send(
                        channel,
                        f"Then {profile.name} I am. Come talk to me.")
                except ValueError:
                    self.rest.send(
                        channel,
                        "I can be: "
                        + ", ".join(list_packs()) + ".")
            else:
                from ukft_pack import list_packs
                self.rest.send(channel, "I can be: "
                               + ", ".join(list_packs()) + ".")
            return True
        return False

    # ── chat ──
    def handle_message(self, msg):
        if self.handle_command(msg):
            return "command"
        if not should_reply(msg, self.self_id, self.config):
            return "ignore"
        uid = "discord:" + str(msg.get("author", {}).get("id", ""))
        author = msg.get("author", {}) or {}
        user_name = (msg.get("member", {}).get("nick")
                     or author.get("global_name")
                     or author.get("username") or "")
        channel = str(msg.get("channel_id", ""))
        if not self.cooldown.allow(uid):
            return "cooldown"
        text = strip_mention(msg.get("content", ""), self.self_id)
        if not text:
            return "ignore"
        stop_typing = threading.Event()

        def _type():
            # Immediate: humans see "typing..." at once, not in 8s.
            self.rest.typing(channel)
            while not stop_typing.wait(8.0):
                self.rest.typing(channel)

        typer = threading.Thread(target=_type, daemon=True)
        typer.start()
        try:
            pack = None
            try:
                if not self.brain.get_profile(uid):
                    pack = self.config.get("default_pack") or None
            except Exception:
                pack = None
            resp = self.brain.roleplay(
                uid, text,
                pack=pack, user_name=user_name) if pack else \
                self.brain.roleplay(uid, text, user_name=user_name)
        except Exception as e:
            self.rest.send(channel, "Give me a moment — "
                                    "something snagged.")
            return f"error: {e}"
        finally:
            stop_typing.set()
            typer.join(timeout=10)
        body = str(getattr(resp, "response", "") or "")
        if body.startswith("[AURA]: "):
            body = body[len("[AURA]: "):]
        bubbles = [b.strip() for b in
                   (getattr(resp, "bubbles", None) or [])
                   if b and b.strip()]
        msgs = bubbles if bubbles else chunk_message(body or "...")
        # Sporadic by design: a short human pause before answering,
        # then paced bubbles. Latency becomes rhythm.
        time.sleep(1.0)
        first = True
        for m in msgs:
            if not first:
                time.sleep(bubble_delay(m))
            first = False
            self.rest.send(channel, m)
        return "reply"

    def stopped(self):
        return self._stop.is_set()


def run_bot(config=None, brain=None):
    """Blocking: connect, identify, dispatch until !aura-stop."""
    from ukft_brain_api import get_brain
    config = config or load_config()
    if not config.get("token"):
        print("No token: set DISCORD_TOKEN or discord_config.json, "
              "then retry. Refusing to run blind.")
        return 2
    rest = DiscordREST(config["token"])
    try:
        me = rest.me()
    except Exception as e:
        print(f"Token rejected by Discord: {e}")
        return 3
    adapter = DiscordAdapter(brain or get_brain(), rest, config)
    adapter.self_id = str(me.get("id"))
    print(f"Discord: I am {me.get('username')} ({adapter.self_id}). "
          f"Listening.")
    session_id, seq, resume_url = None, None, None
    backoff = 5
    while not adapter.stopped():
        sock, reader = None, FrameReader()
        try:
            sock = gateway_connect()
            hello = None
            while hello is None:
                for kind, data in _pump(sock, reader, timeout=30):
                    if kind == "text":
                        msg = json.loads(data)
                        if msg.get("op") == OP_HELLO:
                            hello = msg
                            break
            interval = (hello.get("d", {}) or {}).get(
                "heartbeat_interval", 41250) / 1000.0
            if session_id and seq is not None:
                _send(sock, {"op": OP_RESUME, "d": {
                    "token": config["token"],
                    "session_id": session_id, "seq": seq}})
            else:
                _send(sock, {"op": OP_IDENTIFY, "d": {
                    "token": config["token"], "intents": INTENTS,
                    "properties": {"os": "windows",
                                   "browser": "aura_gf",
                                   "device": "aura_gf"}}})
            last_beat = 0.0
            while not adapter.stopped():
                now = time.time()
                if now - last_beat >= interval:
                    _send(sock, {"op": OP_HEARTBEAT, "d": seq})
                    last_beat = now
                for kind, data in _pump(sock, reader, timeout=1):
                    if kind == "text":
                        msg = json.loads(data)
                        op = msg.get("op")
                        if op == OP_HEARTBEAT_ACK:
                            backoff = 5
                        elif op == OP_HEARTBEAT:
                            _send(sock, {"op": OP_HEARTBEAT, "d": seq})
                        elif op == OP_RECONNECT:
                            raise ConnectionError("server asked reconnect")
                        elif op == OP_INVALID_SESSION:
                            session_id, seq = None, None
                            raise ConnectionError("invalid session")
                        elif op == OP_DISPATCH:
                            seq = msg.get("s", seq)
                            if msg.get("t") == "READY":
                                session_id = (msg.get("d", {}) or {}).get(
                                    "session_id", session_id)
                            elif msg.get("t") == "MESSAGE_CREATE":
                                try:
                                    adapter.handle_message(
                                        msg.get("d", {}) or {})
                                except Exception as e:
                                    print(f"[Discord] turn failed: {e}")
                    elif kind == "close":
                        raise ConnectionError("gateway closed")
        except Exception as e:
            print(f"[Discord] link down ({e}); retry in {backoff}s.")
            time.sleep(backoff)
            backoff = min(backoff * 2, 120)
        finally:
            try:
                if sock is not None:
                    sock.sendall(encode_close())
                    sock.close()
            except Exception:
                pass
    print("Discord: stopped by operator.")
    return 0


def _send(sock, payload):
    sock.sendall(encode_frame(json.dumps(payload)))


def _pump(sock, reader, timeout=1):
    r, _, _ = select.select([sock], [], [], timeout)
    if not r:
        return []
    chunk = sock.recv(65536)
    if not chunk:
        raise ConnectionError("gateway EOF")
    reader.feed(chunk)
    return reader.messages()


if __name__ == "__main__":
    raise SystemExit(run_bot())
