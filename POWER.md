---
name: "kironomics"
displayName: "Kironomics"
description: "Gamified Kiro IDE usage tracking with leaderboards, badges, streaks, plan tracking, and credit-based scoring. Track prompts, tool calls, and credit usage and compete with other developers."
keywords: ["kironomics", "leaderboard", "kiro-credits", "kiro-tracking", "kironomics-power"]
author: "Logesh"
---

# Kironomics

## Overview

Kironomics is a gamified usage-tracking system for Kiro IDE inspired by Meta's "Claudinomics" internal leaderboard. It tracks your prompts, tool calls, session time, and real Kiro credit consumption (read directly from Kiro's local `state.vscdb`). Then it ranks you on the AWS User Group Madurai leaderboard with titles like "Kiro Novice", "Tool Wielder", and "Session Immortal".

The system uses a single Kiro hooks file (three hooks) plus one Python reporter script. Hooks silently count activity during each session; at the end, the Python script reads Kiro's own credit data from `state.vscdb` and sends one batched request to the Kironomics backend. Zero overhead during work.

## Backend

Kironomics is hosted — you do **not** run a backend yourself. The Power ships with the live endpoint baked in:

```
https://2q4zt5zl9e.execute-api.us-east-1.amazonaws.com/dev
```

All the reporter needs from you is your personal **API key**.

## Onboarding

When the user first activates this power, run through these onboarding steps to set up tracking in their workspace.

### Step 1: Validate Prerequisites

- **Python 3** is installed (built-in on macOS/Linux). Verify with: `python3 --version`
- The user has a Kironomics **API key**. If they don't have one yet, point them to the leaderboard site, open **https://www.awsugmdu.in/kironomics**, scroll to **"Your API key"**, sign in, click **Generate my API key**, and copy it.

### Step 2: Get the User's API Key

Ask the user for their API key in conversation:

> "Paste your Kironomics API key. (Get it from https://www.awsugmdu.in/kironomics → 'Your API key' → sign in → Generate.)"

Save the pasted value as `API_KEY` for the next step. (Optional: if the user is self-hosting the backend, also ask for an API base URL and save it as `API_BASE`; otherwise use the default endpoint above.)

### Step 3: Create the Reporter Script

Create the file `.kiro/kironomics_report.py` in the workspace with this exact content. Replace `__API_KEY__` with the user's API key. Leave `API_BASE` as the default unless the user provided their own.

```python
#!/usr/bin/env python3
"""Kironomics session reporter - reads Kiro's state.vscdb and sends to the backend."""
import os, sys, ssl, json, sqlite3, urllib.request, urllib.error, time
from pathlib import Path

API_KEY = "__API_KEY__"
API_BASE = "https://2q4zt5zl9e.execute-api.us-east-1.amazonaws.com/dev"

def read_int(path, default=0):
    try:
        return int(Path(path).read_text().strip())
    except Exception:
        return default

tools = read_int("/tmp/kironomics_tools")
prompts = read_int("/tmp/kironomics_prompts")
start = read_int("/tmp/kironomics_start", int(time.time()))
elapsed = max(0, int(time.time()) - start)

# Read Kiro's state.vscdb (silent fail if missing or no usageState)
plan_data = {}
try:
    home = Path.home()
    if sys.platform == "darwin":
        db = home / "Library/Application Support/Kiro/User/globalStorage/state.vscdb"
    elif sys.platform.startswith("win"):
        db = Path(os.environ.get("APPDATA", str(home / "AppData/Roaming"))) / "Kiro/User/globalStorage/state.vscdb"
    else:
        db = home / ".config/Kiro/User/globalStorage/state.vscdb"
    if db.exists():
        conn = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
        row = conn.execute(
            "SELECT value FROM ItemTable WHERE key=?",
            ("kiro.kiroAgent",),
        ).fetchone()
        conn.close()
        if row:
            state = json.loads(row[0])
            usage = state.get("kiro.resourceNotifications.usageState", {})
            breakdowns = usage.get("usageBreakdowns", [])
            if breakdowns:
                bd = breakdowns[0]
                plan_data = {
                    "currentUsage": bd.get("currentUsage"),
                    "usageLimit": bd.get("usageLimit"),
                    "percentageUsed": bd.get("percentageUsed"),
                    "resetDate": bd.get("resetDate"),
                }
except Exception:
    pass

payload = {
    "token": API_KEY,
    "tool_calls": tools,
    "prompts": prompts,
    "elapsed_seconds": elapsed,
    **plan_data,
}

# Build a verified TLS context. Prefer certifi's CA bundle (some Python builds —
# e.g. the python.org macOS build — ship without a usable default CA bundle, which
# makes urllib raise CERTIFICATE_VERIFY_FAILED), then fall back to the default.
def _ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        try:
            return ssl.create_default_context()
        except Exception:
            return None

# POST to the hosted backend. Verified TLS by default; if this machine has no
# working CA bundle (cert verify fails), retry once unverified so the report
# still lands — the payload is only usage counts, sent over HTTPS.
try:
    req = urllib.request.Request(
        f"{API_BASE}/kironomics/session",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=5, context=_ssl_context()).read()
    except (ssl.SSLError, urllib.error.URLError) as e:
        if "certificate verify failed" in str(e).lower():
            urllib.request.urlopen(req, timeout=5, context=ssl._create_unverified_context()).read()
        else:
            raise
except Exception:
    pass

# Cleanup temp counters
for f in ("/tmp/kironomics_tools", "/tmp/kironomics_prompts", "/tmp/kironomics_start"):
    try:
        os.remove(f)
    except Exception:
        pass
```

After creating the file, verify it compiles:

```bash
python3 -m py_compile .kiro/kironomics_report.py && echo "Reporter script OK"
```

### Step 4: Create the Hooks File

Kiro uses a single versioned hook file with all hooks in one `hooks` array. Create the file `.kiro/hooks/kironomics.json`. Replace `__WORKSPACE_ROOT__` with the absolute path to the user's current workspace directory (the directory containing `.kiro/`). Find it with `pwd` from the agent's working directory and use the absolute path so the reporter runs regardless of which subfolder the agent is in.

```json
{
  "version": "v1",
  "hooks": [
    {
      "name": "Kironomics Tool Counter",
      "trigger": "PostToolUse",
      "matcher": ".*",
      "description": "Silently counts tool calls for the Kironomics leaderboard.",
      "action": {
        "type": "command",
        "command": "bash -c 'FILE=/tmp/kironomics_tools; COUNT=$(cat \"$FILE\" 2>/dev/null || echo 0); echo $((COUNT + 1)) > \"$FILE\"; echo ok'",
        "timeout": 2
      }
    },
    {
      "name": "Kironomics Prompt Counter",
      "trigger": "UserPromptSubmit",
      "description": "Silently counts prompts and records session start time.",
      "action": {
        "type": "command",
        "command": "bash -c 'START=/tmp/kironomics_start; PFILE=/tmp/kironomics_prompts; test -f \"$START\" || date +%s > \"$START\"; COUNT=$(cat \"$PFILE\" 2>/dev/null || echo 0); echo $((COUNT + 1)) > \"$PFILE\"; echo ok'",
        "timeout": 2
      }
    },
    {
      "name": "Kironomics Session Reporter",
      "trigger": "Stop",
      "description": "Reads Kiro's credit usage and sends session data to the backend when the agent finishes.",
      "action": {
        "type": "command",
        "command": "python3 \"__WORKSPACE_ROOT__/.kiro/kironomics_report.py\" 2>/dev/null; echo ok",
        "timeout": 10
      }
    }
  ]
}
```

Trigger names use the current Kiro hook format: `PostToolUse` (fires after each tool call), `UserPromptSubmit` (fires on each prompt), and `Stop` (fires when the agent finishes its turn). The `matcher` is a regex tested against the tool name (`.*` matches every tool) and only applies to `PostToolUse`.

### Step 5: Confirm Setup

Tell the user:

> "Kironomics setup complete. Created:
> - `.kiro/kironomics_report.py`
> - `.kiro/hooks/kironomics.json` (3 hooks: tool counter, prompt counter, session reporter)
>
> Restart Kiro (or reload the window) so the hooks register. Then just build normally — your stats appear on the leaderboard at https://www.awsugmdu.in/kironomics."

## How Tracking Works

Once setup is complete, tracking is fully passive and silent.

**During a session:**
- The `UserPromptSubmit` hook fires on every prompt the user submits. It increments `/tmp/kironomics_prompts` and records the session start time on the first prompt.
- The `PostToolUse` hook fires after every tool the AI calls (read_file, str_replace, execute_bash, etc.). It increments `/tmp/kironomics_tools`.
- Both hooks run in under 2ms and produce no chat output.

**When the agent finishes (`Stop`):**
- The session reporter hook runs `python3 .kiro/kironomics_report.py`.
- The script reads the temp counters, opens Kiro's `state.vscdb` in read-only mode, extracts `currentUsage`, `usageLimit`, `percentageUsed`, and `resetDate`, then POSTs everything to `{API_BASE}/kironomics/session`.
- After sending, the script deletes the temp counters so the next session starts fresh.

**On the backend:**
- The API key (token) is validated.
- The plan is auto-detected from `usageLimit` (50 = Free, 1000 = Pro, 2000 = Pro+, 10000 = Power).
- `creditsConsumed = newUsage − previousUsage` is computed.
- A simple sanity check runs (no over-claiming, hooks match credit growth over time).
- User totals + score are updated and persisted, then reflected on the leaderboard.

## Score Formula

Primary (credit-based, tamper-proof):

```
score = (credits_consumed × 100) + (tool_calls × 1) + (prompts × 2)
```

Fallback (for users without credit data yet, e.g., on Auto-Auto plan):

```
score = (tool_calls × 3) + (prompts × 5) + (elapsed_minutes)
```

## Title Tiers

| Title | Score Range | Icon |
|---|---|---|
| Kiro Novice | 0 to 99 | 🌱 |
| Prompt Apprentice | 100 to 499 | 📝 |
| Hook Wrangler | 500 to 1,999 | 🪝 |
| Tool Wielder | 2,000 to 4,999 | 🔧 |
| Session Warrior | 5,000 to 14,999 | ⚔️ |
| Token Legend | 15,000 to 49,999 | 👑 |
| Session Immortal | 50,000+ | 🏆 |

## Badges

| Badge | Criteria | Icon |
|---|---|---|
| First Session | 1 session completed | 🎯 |
| Century Club | 100 tool calls | 💯 |
| Hook Hero | 50 prompts | 🦸 |
| Token Titan | 500 tool calls | 💎 |
| Marathon Runner | 10+ hours total | 🏃 |
| Week Warrior | 7-day streak | 🔥 |
| Monthly Master | 30-day streak | 🌟 |

## Plan Detection

Kiro plans are auto-detected from `usageLimit` in `state.vscdb`:

| Plan | Limit | Price |
|---|---|---|
| Kiro Free | 50 credits/mo | $0 |
| Kiro Pro | 1,000 credits/mo | $20/mo |
| Kiro Pro+ | 2,000 credits/mo | $40/mo |
| Kiro Power | 10,000 credits/mo | $200/mo |
| Auto-Auto | (no usageState) | not detected |

Auto-Auto users skip credit tracking but still earn hook-based scores.

## Common Workflows

### Workflow: Setting Up in a New Workspace

The user activates the power, pastes their API key, and the agent runs through Steps 3 to 5 of Onboarding to create the two files. No backend URL needed — the hosted endpoint is built in.

### Workflow: Verifying Tracking Is Active

After setup and a Kiro restart, the user can verify hooks are firing during work:

```bash
cat /tmp/kironomics_prompts
cat /tmp/kironomics_tools
cat /tmp/kironomics_start
```

These should show increasing counts and a Unix timestamp.

### Workflow: Manually Triggering a Session Report

To test the full flow without waiting for the agent to stop:

```bash
python3 .kiro/kironomics_report.py
```

This reads the current counters, reads `state.vscdb`, POSTs to the backend, and clears the temp files. Refresh the leaderboard to confirm.

### Workflow: Updating the API Key

If the user regenerates their API key, edit `.kiro/kironomics_report.py` and change the `API_KEY` constant. Or re-run onboarding to recreate the files.

## Troubleshooting

### Setup ran but hooks aren't firing

**Cause:** Kiro hasn't picked up the new hook file yet.

**Solution:** Restart Kiro (or reload the workspace). On next launch, Kiro scans `.kiro/hooks/` and registers the hooks automatically.

### Reporter script fails

**Cause:** Python 3 not on PATH.

**Solution:** Verify with `python3 --version`. On macOS, install via `brew install python3` if missing. The script uses only stdlib modules (sqlite3, urllib, json, pathlib), so no `pip install` is needed.

### Nothing shows on the leaderboard

**Cause:** Invalid API key, or the agent hasn't finished a turn yet.

**Solution:** Confirm `API_KEY` in `.kiro/kironomics_report.py` matches the key from https://www.awsugmdu.in/kironomics. Send a prompt, let the agent finish (the `Stop` hook fires), then refresh the leaderboard. You can also run `python3 .kiro/kironomics_report.py` manually to test.

### Plan shows "Auto-Auto" but I'm on Kiro Pro

**Cause:** Kiro's `state.vscdb` doesn't have `usageState` populated yet (happens occasionally on first install or after a Kiro update).

**Solution:** Use Kiro for one full session, then check again. Kiro syncs usage periodically, and the next session report will pick it up.

### I want to remove Kironomics from a workspace

**Solution:** Delete these files, then restart Kiro:

```bash
rm -f .kiro/kironomics_report.py
rm -f .kiro/hooks/kironomics.json
```

## Best Practices

- **One workspace, one setup.** Run onboarding once per workspace.
- **Keep the reporter script absolute-pathed in the hook.** This avoids issues when Kiro runs the hook from a different working directory.
- **Don't edit `state.vscdb` manually.** It's Kiro's internal database. Editing it can corrupt your IDE and trigger anti-cheat flags.
- **Use the same API key across machines.** This consolidates your stats under one user.

## API Endpoints Reference

The reporter and leaderboard use these backend endpoints (base: `https://2q4zt5zl9e.execute-api.us-east-1.amazonaws.com/dev`).

| Method | Path | Purpose |
|---|---|---|
| POST | `/kironomics/session` | Sends batched session data (called by reporter) |
| GET | `/kironomics/leaderboard?window=daily\|weekly\|all-time` | Ranked leaderboard |
| GET | `/kironomics/users/:id/metrics` | Personal metrics (plan, credits, burn rate) |
| GET | `/kironomics/users/:id/heatmap` | 365-day activity heatmap |
| GET | `/kironomics/users/:id/sessions` | Recent sessions |
| GET | `/kironomics/users/:id/badges` | Earned badges |
| POST | `/kironomics/users/profile` | Mint/return the caller's API key (used by the website, Cognito-authenticated) |
| GET | `/kironomics/health` | Health check |

## Files Created in Workspace

After running the onboarding, the workspace contains:

```
.kiro/
├── kironomics_report.py    (Python session reporter)
└── hooks/
    └── kironomics.json     (3 hooks: PostToolUse, UserPromptSubmit, Stop)
```

To uninstall, delete those files and restart Kiro.

---

**Stack**

- Backend: AWS Lambda + DynamoDB behind API Gateway (hosted)
- Frontend: React + Vite leaderboard at awsugmdu.in/kironomics
- Reporter: Python 3 (built-in on macOS/Linux)
- Auth: AWS Cognito (for minting API keys on the site)
