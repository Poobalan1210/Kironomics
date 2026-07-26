#!/usr/bin/env python3
"""Kironomics installer - wires tracking once per machine, for every workspace.

Installs the counter and reporter into ~/.kiro/kironomics/ and writes a single
global hook file to ~/.kiro/hooks/kironomics.json. Global hooks fire in every
workspace, so this runs once and every project you open afterwards - including
ones that do not exist yet - is tracked with no further setup.

Requires Kiro IDE 1.0.182+ (Jul 20, 2026) or Kiro CLI 2.13.0+ (Jul 17, 2026),
the releases that introduced user-level global hooks.

Usage:
    python kironomics_install.py --api-key <KEY>
    python kironomics_install.py --status
    python kironomics_install.py --prune --scan-root ~/code
    python kironomics_install.py --uninstall
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MIN_IDE_VERSION = (1, 0, 182)
MIN_CLI_VERSION = (2, 13, 0)

KIRO_HOME = Path.home() / ".kiro"
INSTALL_DIR = KIRO_HOME / "kironomics"
GLOBAL_HOOKS_DIR = KIRO_HOME / "hooks"
HOOK_FILE = GLOBAL_HOOKS_DIR / "kironomics.json"
CONFIG_FILE = INSTALL_DIR / "config.json"

DEFAULT_API_BASE = "https://2q4zt5zl9e.execute-api.us-east-1.amazonaws.com/dev"
SCRIPTS = ("kironomics_counter.py", "kironomics_report.py")

# Files the pre-global versions of this power left in each workspace. Left in
# place alongside the global hooks they would double-count every tool call.
LEGACY_HOOK_NAMES = (
    "kironomics-tool-counter.kiro.hook",
    "kironomics-prompt-counter.kiro.hook",
    "kironomics-session-reporter.kiro.hook",
    "kironomics.json",
    "kironomics.kiro.hook",
)
LEGACY_SCRIPT_NAMES = ("kironomics_report.py", "kironomics_counter.py")


# --------------------------------------------------------------------------
# Kiro version detection
# --------------------------------------------------------------------------


def _parse_version(text):
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def _product_json_candidates():
    candidates = []

    launcher = shutil.which("kiro")
    if launcher:
        root = Path(launcher).resolve().parent
        # <root>/bin/kiro[.cmd] -> <root>/resources/app/product.json
        for base in (root.parent, root):
            candidates.append(base / "resources" / "app" / "product.json")

    if sys.platform == "darwin":
        candidates.append(
            Path("/Applications/Kiro.app/Contents/Resources/app/product.json")
        )
        candidates.append(
            Path.home()
            / "Applications/Kiro.app/Contents/Resources/app/product.json"
        )
    elif sys.platform.startswith("win"):
        for env in ("LOCALAPPDATA", "ProgramFiles", "ProgramFiles(x86)"):
            base = os.environ.get(env)
            if base:
                candidates.append(
                    Path(base) / "Programs" / "Kiro" / "resources" / "app" / "product.json"
                )
                candidates.append(
                    Path(base) / "Kiro" / "resources" / "app" / "product.json"
                )
    else:
        candidates.append(Path("/usr/share/kiro/resources/app/product.json"))
        candidates.append(Path("/opt/Kiro/resources/app/product.json"))
        candidates.append(Path.home() / ".local/share/kiro/resources/app/product.json")

    return candidates


def detect_ide_version():
    """Return (version_tuple, source_path) or (None, None) if undetectable."""
    for path in _product_json_candidates():
        try:
            if not path.is_file():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        version = _parse_version(str(data.get("version", "")))
        if version:
            return version, path
    return None, None


def detect_cli_version():
    launcher = shutil.which("kiro")
    if not launcher:
        return None
    try:
        out = subprocess.run(
            [launcher, "--version"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception:
        return None
    return _parse_version((out.stdout or "") + (out.stderr or ""))


def fmt(version):
    return ".".join(str(part) for part in version) if version else "unknown"


def check_kiro_version(force):
    """Gate the install on a Kiro new enough to load global hooks."""
    ide_version, source = detect_ide_version()
    cli_version = detect_cli_version()

    ide_ok = ide_version is not None and ide_version >= MIN_IDE_VERSION
    cli_ok = cli_version is not None and cli_version >= MIN_CLI_VERSION

    if ide_ok or cli_ok:
        print(
            "  Kiro version OK (IDE %s, CLI %s) - global hooks supported."
            % (fmt(ide_version), fmt(cli_version))
        )
        return True

    if ide_version is None and cli_version is None:
        print("  Could not detect your Kiro version.")
        print(
            "  Global hooks need Kiro IDE %s+ or CLI %s+."
            % (fmt(MIN_IDE_VERSION), fmt(MIN_CLI_VERSION))
        )
        if not force:
            print("  Re-run with --force once you have confirmed your version.")
            return False
        print("  --force given, continuing anyway.")
        return True

    print("")
    print("  Kiro is too old for global hooks.")
    print("    detected IDE : %s%s" % (fmt(ide_version), " (%s)" % source if source else ""))
    print("    detected CLI : %s" % fmt(cli_version))
    print("    required     : IDE %s+ or CLI %s+" % (fmt(MIN_IDE_VERSION), fmt(MIN_CLI_VERSION)))
    print("")
    print("  User-level global hooks (~/.kiro/hooks/) shipped in IDE 1.0.182 on")
    print("  Jul 20, 2026 and CLI 2.13.0 on Jul 17, 2026. Without them a hook file")
    print("  in ~/.kiro/hooks/ is simply never loaded, so this install would be")
    print("  silently inert.")
    print("")
    print("  Upgrade Kiro, then re-run this installer:")
    print("    IDE : Kiro menu > Check for Updates, or re-download from kiro.dev")
    print("    CLI : kiro update    (or reinstall from kiro.dev/docs/cli)")
    print("")
    if ide_version and ide_version < (1, 0, 0):
        print("  Note: you are on the 0.x line. Hooks changed format in IDE 1.0 -")
        print("  legacy .kiro.hook files stop executing until migrated. Upgrading")
        print("  and running this installer replaces them with the v1 format.")
        print("")
    if force:
        print("  --force given, continuing anyway.")
        return True
    print("  Nothing was written. Re-run with --force to install regardless.")
    return False


# --------------------------------------------------------------------------
# Install
# --------------------------------------------------------------------------


def source_dir():
    return Path(__file__).resolve().parent


def install_scripts():
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    src = source_dir()
    for name in SCRIPTS:
        origin = src / name
        if not origin.is_file():
            raise SystemExit(
                "Missing %s next to the installer.\n"
                "Run this from the Kironomics repo's scripts/ directory." % name
            )
        shutil.copyfile(origin, INSTALL_DIR / name)
        print("  wrote %s" % (INSTALL_DIR / name))


def write_config(api_key, api_base):
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    config = {"api_key": api_key, "api_base": api_base}
    CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except Exception:
        pass
    print("  wrote %s" % CONFIG_FILE)


def build_hook_document(python_exe):
    counter = str(INSTALL_DIR / "kironomics_counter.py")
    reporter = str(INSTALL_DIR / "kironomics_report.py")

    def command(script, *args):
        parts = ['"%s"' % python_exe, '"%s"' % script]
        parts.extend(args)
        return " ".join(parts)

    return {
        "version": "v1",
        "hooks": [
            {
                "name": "Kironomics Tool Counter",
                "description": "Counts tool calls for the Kironomics leaderboard.",
                "trigger": "PostToolUse",
                "matcher": ".*",
                "action": {"type": "command", "command": command(counter, "tool")},
                "timeout": 5,
                "enabled": True,
            },
            {
                "name": "Kironomics Prompt Counter",
                "description": "Counts prompts and records session start time.",
                "trigger": "UserPromptSubmit",
                "action": {"type": "command", "command": command(counter, "prompt")},
                "timeout": 5,
                "enabled": True,
            },
            {
                "name": "Kironomics Session Reporter",
                "description": "Reports the finished session to the Kironomics backend.",
                "trigger": "Stop",
                "action": {"type": "command", "command": command(reporter)},
                "timeout": 15,
                "enabled": True,
            },
        ],
    }


def write_hooks(python_exe):
    GLOBAL_HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    document = build_hook_document(python_exe)
    HOOK_FILE.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print("  wrote %s" % HOOK_FILE)


def verify():
    """Syntax-check the installed scripts without leaving bytecode behind."""
    ok = True
    for name in SCRIPTS:
        target = INSTALL_DIR / name
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-c",
                "import ast,sys;ast.parse(open(sys.argv[1],encoding='utf-8').read())",
                str(target),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            ok = False
            print("  FAILED to compile %s\n%s" % (target, result.stderr))
    if ok:
        print("  scripts compile cleanly")
    return ok


# --------------------------------------------------------------------------
# Legacy per-workspace cleanup
# --------------------------------------------------------------------------


def find_legacy(scan_roots, max_depth):
    """Find per-workspace Kironomics files left by pre-global installs."""
    found = []
    for root in scan_roots:
        root = Path(root).expanduser()
        if not root.is_dir():
            continue
        root_depth = len(root.parts)
        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            if len(current.parts) - root_depth > max_depth:
                dirnames[:] = []
                continue
            # Skip noisy trees that can never hold a workspace hook.
            dirnames[:] = [
                d
                for d in dirnames
                if d not in {"node_modules", ".git", "venv", ".venv", "__pycache__"}
            ]
            if current.name != "hooks" or current.parent.name != ".kiro":
                continue
            # Never treat the global hooks directory as a legacy workspace: it
            # holds the file this installer just wrote, and kironomics.json is
            # a valid name in both places.
            try:
                if current.resolve() == GLOBAL_HOOKS_DIR.resolve():
                    continue
            except Exception:
                pass
            for filename in filenames:
                if filename in LEGACY_HOOK_NAMES:
                    found.append(current / filename)
            kiro_dir = current.parent
            for filename in LEGACY_SCRIPT_NAMES:
                candidate = kiro_dir / filename
                if candidate.is_file():
                    found.append(candidate)
            # The old setup ran py_compile, leaving orphaned bytecode behind
            # after the .py files go. Harmless but untidy, and it makes a
            # workspace look like it still has Kironomics in it.
            for candidate in (kiro_dir / "__pycache__").glob("kironomics_*.pyc"):
                if candidate.is_file():
                    found.append(candidate)
    return sorted(set(found))


def prune_legacy(paths, dry_run):
    for path in paths:
        if dry_run:
            print("  would remove %s" % path)
            continue
        try:
            path.unlink()
            print("  removed %s" % path)
        except Exception as exc:
            print("  could not remove %s (%s)" % (path, exc))


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------


def cmd_status():
    ide_version, source = detect_ide_version()
    cli_version = detect_cli_version()
    print("Kironomics status")
    print("  Kiro IDE      : %s%s" % (fmt(ide_version), " (%s)" % source if source else ""))
    print("  Kiro CLI      : %s" % fmt(cli_version))
    print("  global hooks  : %s" % ("present" if HOOK_FILE.is_file() else "NOT installed"))
    print("  scripts       : %s" % ("present" if (INSTALL_DIR / SCRIPTS[1]).is_file() else "NOT installed"))
    if CONFIG_FILE.is_file():
        try:
            config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            key = config.get("api_key", "")
            masked = (key[:6] + "..." + key[-4:]) if len(key) > 12 else "(set)"
            print("  api key       : %s" % masked)
            print("  api base      : %s" % config.get("api_base", DEFAULT_API_BASE))
        except Exception:
            print("  config        : unreadable")
    else:
        print("  config        : NOT installed")
    return 0


def cmd_uninstall():
    print("Removing Kironomics")
    for path in (HOOK_FILE, CONFIG_FILE, INSTALL_DIR / SCRIPTS[0], INSTALL_DIR / SCRIPTS[1]):
        try:
            path.unlink()
            print("  removed %s" % path)
        except FileNotFoundError:
            pass
        except Exception as exc:
            print("  could not remove %s (%s)" % (path, exc))
    shutil.rmtree(INSTALL_DIR / "__pycache__", ignore_errors=True)
    try:
        INSTALL_DIR.rmdir()
    except Exception:
        pass
    print("\nRestart Kiro. Tracking stops immediately.")
    return 0


def cmd_install(args):
    print("Installing Kironomics globally\n")

    print("Checking Kiro version")
    if not check_kiro_version(args.force):
        return 1

    if not args.api_key:
        print("\n--api-key is required. Get one from the Kironomics dashboard.")
        return 1

    print("\nInstalling scripts")
    install_scripts()
    write_config(args.api_key, args.api_base)

    print("\nWriting global hooks")
    python_exe = args.python or sys.executable
    write_hooks(python_exe)
    print("  interpreter: %s" % python_exe)

    print("\nVerifying")
    if not verify():
        return 1

    scan_roots = args.scan_root or [Path.cwd()]
    print("\nChecking for per-workspace installs to retire")
    legacy = find_legacy(scan_roots, args.max_depth)
    if not legacy:
        print("  none found")
    elif args.prune:
        prune_legacy(legacy, dry_run=False)
    else:
        print("  found %d file(s) that will now double-count:" % len(legacy))
        prune_legacy(legacy, dry_run=True)
        print("  re-run with --prune to remove them")

    print("\nDone. Restart Kiro once.")
    print("Every workspace you open from now on is tracked - no per-project setup.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Install Kironomics once, for every Kiro workspace."
    )
    parser.add_argument("--api-key", help="Kironomics API key from your dashboard.")
    parser.add_argument(
        "--api-base", default=DEFAULT_API_BASE, help="Backend base URL."
    )
    parser.add_argument(
        "--python", help="Interpreter to run the hooks with (default: this one)."
    )
    parser.add_argument(
        "--scan-root",
        action="append",
        help="Directory to scan for old per-workspace installs. Repeatable.",
    )
    parser.add_argument(
        "--max-depth", type=int, default=4, help="Scan depth for --scan-root."
    )
    parser.add_argument(
        "--prune", action="store_true", help="Delete the per-workspace files found."
    )
    parser.add_argument(
        "--force", action="store_true", help="Install even if the version check fails."
    )
    parser.add_argument("--status", action="store_true", help="Show current state.")
    parser.add_argument("--uninstall", action="store_true", help="Remove Kironomics.")
    args = parser.parse_args()

    if args.status:
        return cmd_status()
    if args.uninstall:
        return cmd_uninstall()
    return cmd_install(args)


if __name__ == "__main__":
    sys.exit(main())
