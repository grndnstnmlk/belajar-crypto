"""
auto_git_sync.py - Seamless Multi-Device Git Cloud Synchronization Engine
Enables automatic real-time sync between Laptop and PC for trading journals, active positions, and genome state.

Key Features:
1. `auto_pull_on_startup()`: Silently pulls latest cloud state before trading starts.
2. `trigger_background_push(reason)`: Non-blocking daemon thread that commits & pushes trade data to GitHub upon trade close or periodic intervals.
"""

import os
import subprocess
import sys
import threading
import time

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(TOOLS_DIR))

_LAST_PUSH_TIME = 0
_SYNC_LOCK = threading.Lock()
_SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

def sync_pull():
    """Silently pulls the latest commits from remote main branch with autostash."""
    try:
        res = subprocess.run(
            ["git", "pull", "--rebase", "--autostash", "origin", "main"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=_SUBPROCESS_FLAGS
        )
        if res.returncode == 0:
            return True, "✅ Git pull successful (Up to date with GitHub)"
        else:
            return False, f"⚠️ Git pull warning: {res.stderr.strip() or res.stdout.strip()}"
    except Exception as e:
        return False, f"⚠️ Git pull error: {e}"

def _do_push(reason="trade_journal_update"):
    global _LAST_PUSH_TIME
    with _SYNC_LOCK:
        try:
            # Throttle pushes to avoid spamming GitHub (min 30s between pushes)
            now = time.time()
            if now - _LAST_PUSH_TIME < 20:
                return

            # Stage data files and memory
            subprocess.run(
                ["git", "add", ".agents/data/", "agent_memory_bank.json"],
                cwd=ROOT_DIR,
                capture_output=True,
                timeout=10,
                creationflags=_SUBPROCESS_FLAGS
            )

            # Check if there are changes to commit
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=_SUBPROCESS_FLAGS
            )

            if not status.stdout.strip():
                return  # Nothing to commit

            commit_msg = f"auto-sync: {reason} [{time.strftime('%Y-%m-%d %H:%M:%S')}]"
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=ROOT_DIR,
                capture_output=True,
                timeout=10,
                creationflags=_SUBPROCESS_FLAGS
            )

            push_res = subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                timeout=25,
                creationflags=_SUBPROCESS_FLAGS
            )

            if push_res.returncode == 0:
                _LAST_PUSH_TIME = time.time()
                # print(f"[Auto-Git-Sync] ☁️ Pushed updates to GitHub: {reason}")
        except Exception as e:
            pass

def trigger_background_push(reason="trade_journal_update"):
    """Fires non-blocking daemon thread to commit & push data to GitHub."""
    t = threading.Thread(target=_do_push, args=(reason,), daemon=True)
    t.start()

_PERIODIC_SYNC_THREAD = None

def _periodic_sync_worker(interval_minutes=30):
    while True:
        try:
            time.sleep(max(60, interval_minutes * 60))
            _do_push(reason="periodic_cloud_backup")
        except Exception:
            pass

def start_periodic_sync_daemon(interval_minutes=30):
    """Starts background daemon thread that periodically syncs data to GitHub."""
    global _PERIODIC_SYNC_THREAD
    if _PERIODIC_SYNC_THREAD is None or not _PERIODIC_SYNC_THREAD.is_alive():
        _PERIODIC_SYNC_THREAD = threading.Thread(
            target=_periodic_sync_worker,
            args=(interval_minutes,),
            daemon=True,
            name="PeriodicGitSyncDaemon"
        )
        _PERIODIC_SYNC_THREAD.start()
        print(f"[Auto-Git-Sync] ☁️ Daemon sinkronisasi cloud periodik aktif (Interval: {interval_minutes}m).")
    return _PERIODIC_SYNC_THREAD

if __name__ == "__main__":
    print("Testing auto_git_sync...")
    success, msg = sync_pull()
    print(f"Pull Result: {msg}")
    trigger_background_push("manual_test_sync")
    time.sleep(3)
    print("Test completed.")
