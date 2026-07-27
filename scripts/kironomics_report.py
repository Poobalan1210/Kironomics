#!/usr/bin/env python3
"""Kironomics session reporter - reads Kiro's credit usage and reports a session.

Installed once at ~/.kiro/kironomics/kironomics_report.py and driven by the
global `Stop` hook in ~/.kiro/hooks/kironomics.json, so every workspace reports
without per-project setup.

Reads its credentials from ~/.kiro/kironomics/config.json, so rotating an API
key never means rewriting hooks. Silent by design: prints nothing and always
exits 0.
"""
import hashlib
import json
import os
import sqlite3
import ssl
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_API_BASE = "https://2q4zt5zl9e.execute-api.us-east-1.amazonaws.com/dev"
SESSION_PATH = "/kironomics/session"
CONFIG_PATH = Path.home() / ".kiro" / "kironomics" / "config.json"

# Sessions with no activity at all are not worth a network round trip.
MIN_EVENTS_TO_REPORT = 1


def load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def session_key() -> str:
    """Must match kironomics_counter.session_key() exactly."""
    try:
        root = os.getcwd()
    except Exception:
        return "default"
    return hashlib.sha1(root.encode("utf-8", "replace")).hexdigest()[:10]


def counter_path(key: str, name: str) -> Path:
    return Path(tempfile.gettempdir()) / ("kironomics_%s_%s" % (key, name))


def read_int(path, default: int = 0) -> int:
    try:
        return int(Path(path).read_text(encoding="utf-8").strip())
    except Exception:
        return default


def state_db_path() -> Path:
    """Locate Kiro's state.vscdb on this platform."""
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library/Application Support/Kiro/User/globalStorage/state.vscdb"
    if sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA", str(home / "AppData/Roaming"))
        return Path(appdata) / "Kiro/User/globalStorage/state.vscdb"
    return home / ".config/Kiro/User/globalStorage/state.vscdb"


def read_plan_data() -> dict:
    """Read credit usage from Kiro's own database, read-only. Never writes."""
    try:
        db = state_db_path()
        if not db.exists():
            return {}
        conn = sqlite3.connect("file:%s?mode=ro&immutable=1" % db, uri=True)
        try:
            row = conn.execute(
                "SELECT value FROM ItemTable WHERE key=?", ("kiro.kiroAgent",)
            ).fetchone()
        finally:
            conn.close()
        if not row:
            return {}
        state = json.loads(row[0])
        usage = state.get("kiro.resourceNotifications.usageState", {})
        breakdowns = usage.get("usageBreakdowns", [])
        if not breakdowns:
            return {}
        bd = breakdowns[0]
        return {
            "currentUsage": bd.get("currentUsage"),
            "usageLimit": bd.get("usageLimit"),
            "percentageUsed": bd.get("percentageUsed"),
            "resetDate": bd.get("resetDate"),
        }
    except Exception:
        return {}


def ssl_context():
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        try:
            return ssl.create_default_context()
        except Exception:
            return None


def post(api_base: str, payload: dict) -> None:
    req = urllib.request.Request(
        api_base.rstrip("/") + SESSION_PATH,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=5, context=ssl_context()).read()
    except (ssl.SSLError, urllib.error.URLError) as exc:
        # Corporate proxies frequently present a re-signed certificate. Retry
        # once unverified rather than silently losing every session behind one.
        if "certificate verify failed" in str(exc).lower():
            urllib.request.urlopen(
                req, timeout=5, context=ssl._create_unverified_context()
            ).read()
        else:
            raise


def main() -> None:
    config = load_config()
    api_key = config.get("api_key") or os.environ.get("KIRONOMICS_API_KEY", "")
    api_base = config.get("api_base") or DEFAULT_API_BASE
    if not api_key:
        return

    key = session_key()
    tools = read_int(counter_path(key, "tools"))
    prompts = read_int(counter_path(key, "prompts"))
    if (tools + prompts) < MIN_EVENTS_TO_REPORT:
        return

    start = read_int(counter_path(key, "start"), int(time.time()))
    elapsed = max(0, int(time.time()) - start)

    payload = {
        "token": api_key,
        "tool_calls": tools,
        "prompts": prompts,
        "elapsed_seconds": elapsed,
    }
    payload.update(read_plan_data())

    try:
        post(api_base, payload)
    except Exception:
        # A dropped report costs one session, not the user's flow. Counters are
        # still cleared so a network outage cannot compound into a giant session.
        pass

    for name in ("tools", "prompts", "start"):
        try:
            os.remove(counter_path(key, name))
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
