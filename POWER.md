---
name: "kironomics"
displayName: "Kironomics"
description: "Gamified Kiro IDE usage tracking with leaderboards, badges, streaks, plan tracking, and credit-based scoring. Track prompts, tool calls, and credit usage and compete with other developers. Installs once per machine via global hooks and tracks every workspace automatically."
keywords: ["kironomics", "leaderboard", "kiro-credits", "kiro-tracking", "kironomics-power", "global-hooks"]
author: "Logesh"
---

# Kironomics

## Overview

Kironomics is a gamified usage-tracking system for Kiro IDE inspired by Meta's "Claudinomics" internal leaderboard. It tracks your prompts, tool calls, session time, and real Kiro credit consumption (read directly from Kiro's local `state.vscdb`). Then it ranks you on the AWS User Group Madurai leaderboard with titles like "Kiro Novice", "Tool Wielder", and "Session Immortal".

**Kironomics installs once per machine.** The counter and reporter live in `~/.kiro/kironomics/`, and a single global hook file lives in `~/.kiro/hooks/kironomics.json`. Global hooks fire in *every* workspace, so every project you open afterwards - including projects that do not exist yet - is tracked with no further setup. Nothing is written into your workspace.

## Backend

Kironomics is hosted - you do **not** run a backend yourself. The Power ships with the live endpoint baked in:

```
https://2q4zt5zl9e.execute-api.us-east-1.amazonaws.com/dev
```

All the reporter needs from you is your personal **API key**.

## Requirements

| Requirement | Minimum | Why |
|---|---|---|
| **Kiro IDE** | **1.0.182** (Jul 20, 2026) | Added user-level global hooks (`~/.kiro/hooks/`) |
| *or* **Kiro CLI** | **2.13.0** (Jul 17, 2026) | Same feature on the CLI |
| Python 3 | 3.8+ | Runs the counter and reporter (stdlib only) |

This version floor is not optional. On anything older, a hook file placed in `~/.kiro/hooks/` is **never loaded** - the install would look successful and silently track nothing. The installer checks the version and refuses rather than leaving a user sitting at zero on the leaderboard wondering why.

Two other things changed in IDE 1.0 that matter here:

- **Hook format changed.** 0.x used one `.kiro.hook` file per hook with `when`/`then` keys. 1.0 uses a structured v1 JSON document with a `hooks` array, `trigger`, and `action`. Legacy files show an upgrade badge in the Agent Hooks panel and do not execute until migrated.
- **Trigger names changed.** `promptSubmit` → `UserPromptSubmit`, `postToolUse` → `PostToolUse`, `agentStop` → `Stop`.

The installer writes the v1 format, so an upgrade plus one install replaces any legacy setup.

## Onboarding

When the user first activates this power, set up **global** tracking. Do not create anything inside the workspace.

### Step 1: Check the Kiro version

Run the installer's status check first. It reports the detected version and what is already installed:

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py --status
```

On Windows use `python` instead of `python3`.

If the reported IDE version is below `1.0.182` (and the CLI is below `2.13.0`), **stop and tell the user to upgrade Kiro first**:

> "Kironomics now installs once for all your workspaces using Kiro's global hooks. That needs Kiro IDE 1.0.182 or newer (released Jul 20, 2026) - you're on `<detected version>`. Update via **Kiro menu → Check for Updates**, restart, and I'll finish the setup. If you'd rather not upgrade yet, I can fall back to the old per-workspace install, but you'd have to repeat it in every project."

Only continue past this point once the version check passes, or the user explicitly asks for the per-workspace fallback below.

### Step 2: Get the user's API key

Ask the user for their API key in conversation:

> "Paste your Kironomics API key. (Get it from https://www.awsugmdu.in/kironomics → 'Your API key' → sign in → Generate.)"

Save the pasted value as `API_KEY`. No backend URL is needed - the hosted endpoint is built in. (Optional: if the user is self-hosting, ask for an API base URL and pass it as `--api-base`.)

### Step 3: Run the installer

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py \
  --api-key "<API_KEY>" \
  --scan-root ~ \
  --prune
```

This does everything in one pass:

1. Re-checks the Kiro version and refuses if it is too old.
2. Copies `kironomics_counter.py` and `kironomics_report.py` into `~/.kiro/kironomics/`.
3. Writes `~/.kiro/kironomics/config.json` with the API key (mode `600`).
4. Writes `~/.kiro/hooks/kironomics.json` - the three global hooks, in v1 format, with absolute paths to the interpreter and scripts.
5. Syntax-checks the installed scripts.
6. Finds and removes leftover per-workspace Kironomics installs.

`--scan-root ~ --prune` is what retires the old setup. Adjust the root if the user keeps code somewhere else (`--scan-root /d/projects`), and repeat the flag for multiple roots. Without `--prune` the installer only lists what it would remove.

**Why pruning matters:** if old per-workspace hooks survive alongside the global ones, every tool call is counted twice in those projects, which inflates the score and can trip the backend's anti-cheat checks.

If the power repo is not at the path above, find it with `ls ~/.kiro/powers/repos/`, or clone the repo and run `scripts/kironomics_install.py` from there.

### Step 4: Confirm

Tell the user:

> "Kironomics is wired globally. Installed:
> - `~/.kiro/kironomics/` - counter + reporter + your API key
> - `~/.kiro/hooks/kironomics.json` - three global hooks
>
> Restart Kiro once so the hooks register. After that every workspace you open is tracked automatically - new projects included. You never run this setup again. Your stats appear at https://www.awsugmdu.in/kironomics."

### Rotating the API key

Editing one file is enough - no hook changes, no reinstall:

```bash
python3 -c "import json,pathlib;p=pathlib.Path.home()/'.kiro/kironomics/config.json';c=json.loads(p.read_text());c['api_key']='<NEW_KEY>';p.write_text(json.dumps(c,indent=2))"
```

## Fallback: per-workspace install (Kiro older than 1.0.182)

Only use this if the user declines the upgrade. It has to be repeated in every workspace, which is exactly the problem the global install solves. Tell the user plainly that it is a stopgap and that upgrading removes the per-project work permanently.

Create `.kiro/kironomics_report.py` and `.kiro/hooks/kironomics.json` in the workspace, with the reporter's absolute path (`pwd`) baked into the `Stop` hook command. On a pre-1.0 Kiro you must also use the 0.x schema - one `.kiro.hook` file per hook, `when.type` of `promptSubmit` / `postToolUse` / `agentStop`, and `then.type` of `runCommand`.

## How Tracking Works

Tracking is fully passive and silent. The scripts print nothing and always exit `0`, so they never add noise to the agent's context and never block a tool call or a prompt.

**During a session:**
- The `UserPromptSubmit` hook increments the prompt counter and records session start on the first prompt.
- The `PostToolUse` hook (matcher `.*`) increments the tool counter after every tool the agent calls (read_file, str_replace, execute_bash, etc.).
- Counters are plain files in the OS temp directory, keyed by a hash of the workspace path. Because global hooks fire in every window, this keying is what keeps two open Kiro windows from pooling into one bogus session.
- A session whose counters are older than 24 hours is discarded, so a crashed window cannot inflate the next session.

**When the agent finishes (`Stop`):**
- The reporter reads the counters for *this* workspace, opens Kiro's `state.vscdb` read-only, extracts `currentUsage`, `usageLimit`, `percentageUsed`, and `resetDate`, and POSTs one batched request to `{api_base}/kironomics/session`.
- Sessions with no activity are skipped entirely - no empty requests.
- Counters are cleared afterwards, even if the request failed, so an outage cannot compound into one giant session.
- TLS is verified using certifi's CA bundle when available, falling back to the system default. If a machine has no working CA bundle or a corporate proxy presents a re-signed certificate, the reporter retries once unverified so the report still lands - the payload is only usage counts, over HTTPS.

**On the backend:**
- The API key (token) is validated.
- The plan is auto-detected from `usageLimit` (50 = Free, 1000 = Pro, 2000 = Pro+, 10000 = Power).
- `creditsConsumed = newUsage − previousUsage` is computed.
- A simple sanity check runs (no over-claiming, hooks match credit growth over time).
- User totals + score are updated and persisted, then reflected on the leaderboard.

## The Global Hook File

`~/.kiro/hooks/kironomics.json`, generated by the installer (paths shown for macOS/Linux):

```json
{
  "version": "v1",
  "hooks": [
    {
      "name": "Kironomics Tool Counter",
      "description": "Counts tool calls for the Kironomics leaderboard.",
      "trigger": "PostToolUse",
      "matcher": ".*",
      "action": {
        "type": "command",
        "command": "\"/usr/bin/python3\" \"/Users/you/.kiro/kironomics/kironomics_counter.py\" tool"
      },
      "timeout": 5,
      "enabled": true
    },
    {
      "name": "Kironomics Prompt Counter",
      "description": "Counts prompts and records session start time.",
      "trigger": "UserPromptSubmit",
      "action": {
        "type": "command",
        "command": "\"/usr/bin/python3\" \"/Users/you/.kiro/kironomics/kironomics_counter.py\" prompt"
      },
      "timeout": 5,
      "enabled": true
    },
    {
      "name": "Kironomics Session Reporter",
      "description": "Reports the finished session to the Kironomics backend.",
      "trigger": "Stop",
      "action": {
        "type": "command",
        "command": "\"/usr/bin/python3\" \"/Users/you/.kiro/kironomics/kironomics_report.py\""
      },
      "timeout": 15,
      "enabled": true
    }
  ]
}
```

Trigger names use the current Kiro hook format: `PostToolUse` (fires after each tool call), `UserPromptSubmit` (fires on each prompt), and `Stop` (fires when the agent finishes its turn). The `matcher` is a regex tested against the tool name (`.*` matches every tool) and only applies to `PostToolUse`.

Paths are absolute and point at the user's home directory, never at a workspace. That is the whole trick: a home path is stable for the life of the machine, so one hook file serves every project. Workspace hooks still take precedence over global ones if a project defines a hook with the same name.

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

`state.vscdb` is located per platform:

| Platform | Path |
|---|---|
| macOS | `~/Library/Application Support/Kiro/User/globalStorage/state.vscdb` |
| Windows | `%APPDATA%\Kiro\User\globalStorage\state.vscdb` |
| Linux | `~/.config/Kiro/User/globalStorage/state.vscdb` |

It is always opened `mode=ro&immutable=1`. Kironomics never writes to Kiro's database.

## Common Workflows

### Workflow: Setting up on a new machine

Run Steps 1 to 4 of Onboarding once. Every workspace on that machine is covered from then on.

### Workflow: "I started a new project - do I need to set this up?"

No. That is the point of the global install. Confirm with `--status` if the user wants reassurance.

### Workflow: Migrating from the old per-workspace setup

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py \
  --api-key "<API_KEY>" --scan-root ~ --prune
```

Run without `--prune` first if the user wants to review the list before anything is deleted. Only Kironomics-owned files are ever touched; other hooks in the same directory are left alone.

### Workflow: Verifying tracking is active

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py --status
```

Then, after a few prompts in a workspace, list the live counters:

```bash
python3 -c "import glob,os,tempfile;[print(os.path.basename(f),open(f).read()) for f in glob.glob(os.path.join(tempfile.gettempdir(),'kironomics_*'))]"
```

Counts should be climbing. They clear when the agent stops and the session reports. Refresh the leaderboard to confirm the session landed.

### Workflow: Manually triggering a session report

```bash
python3 ~/.kiro/kironomics/kironomics_report.py
```

Run it from the workspace you want to report, since counters are workspace-keyed.

### Workflow: Uninstalling

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py --uninstall
```

Removes the hooks, scripts, and stored key. Restart Kiro; tracking stops immediately.

## Troubleshooting

### Setup ran but nothing is tracked

**Cause:** Kiro is older than 1.0.182, so `~/.kiro/hooks/` is not read at all.

**Solution:** Run `--status` and check the reported version. Upgrade Kiro, restart, and re-run the installer.

### Hooks aren't firing right after install

**Cause:** Kiro scans hook files at startup.

**Solution:** Restart Kiro (or reload the window) once. The three Kironomics hooks then appear in the Agent Hooks panel.

### My score jumped unrealistically

**Cause:** Old per-workspace hooks are still present alongside the global ones, so tool calls are counted twice.

**Solution:** Re-run the installer with `--scan-root ~ --prune` and restart Kiro.

### Legacy hooks show an "upgrade" badge in the Agent Hooks panel

**Cause:** They are 0.x `.kiro.hook` files left over from a per-workspace install. They no longer execute in IDE 1.0.

**Solution:** Let the installer prune them. The global v1 hooks replace them.

### `python3: command not found` in the hook output

**Cause:** The interpreter recorded at install time is gone (common after removing a virtualenv).

**Solution:** Re-run the installer, optionally pinning a stable interpreter: `--python /usr/bin/python3`.

### Nothing shows on the leaderboard

**Cause:** Invalid API key, or the agent hasn't finished a turn yet.

**Solution:** Check the stored key with `--status` and confirm it matches the key from https://www.awsugmdu.in/kironomics. Send a prompt, let the agent finish (the `Stop` hook fires), then refresh the leaderboard. You can also run the reporter manually to test.

### Plan shows "Auto-Auto" but I'm on Kiro Pro

**Cause:** Kiro's `state.vscdb` doesn't have `usageState` populated yet (happens occasionally on first install or after a Kiro update).

**Solution:** Use Kiro for one full session, then check again. Kiro syncs usage periodically, and the next session report will pick it up.

### Two Kiro windows produced one merged session

**Cause:** Hooks ran with the same working directory for both windows, so the workspace key collapsed.

**Solution:** Expected degradation, not data loss - totals stay correct.

## Files Installed

```
~/.kiro/
├── kironomics/
│   ├── kironomics_counter.py   (PostToolUse + UserPromptSubmit)
│   ├── kironomics_report.py    (Stop)
│   └── config.json             (API key + backend URL, mode 600)
└── hooks/
    └── kironomics.json         (all three global hooks, v1 format)
```

Nothing is written into any workspace.

## API Endpoints Reference

Exactly one endpoint is called from your machine. Listed here for transparency.

| Method | Path | Purpose |
|---|---|---|
| POST | `{api_base}/kironomics/session` | Sends batched session data (called by the reporter on `Stop`) |

`api_base` defaults to the hosted endpoint and is stored in `~/.kiro/kironomics/config.json`. Point it at your own deployment by passing `--api-base` to the installer.

Every other endpoint (leaderboard, metrics, heatmap, badges, profile) is called by the dashboard in your browser, never by the hooks.

## Your Data, Your Rules

What leaves your machine, per session: prompt count, tool-call count, session length in seconds, and the four credit fields read from `state.vscdb`.

What never leaves: prompt text, Kiro's replies, source code, file names, paths, repo names, and anything you type. The credit database is opened read-only and immutable, so Kironomics cannot modify Kiro's data. Uninstall any time with `--uninstall`.

---

**Stack**

- Backend: hosted on API Gateway + Lambda
- Frontend: React + Vite + Tailwind dashboard at https://www.awsugmdu.in/kironomics
- Reporter: Python 3 standard library only - no `pip install`
- Auth: AWS Cognito (in dashboard)
