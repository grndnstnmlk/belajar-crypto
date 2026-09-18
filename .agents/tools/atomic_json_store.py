"""
atomic_json_store.py - High-Performance Cross-Thread Atomic Transactional JSON Store
Provides thread-safe, crash-resilient JSON reads and writes with zero file corruption.

Features:
1. Process-wide threading.RLock per file path to prevent concurrent race conditions.
2. Atomic write pattern: writes to unique .tmp file, flushes/fsyncs, then executes os.replace().
3. Self-healing read retries with exponential micro-backoff to handle transient locks.
4. Transactional read-modify-write helper (atomic_update_json).
"""

import json
import os
import sys
import time
import threading
import tempfile
from typing import Any, Callable, Dict, Optional

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

_LOCK_REGISTRY: Dict[str, threading.RLock] = {}
_REGISTRY_LOCK = threading.Lock()

def _get_file_lock(filepath: str) -> threading.RLock:
    """Returns or creates a persistent reentrant lock for the specified canonical path."""
    norm_path = os.path.abspath(os.path.normpath(filepath))
    with _REGISTRY_LOCK:
        if norm_path not in _LOCK_REGISTRY:
            _LOCK_REGISTRY[norm_path] = threading.RLock()
        return _LOCK_REGISTRY[norm_path]

def atomic_read_json(filepath: str, default: Any = None, max_retries: int = 3) -> Any:
    """
    Thread-safely reads and parses a JSON file with automatic retry on transient read locks.
    Returns default if the file does not exist or is corrupted.
    """
    if not os.path.exists(filepath):
        return default

    lock = _get_file_lock(filepath)
    with lock:
        for attempt in range(max_retries):
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                    if not content:
                        if attempt < max_retries - 1:
                            time.sleep(0.05)
                            continue
                        return default
                    return json.loads(content)
            except (json.JSONDecodeError, OSError) as e:
                if attempt < max_retries - 1:
                    time.sleep(0.05 * (attempt + 1))
                else:
                    return default
        return default

def atomic_write_json(filepath: str, data: Any, indent: int = 2, ensure_ascii: bool = False) -> bool:
    """
    Thread-safely and atomically writes data to a JSON file.
    Uses Write-to-Temp and os.replace() to guarantee zero 0-byte corrupted files.
    """
    lock = _get_file_lock(filepath)
    with lock:
        target_dir = os.path.dirname(os.path.abspath(filepath))
        os.makedirs(target_dir, exist_ok=True)

        temp_file = None
        try:
            # Create temp file in the exact same directory to ensure atomic os.replace across volumes
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=target_dir,
                delete=False,
                prefix="atom_",
                suffix=".tmp"
            ) as tf:
                temp_file = tf.name
                json.dump(data, tf, indent=indent, ensure_ascii=ensure_ascii)
                tf.flush()
                os.fsync(tf.fileno())

            # Atomic replace (guaranteed atomic on Windows & POSIX)
            os.replace(temp_file, filepath)
            return True
        except Exception as e:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            raise e

def atomic_update_json(filepath: str, updater_func: Callable[[Any], Any], default: Any = None) -> Any:
    """
    Atomically performs read-modify-write on a JSON file under an uninterrupted lock.
    updater_func receives current data (or default) and must return the modified data.
    """
    lock = _get_file_lock(filepath)
    with lock:
        current_data = atomic_read_json(filepath, default=default)
        new_data = updater_func(current_data)
        atomic_write_json(filepath, new_data)
        return new_data

if __name__ == "__main__":
    print("Testing atomic_json_store...")
    test_path = os.path.join(os.path.dirname(__file__), "test_atomic.json")
    try:
        atomic_write_json(test_path, {"status": "ok", "value": 42})
        data = atomic_read_json(test_path)
        assert data["value"] == 42
        
        def update_val(d):
            d["value"] += 10
            return d
        
        updated = atomic_update_json(test_path, update_val)
        assert updated["value"] == 52
        print("✅ atomic_json_store self-test passed!")
    finally:
        if os.path.exists(test_path):
            os.remove(test_path)
