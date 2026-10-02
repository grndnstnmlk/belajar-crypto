"""
Institutional Sentry Observability & Error Tracking Engine
Provides end-to-end exception capturing, performance tracing,
and credential-sanitized crash telemetry for Belajar Kripto.
"""

import os
import sys
import time
import socket
import logging
from contextlib import contextmanager
from datetime import datetime

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(os.path.dirname(TOOLS_DIR))
ENV_FILE = os.path.join(ROOT_DIR, ".env")

logger = logging.getLogger("sentry_monitor")

# In-memory telemetry buffer for local diagnostic introspection
_telemetry_state = {
    "initialized": False,
    "sdk_available": False,
    "sdk_version": None,
    "dsn_configured": False,
    "dsn_masked": None,
    "environment": "production",
    "service_name": "trading_desk",
    "traces_sample_rate": 1.0,
    "profiles_sample_rate": 1.0,
    "release": "belajar-crypto@2.0.0",
    "total_captured": 0,
    "recent_events": []
}

# Try importing sentry_sdk
try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.threading import ThreadingIntegration
    _telemetry_state["sdk_available"] = True
    _telemetry_state["sdk_version"] = getattr(sentry_sdk, "VERSION", "installed")
except ImportError:
    sentry_sdk = None
    LoggingIntegration = None
    ThreadingIntegration = None
    _telemetry_state["sdk_available"] = False


def parse_env_file():
    """Parses local .env file and blends with system environment variables."""
    env_vars = {}
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        parts = line.split("=", 1)
                        key = parts[0].strip()
                        val = parts[1].strip().strip('"').strip("'")
                        env_vars[key] = val
        except Exception:
            pass
    # Merge with system environment (system env takes precedence if set)
    for k, v in os.environ.items():
        env_vars[k] = v
    return env_vars


def _mask_dsn(dsn: str) -> str:
    """Masks Sentry DSN so credentials are never leaked in logs or UI."""
    if not dsn:
        return ""
    try:
        if "@" in dsn:
            prefix, rest = dsn.split("@", 1)
            scheme = prefix.split("://")[0] if "://" in prefix else "https"
            return f"{scheme}://***@.../{rest.split('/')[-1] if '/' in rest else 'project'}"
        return dsn[:8] + "***"
    except Exception:
        return "***REDACTED***"


def _sanitize_data(data):
    """
    Recursively scrubs API keys, private secrets, and tokens
    to prevent credential leakage to remote Sentry collectors.
    """
    SENSITIVE_KEYS = {
        "api_key", "secret", "binance_api_key", "binance_api_secret",
        "demo_api_key", "demo_api_secret", "telegram_bot_token",
        "token", "password", "private_key", "authorization", "cookie"
    }

    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(sensitive in k_lower for sensitive in SENSITIVE_KEYS):
                cleaned[k] = "***REDACTED***"
            else:
                cleaned[k] = _sanitize_data(v)
        return cleaned
    elif isinstance(data, list):
        return [_sanitize_data(item) for item in data]
    elif isinstance(data, str):
        # Scrub standard Telegram bot tokens (e.g. 123456789:ABC...)
        if len(data) > 30 and ":" in data and data.split(":")[0].isdigit():
            return "***REDACTED_TOKEN***"
        # Scrub long 64-char hex strings (potential API keys / secret hashes)
        if len(data) == 64 and all(c in "0123456789abcdefABCDEF" for c in data):
            return data[:4] + "***REDACTED***" + data[-4:]
        return data
    return data


def _sentry_before_send(event, hint):
    """
    Sentry before_send hook:
    Strict institutional guardrail scrubbing sensitive payload and request info.
    """
    try:
        return _sanitize_data(event)
    except Exception:
        return event


def init_sentry(service_name: str = "trading_desk", force_reinit: bool = False):
    """
    Initializes Sentry SDK with institutional defaults, automatic credential
    scrubbing, and distributed tracing.
    """
    global _telemetry_state

    if not _telemetry_state["sdk_available"] or sentry_sdk is None:
        logger.warning("[SENTRY] sentry-sdk library not installed; operating in mock mode.")
        return False

    if _telemetry_state["initialized"] and not force_reinit:
        return True

    env = parse_env_file()
    dsn = env.get("SENTRY_DSN", "").strip()
    environment = env.get("SENTRY_ENVIRONMENT", "production").strip()
    traces_rate = float(env.get("SENTRY_TRACES_SAMPLE_RATE", "1.0"))
    profiles_rate = float(env.get("SENTRY_PROFILES_SAMPLE_RATE", "1.0"))
    release = env.get("SENTRY_RELEASE", "belajar-crypto@2.0.0").strip()

    _telemetry_state["service_name"] = service_name
    _telemetry_state["environment"] = environment
    _telemetry_state["traces_sample_rate"] = traces_rate
    _telemetry_state["profiles_sample_rate"] = profiles_rate
    _telemetry_state["release"] = release

    if not dsn:
        _telemetry_state["dsn_configured"] = False
        _telemetry_state["dsn_masked"] = None
        _telemetry_state["initialized"] = False
        return False

    try:
        integrations = [
            ThreadingIntegration(propagate_hub=True)
        ]
        if LoggingIntegration:
            integrations.append(LoggingIntegration(level=logging.INFO, event_level=logging.ERROR))

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            release=release,
            traces_sample_rate=traces_rate,
            profiles_sample_rate=profiles_rate,
            server_name=socket.gethostname(),
            max_breadcrumbs=100,
            attach_stacktrace=True,
            send_default_pii=False,
            before_send=_sentry_before_send,
            integrations=integrations
        )

        # Set default tags
        sentry_sdk.set_tag("app", "belajar_crypto")
        sentry_sdk.set_tag("service", service_name)
        sentry_sdk.set_tag("host", socket.gethostname())

        _telemetry_state["initialized"] = True
        _telemetry_state["dsn_configured"] = True
        _telemetry_state["dsn_masked"] = _mask_dsn(dsn)
        return True
    except Exception as e:
        logger.error(f"[SENTRY] Initialization error: {e}")
        _telemetry_state["initialized"] = False
        return False


def capture_exception(error: Exception, context: dict = None, tags: dict = None, level: str = "error"):
    """
    Captures an exception into Sentry and stores local telemetry entry.
    """
    global _telemetry_state
    _telemetry_state["total_captured"] += 1

    event_record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "exception",
        "error": str(error),
        "error_class": error.__class__.__name__,
        "level": level,
        "tags": tags or {},
        "context": _sanitize_data(context) if context else {}
    }
    _telemetry_state["recent_events"].insert(0, event_record)
    if len(_telemetry_state["recent_events"]) > 50:
        _telemetry_state["recent_events"].pop()

    if _telemetry_state["initialized"] and sentry_sdk is not None:
        try:
            with sentry_sdk.push_scope() as scope:
                scope.set_level(level)
                if tags:
                    for k, v in tags.items():
                        scope.set_tag(k, v)
                if context:
                    scope.set_context("execution_context", _sanitize_data(context))
                event_id = sentry_sdk.capture_exception(error)
                event_record["sentry_event_id"] = event_id
                return event_id
        except Exception as e:
            logger.error(f"[SENTRY] capture_exception failed: {e}")
            return None
    return "local_telemetry_cached"


def capture_message(message: str, level: str = "info", tags: dict = None, extra: dict = None):
    """
    Captures a formatted message or warning into Sentry.
    """
    global _telemetry_state
    _telemetry_state["total_captured"] += 1

    event_record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": "message",
        "message": message,
        "level": level,
        "tags": tags or {},
        "extra": _sanitize_data(extra) if extra else {}
    }
    _telemetry_state["recent_events"].insert(0, event_record)
    if len(_telemetry_state["recent_events"]) > 50:
        _telemetry_state["recent_events"].pop()

    if _telemetry_state["initialized"] and sentry_sdk is not None:
        try:
            with sentry_sdk.push_scope() as scope:
                scope.set_level(level)
                if tags:
                    for k, v in tags.items():
                        scope.set_tag(k, v)
                if extra:
                    scope.set_context("extra_info", _sanitize_data(extra))
                event_id = sentry_sdk.capture_message(message, level=level)
                event_record["sentry_event_id"] = event_id
                return event_id
        except Exception as e:
            logger.error(f"[SENTRY] capture_message failed: {e}")
            return None
    return "local_telemetry_cached"


def add_breadcrumb(category: str, message: str, level: str = "info", data: dict = None):
    """
    Adds a breadcrumb to trace trading actions leading up to an event.
    """
    if _telemetry_state["initialized"] and sentry_sdk is not None:
        try:
            sentry_sdk.add_breadcrumb(
                category=category,
                message=message,
                level=level,
                data=_sanitize_data(data) if data else None
            )
        except Exception:
            pass


@contextmanager
def start_transaction(name: str, op: str = "task"):
    """
    Context manager for performance tracing and span profiling.
    Usage:
        with start_transaction("analyze_orderflow", op="trading_engine"):
            ...
    """
    if _telemetry_state["initialized"] and sentry_sdk is not None:
        try:
            with sentry_sdk.start_transaction(name=name, op=op) as tx:
                yield tx
        except Exception:
            yield None
    else:
        t0 = time.time()
        yield None
        _ = time.time() - t0


def get_sentry_status() -> dict:
    """
    Returns full telemetry health status of Sentry monitoring engine.
    """
    env = parse_env_file()
    dsn = env.get("SENTRY_DSN", "").strip()

    status = dict(_telemetry_state)
    status["dsn_configured"] = bool(dsn)
    if dsn and not status.get("dsn_masked"):
        status["dsn_masked"] = _mask_dsn(dsn)
    status["client_dsn"] = env.get("SENTRY_CLIENT_DSN", dsn) if dsn else ""
    return status


def send_test_event(test_type: str = "message", custom_msg: str = None) -> dict:
    """
    Sends an active diagnostic probe event to verify end-to-end Sentry telemetry.
    """
    msg = custom_msg or f"Belajar Kripto Sentry Diagnostic Probe ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
    tags = {
        "diagnostic_probe": "true",
        "probe_origin": "test_endpoint"
    }

    if test_type == "exception":
        try:
            raise RuntimeError(f"[PROBE] Sentry Simulated Exception: {msg}")
        except Exception as e:
            evt_id = capture_exception(e, context={"probe_type": "exception_test"}, tags=tags)
            return {
                "success": True,
                "type": "exception",
                "message": str(e),
                "event_id": evt_id,
                "initialized": _telemetry_state["initialized"]
            }
    else:
        evt_id = capture_message(msg, level="info", tags=tags, extra={"probe_type": "message_test"})
        return {
            "success": True,
            "type": "message",
            "message": msg,
            "event_id": evt_id,
            "initialized": _telemetry_state["initialized"]
        }


# Auto-initialize on import with defaults
init_sentry()
