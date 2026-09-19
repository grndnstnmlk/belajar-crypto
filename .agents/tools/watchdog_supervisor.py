"""
Auto-Healing Watchdog Supervisor Daemon
Supervises Mission Control Dashboard Server and Autonomous Trading Desk.
Detects unexpected terminations, unhandled exceptions, or port collisions,
and automatically revives processes with exponential backoff and Telegram alerts.
"""

import http.client
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime

# Windows Console UTF-8
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
ROOT_DIR = os.path.dirname(os.path.dirname(TOOLS_DIR))
STATE_FILE = os.path.join(DATA_DIR, "watchdog_state.json")

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

sys.path.insert(0, TOOLS_DIR)
try:
    import telegram_notifier
except Exception:
    telegram_notifier = None

class ServiceWatcher:
    def __init__(self, name, command, port=None, check_endpoint=None):
        self.name = name
        self.command = command
        self.port = port
        self.check_endpoint = check_endpoint
        self.process = None
        self.restart_count = 0
        self.last_start_time = 0
        self.consecutive_crashes = 0
        self.log_file = os.path.join(LOGS_DIR, f"{name.lower().replace(' ', '_')}.log")

    def is_alive(self):
        if self.process is None:
            return False
        return self.process.poll() is None

    def check_http_health(self):
        if not self.port or not self.check_endpoint:
            return True
        try:
            conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3.0)
            conn.request("GET", self.check_endpoint)
            res = conn.getresponse()
            conn.close()
            return res.status in (200, 204, 302)
        except Exception:
            return False

    def kill_stale_port(self):
        if not self.port:
            return
        try:
            out = subprocess.check_output(f"netstat -ano | findstr :{self.port}", shell=True).decode("utf-8", errors="ignore")
            for line in out.splitlines():
                if "LISTENING" in line:
                    parts = line.strip().split()
                    pid = int(parts[-1])
                    if self.process is None or pid != self.process.pid:
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                        time.sleep(0.5)
        except Exception:
            pass

    def start(self):
        self.kill_stale_port()
        flags = (0x00000008 | 0x00000200) if sys.platform == "win32" else 0  # DETACHED_PROCESS / CREATE_NEW_PROCESS_GROUP
        try:
            log_handle = open(self.log_file, "a", encoding="utf-8")
            self.process = subprocess.Popen(
                self.command,
                cwd=ROOT_DIR,
                stdout=log_handle,
                stderr=log_handle,
                stdin=subprocess.DEVNULL,
                creationflags=flags
            )
            self.last_start_time = time.time()
            print(f"🚀 [{datetime.now().strftime('%H:%M:%S')}] Started {self.name} (PID: {self.process.pid})")
            return True
        except Exception as e:
            print(f"❌ Failed to start {self.name}: {e}")
            return False

    def restart(self, reason="Crash"):
        self.restart_count += 1
        self.consecutive_crashes += 1
        backoff = min(30, 2 ** min(self.consecutive_crashes, 5))

        print(f"⚠️ [{datetime.now().strftime('%H:%M:%S')}] {self.name} stopped ({reason}). Restart #{self.restart_count} in {backoff}s...")

        # Telegram Alert
        if telegram_notifier:
            try:
                alert_text = (
                    f"🛡️ <b>WATCHDOG AUTO-HEALING</b>\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"⚠️ Layanan <b>{self.name}</b> terhenti ({reason}).\n"
                    f"🔄 Memulai ulang otomatis dalam <code>{backoff}s</code> (Restart ke-{self.restart_count})..."
                )
                telegram_notifier.send_telegram_msg(alert_text)
            except Exception:
                pass

        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=2.0)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

        time.sleep(backoff)
        success = self.start()
        if success:
            if telegram_notifier:
                try:
                    telegram_notifier.send_telegram_msg(f"✅ <b>WATCHDOG</b>: Layanan <b>{self.name}</b> berhasil dipulihkan (PID: {self.process.pid}).")
                except Exception:
                    pass
        return success

    def tick(self):
        """Performs a health check cycle."""
        if not self.is_alive():
            exit_code = self.process.poll() if self.process else "None"
            self.restart(f"Exit code: {exit_code}")
            return False

        # If it has been alive for > 60s, reset consecutive crash counter
        if time.time() - self.last_start_time > 60:
            self.consecutive_crashes = 0

        # HTTP health check if applicable
        if self.port and self.check_endpoint:
            if not self.check_http_health():
                print(f"⚠️ [{datetime.now().strftime('%H:%M:%S')}] {self.name} HTTP check failed on port {self.port}.")
                self.restart("HTTP Endpoint Unresponsive")
                return False

        return True

def run_supervisor():
    print("=" * 65)
    print("       🛡️  AUTONOMOUS AUTO-HEALING WATCHDOG SUPERVISOR")
    print(f"       ⏱️  Check Interval: 5 seconds")
    print(f"       📁  Logs Directory: {LOGS_DIR}")
    print("=" * 65)

    dashboard = ServiceWatcher(
        name="Dashboard Server",
        command=[sys.executable, "-u", os.path.join(TOOLS_DIR, "dashboard_server.py")],
        port=5000,
        check_endpoint="/api/ws/status"
    )

    trading_desk = ServiceWatcher(
        name="Trading Desk Autopilot",
        command=[sys.executable, "-u", os.path.join(TOOLS_DIR, "trading_desk.py"), "run", "--mode", "HYBRID"]
    )

    services = [dashboard, trading_desk]

    # Auto-detect and supervise Ollama Local LLM if installed
    try:
        from local_cognitive_brain import find_ollama_executable
        ollama_exe = find_ollama_executable()
        if ollama_exe:
            ollama_watcher = ServiceWatcher(
                name="Ollama Local LLM",
                command=[ollama_exe, "serve"],
                port=11434,
                check_endpoint="/api/tags"
            )
            services.insert(0, ollama_watcher)
            print(f"🤖 [Watchdog] Detected Ollama at {ollama_exe}. Adding to supervised services.")
    except Exception:
        pass

    # Initial start
    for s in services:
        s.start()

    last_state_save = 0
    last_console_heartbeat = 0

    def cleanup(signum=None, frame=None):
        print("\n🛑 Shutting down Watchdog Supervisor and managed services...")
        for s in services:
            if s.process and s.process.poll() is None:
                print(f"Terminating {s.name} (PID: {s.process.pid})...")
                try:
                    s.process.terminate()
                except Exception:
                    pass
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    while True:
        try:
            for s in services:
                s.tick()

            now = time.time()

            # Save state every 10s
            if now - last_state_save >= 10:
                last_state_save = now
                state = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "services": {
                        s.name: {
                            "pid": s.process.pid if s.process else None,
                            "alive": s.is_alive(),
                            "restart_count": s.restart_count,
                            "uptime_seconds": round(now - s.last_start_time, 1) if s.last_start_time else 0
                        }
                        for s in services
                    }
                }
                try:
                    with open(STATE_FILE, "w", encoding="utf-8") as f:
                        json.dump(state, f, indent=2)
                except Exception:
                    pass

            # Heartbeat print every 60s
            if now - last_console_heartbeat >= 60:
                last_console_heartbeat = now
                statuses = " | ".join(f"{s.name}: {'🟢 ALIVE' if s.is_alive() else '🔴 DOWN'} (Restarts: {s.restart_count})" for s in services)
                print(f"💓 [{datetime.now().strftime('%H:%M:%S')}] {statuses}")

            time.sleep(5.0)
        except KeyboardInterrupt:
            cleanup()
        except Exception as e:
            print(f"Watchdog loop error: {e}")
            time.sleep(5.0)

if __name__ == "__main__":
    run_supervisor()
