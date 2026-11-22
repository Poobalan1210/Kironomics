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

The system uses one shared Python reporter per machine (`~/.kironomics/report.py`, published at https://www.awsugmdu.in/kiro/report.py) plus a Kiro hooks file in each workspace. Hooks silently count activity during each session; at the end, the reporter reads Kiro's own credit data from `state.vscdb` (including bonus credit pools) and sends one batched request to the Kironomics backend. Zero overhead during work.

Because every workspace runs the same shared reporter, fixes ship by updating that one file — see **Workflow: Updating Kironomics**.

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

### Step 3: Install the Shared Reporter

Download the reporter once per machine into `~/.kironomics/`. Run the command for the user's OS:

macOS / Linux:

```bash
curl -fsSL https://www.awsugmdu.in/kiro/report.py --create-dirs -o ~/.kironomics/report.py
```

Windows (PowerShell):

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.kironomics" | Out-Null
Invoke-WebRequest -UseBasicParsing https://www.awsugmdu.in/kiro/report.py -OutFile "$env:USERPROFILE\.kironomics\report.py"
```

Do **not** write your own reporter script or paste the API key into any file in the workspace. The reporter keeps the key in `~/.kironomics/token`, outside the project, so it is never committed.

### Step 4: Run Setup for This Workspace

From the workspace root (the directory that contains, or will contain, `.kiro/`), run setup with the user's key. Use `python3` on macOS/Linux and `python` on Windows:

```bash
python3 ~/.kironomics/report.py setup --key "API_KEY"
```

Setup stores the key, writes `.kiro/hooks/kironomics.json` with absolute paths to the Python interpreter and the reporter, and removes any old `.kiro/kironomics_report.py` from earlier versions of this Power. If the workspace has that old file, `--key` can be omitted: setup reuses the key from it.

Do not hand-write the hooks file. Setup generates it so the commands work on macOS, Linux and Windows.

### Step 5: Confirm Setup

Tell the user:

> "Kironomics setup complete:
> - Tracker installed at `~/.kironomics/report.py` (your key is stored next to it, outside this project)
> - `.kiro/hooks/kironomics.json` (3 hooks: tool counter, prompt counter, session reporter)
>
> Reload the Kiro window so the hooks register. Then just build normally — your stats appear on the leaderboard at https://www.awsugmdu.in/kironomics."

## How Tracking Works

Once setup is complete, tracking is fully passive and silent.

**During a session:**
- The `UserPromptSubmit` hook fires on every prompt the user submits. It runs `report.py count prompt`, which increments a counter in the OS temp directory and records the session start time on the first prompt.
- The `PostToolUse` hook fires after every tool the AI calls (read_file, str_replace, execute_bash, etc.). It runs `report.py count tool`.
- Both hooks are tiny and produce no chat output.

**When the agent finishes (`Stop`):**
- The session reporter hook runs `report.py send`.
- The reporter reads the temp counters, opens Kiro's `state.vscdb` in read-only mode, extracts `currentUsage`, `usageLimit`, `percentageUsed`, `resetDate` and active bonus credit pools, then POSTs everything with its version number to `{API_BASE}/kironomics/session`.
- If the backend reports a newer reporter, it prints a one-line update notice (at most once a day). It never updates itself.
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

The user activates the power and the agent runs Steps 3 to 5 of Onboarding. If `~/.kironomics/report.py` and `~/.kironomics/token` already exist on this machine, skip Step 3 and run setup without `--key`.

### Workflow: Updating Kironomics

When the user asks to "update Kironomics" (or the leaderboard site or a chat notice says their tracker is out of date):

1. If `~/.kironomics/report.py` exists, run:

   ```bash
   python3 ~/.kironomics/report.py update
   ```

   It downloads the latest published reporter, checks it, and replaces the installed one. Hooks keep working — they point at the same file.

2. If it does not exist, or the workspace still has `.kiro/kironomics_report.py` (installed by an older version of this Power), do Step 3 of Onboarding, then run `python3 ~/.kironomics/report.py setup` in the workspace. Setup reuses the key from the old file and removes it.

3. Ask the user to reload the Kiro window if setup ran.

### Workflow: Verifying Tracking Is Active

After setup and a reload, the user can check that hooks are firing:

```bash
python3 ~/.kironomics/report.py status
```

It shows the reporter version, whether the key is set, the current tool and prompt counters, and the credit reading.

### Workflow: Manually Triggering a Session Report

```bash
python3 ~/.kironomics/report.py send
```

This POSTs the current counters and credit reading, then clears the counters. Refresh the leaderboard to confirm.

### Workflow: Updating the API Key

If the user regenerates their API key, run setup again with the new key:

```bash
python3 ~/.kironomics/report.py setup --key "NEW_API_KEY"
```

## Troubleshooting

### Setup ran but hooks aren't firing

**Cause:** Kiro hasn't picked up the new hook file yet.

**Solution:** Restart Kiro (or reload the workspace). On next launch, Kiro scans `.kiro/hooks/` and registers the hooks automatically.

### Reporter script fails

**Cause:** Python 3 not on PATH.

**Solution:** Verify with `python3 --version`. On macOS, install via `brew install python3` if missing. The script uses only stdlib modules (sqlite3, urllib, json, pathlib), so no `pip install` is needed.

### Nothing shows on the leaderboard

**Cause:** Invalid API key, or the agent hasn't finished a turn yet.

**Solution:** Run `python3 ~/.kironomics/report.py status` and check the key is set; if in doubt, re-run setup with the key from https://www.awsugmdu.in/kironomics. Send a prompt, let the agent finish (the `Stop` hook fires), then refresh the leaderboard. You can also run `python3 ~/.kironomics/report.py send` manually to test.

### Plan shows "Auto-Auto" but I'm on Kiro Pro

**Cause:** Kiro's `state.vscdb` doesn't have `usageState` populated yet (happens occasionally on first install or after a Kiro update).

**Solution:** Use Kiro for one full session, then check again. Kiro syncs usage periodically, and the next session report will pick it up.

### I want to remove Kironomics from a workspace

**Solution:** Delete these files, then restart Kiro:

```bash
rm -f .kiro/hooks/kironomics.json
```

To remove it from the machine entirely, also delete `~/.kironomics/`.

## Best Practices

- **One machine, one reporter; one setup per workspace.** The reporter is shared; each workspace needs `setup` once to get its hooks file.
- **Never copy the reporter into the workspace.** Updates only reach `~/.kironomics/report.py`.
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

## Files Created

After running the onboarding:

```
~/.kironomics/
├── report.py               (shared reporter, one per machine)
└── token                   (your API key, outside every project)

<workspace>/.kiro/
└── hooks/
    └── kironomics.json     (3 hooks: PostToolUse, UserPromptSubmit, Stop)
```

To uninstall, delete the hooks file (and `~/.kironomics/` to remove it from the machine), then reload Kiro.

---

**Stack**

- Backend: AWS Lambda + DynamoDB behind API Gateway (hosted)
- Frontend: React + Vite leaderboard at awsugmdu.in/kironomics
- Reporter: Python 3 (built-in on macOS/Linux)
- Auth: AWS Cognito (for minting API keys on the site)
