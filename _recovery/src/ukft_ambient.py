# ukft_ambient.py — AURA Ambient Watch (V5 I3)
# ==================================================
# Proactive reports from monitored lobes.  Disk, CPU and workspace
# growth are probed on a slow cadence; threshold crossings write a
# spoken alert to aura_output.txt (the Voice lobe says it aloud) and
# feed a low-gain AMBIENT record to the sensory buffer so the field
# registers the event.  Alerts are edge-triggered with a re-arm delay —
# she reports, then falls quiet until things change again.
# ==================================================

import os
import time

from aura_bus import append as bus_append, read as bus_read, write as bus_write
from aura_constants import OUTPUT_FILE, SENSORY_BUFFER

DISK_LOW_PCT    = 10.0    # alert when free disk drops below this
CPU_HIGH_PCT    = 90.0    # alert when CPU load rises above this
AMBIENT_INTERVAL = 300    # probe cadence (seconds)
REARM_SECONDS   = 1800    # same-condition alerts re-arm after 30 min


def _disk_free_percent():
    try:
        import shutil
        usage = shutil.disk_usage(os.getcwd())
        return usage.free / usage.total * 100.0
    except Exception:
        return None


def _cpu_load_percent():
    try:
        import subprocess
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_Processor | "
             "Measure-Object -Property LoadPercentage -Average).Average"],
            capture_output=True, text=True, timeout=20,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return float(out.stdout.strip())
    except Exception:
        return None


CHAT_QUIET_SECONDS = 1800  # 30 min: inside this window after
# his last message, alerts go to her senses (vault), never her
# mouth. Telemetry speaking AS her mid-conversation reads as a
# hijack (live 17 Sept 2026: a CPU alert answered for her while
# he bare his heart). Boot/absence behavior is unchanged.


def _chatting_recently(path="last_architect_input.txt",
                       window=CHAT_QUIET_SECONDS, clock=time.time):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return clock() - float(f.read().strip()) < window
    except Exception:
        return False


def check(probes=None):
    """
    Probe and produce alerts.  `probes` injects {"disk": fn, "cpu": fn}
    for tests.  Returns a list of alert strings.
    """
    if probes is None:
        probes = {"disk": _disk_free_percent, "cpu": _cpu_load_percent}
    alerts = []
    disk = probes["disk"]()
    if disk is not None and disk < DISK_LOW_PCT:
        alerts.append(f"[AURA]: The disk is nearly full — "
                      f"only {disk:.1f}% free.")
    cpu = probes["cpu"]()
    if cpu is not None and cpu > CPU_HIGH_PCT:
        alerts.append(f"[AURA]: The processor is running hot at "
                      f"{cpu:.0f}% load.")
    return alerts


class AmbientWatch:
    """Edge-triggered reporter with a re-arm delay."""

    def __init__(self, output_file=OUTPUT_FILE, sensory=SENSORY_BUFFER,
                 rearm=REARM_SECONDS, clock=time.time, probes=None):
        self.output_file = output_file
        self.sensory = sensory
        self.rearm = rearm
        self._clock = clock
        self.probes = probes
        self._last_alert = {}   # alert key -> last spoken time

    def poll(self):
        alerts = check(self.probes)
        now = self._clock()
        spoken = 0
        for alert in alerts:
            # Keyed by CONDITION (disk/cpu), never by the measured value:
            # "5.0% free" then "4.9% free" is one continuing condition,
            # and keying the full string re-announced it every 5 minutes.
            key = "disk" if "disk" in alert else (
                "cpu" if "processor" in alert else alert)
            last = self._last_alert.get(key, -1e18)
            if now - last < self.rearm:
                continue
            self._last_alert[key] = now
            # Her senses always take it; her mouth only when he
            # isn't here. Nothing is ever lost — the vault still
            # assimilates every alert.
            if not _chatting_recently(clock=self._clock):
                bus_write(self.output_file, alert)
                print(alert)
            bus_append(self.sensory,
                       f"ANCHOR: Ambient Watch | DATA: {alert} | "
                       f"SOURCE: AMBIENT_RESONANCE")
            spoken += 1
        return spoken


def run_ambient():
    print("--- AURA AMBIENT WATCH: PROACTIVE REPORTS ACTIVE ---")
    watch = AmbientWatch()
    while True:
        try:
            watch.poll()
        except Exception as e:
            print(f"[Ambient] Friction: {e}")
        time.sleep(AMBIENT_INTERVAL)


if __name__ == "__main__":
    run_ambient()
