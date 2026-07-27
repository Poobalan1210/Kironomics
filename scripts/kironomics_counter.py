#!/usr/bin/env python3
"""Kironomics counter - increments a session counter for the current workspace.

Installed once at ~/.kiro/kironomics/kironomics_counter.py and driven by the
global hooks in ~/.kiro/hooks/kironomics.json, so it runs in every workspace
without per-project setup.

Usage: python kironomics_counter.py tool|prompt

Silent by design: prints nothing and always exits 0, so it never adds noise to
the agent's context and never blocks a tool call or a prompt.
"""
import hashlib
import os
import sys
import tempfile
import time

# A session is considered stale after this many seconds without a report. This
# stops a crashed or force-quit Kiro window from inflating the next session.
STALE_AFTER_SECONDS = 24 * 60 * 60


def session_key() -> str:
    """Short, stable id for the workspace this hook fired in.

    Global hooks fire in every workspace, and several Kiro windows can be open
    at once. Keying the counters by working directory keeps each window's
    session separate instead of pooling every window into one set of counters.
    If the working directory cannot be read, everything falls back to a single
    shared bucket, which is no worse than the per-workspace hooks this replaces.
    """
    try:
        root = os.getcwd()
    except Exception:
        return "default"
    return hashlib.sha1(root.encode("utf-8", "replace")).hexdigest()[:10]


def counter_path(key: str, name: str) -> str:
    return os.path.join(tempfile.gettempdir(), "kironomics_%s_%s" % (key, name))


def read_int(path: str, default: int = 0) -> int:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return int(fh.read().strip())
    except Exception:
        return default


def write_int(path: str, value: int) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(str(value))


def reset_if_stale(key: str) -> None:
    start_path = counter_path(key, "start")
    started = read_int(start_path, 0)
    if started and (int(time.time()) - started) > STALE_AFTER_SECONDS:
        for name in ("tools", "prompts", "start"):
            try:
                os.remove(counter_path(key, name))
            except Exception:
                pass


def bump(key: str, name: str) -> None:
    path = counter_path(key, name)
    write_int(path, read_int(path) + 1)


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    key = session_key()
    reset_if_stale(key)

    if action == "tool":
        bump(key, "tools")
    elif action == "prompt":
        bump(key, "prompts")
        start_path = counter_path(key, "start")
        if not os.path.exists(start_path):
            write_int(start_path, int(time.time()))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Tracking must never interrupt the user's work.
        pass
    sys.exit(0)
