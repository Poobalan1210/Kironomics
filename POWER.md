---
name: "kironomics"
displayName: "Kironomics"
description: "Gamified Kiro IDE usage tracking with leaderboards, badges, streaks, plan tracking, and credit-based scoring. Track prompts, tool calls, and credit usage and compete with other developers. Installs once per machine via global hooks and tracks every workspace automatically."
keywords: ["kironomics", "leaderboard", "kiro-credits", "kiro-tracking", "kironomics-power", "global-hooks"]
author: "Logesh"
---

# Kironomics

## Overview

Kironomics is a gamified usage-tracking system for Kiro IDE inspired by Meta's "Claudinomics" internal leaderboard. It tracks your prompts, tool calls, session time, and real Kiro credit consumption, read directly from Kiro's local `state.vscdb`. Then it ranks you on the AWS User Group Madurai leaderboard with titles like "Kiro Novice", "Tool Wielder", and "Session Immortal".

**Kironomics installs once per machine.** The counter and reporter live in `~/.kiro/kironomics/`, and a single global hook file lives in `~/.kiro/hooks/kironomics.json`. Global hooks fire in *every* workspace, so every project opened afterwards, including projects that do not exist yet, is tracked with no further setup. Nothing is written into the workspace.

## Steering Files

Read the relevant file before acting. Do not answer from memory.

| Read this | When |
|---|---|
| `steering/kironomics-workflows.md` | Verifying an install, migrating from per-workspace, rotating the API key, self-hosting, uninstalling, or any installer flag question |
| `steering/kironomics-troubleshooting.md` | Tracking is not working, the score looks wrong, or the leaderboard is not updating |
| `steering/kironomics-scoring.md` | Questions about score, titles, badges, streaks, plan detection, or anti-cheat |
| `steering/kironomics-hook-reference.md` | How the hooks work internally, inspecting or hand-editing the hook file, 0.x migration details, or the per-workspace fallback |

First-time setup is below and does not require a steering file.

## Backend

Kironomics is hosted, so users do **not** run a backend themselves. The Power ships with the live endpoint baked in:

```
https://2q4zt5zl9e.execute-api.us-east-1.amazonaws.com/dev
```

All the reporter needs from the user is their personal **API key**.

## Requirements

| Requirement | Minimum | Why |
|---|---|---|
| **Kiro IDE** | **1.0.182** (Jul 20, 2026) | Added user-level global hooks (`~/.kiro/hooks/`) |
| *or* **Kiro CLI** | **2.13.0** (Jul 17, 2026) | Same feature on the CLI |
| Python 3 | 3.8+ | Runs the counter and reporter, standard library only |

This version floor is not optional. On anything older, a hook file placed in `~/.kiro/hooks/` is **never loaded**, so the install would look successful and silently track nothing. The installer checks the version and refuses rather than leaving a user sitting at zero on the leaderboard wondering why.

Hook format and trigger names also changed in IDE 1.0. The installer writes the current v1 format, so an upgrade plus one install replaces any legacy setup. See `steering/kironomics-hook-reference.md` for the mapping.

## Onboarding

When the user first activates this power, set up **global** tracking. Do not create anything inside the workspace.

### Step 1: Check the Kiro version

Run the status check first. It reports the detected version and what is already installed:

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py --status
```

On Windows use `python` instead of `python3`. If the power repo is not at that path, find it with `ls ~/.kiro/powers/repos/`.

If the reported IDE version is below `1.0.182` and the CLI is below `2.13.0`, **stop and tell the user to upgrade Kiro first**:

> "Kironomics now installs once for all your workspaces using Kiro's global hooks. That needs Kiro IDE 1.0.182 or newer, released Jul 20, 2026, and you're on `<detected version>`. Update via **Kiro menu > Check for Updates**, restart, and I'll finish the setup. If you'd rather not upgrade yet, I can fall back to the old per-workspace install, but you'd have to repeat it in every project."

Only continue once the version check passes, or the user explicitly asks for the per-workspace fallback documented in `steering/kironomics-hook-reference.md`.

### Step 2: Get the user's API key

Ask for it in conversation:

> "Paste your Kironomics API key. (Get it from https://www.awsugmdu.in/kironomics, 'Your API key', sign in, Generate.)"

Save the pasted value as `API_KEY`. No backend URL is needed, the hosted endpoint is built in. If the user is self-hosting, ask for an API base URL and pass it as `--api-base`.

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
3. Writes `~/.kiro/kironomics/config.json` with the API key, mode `600`.
4. Writes `~/.kiro/hooks/kironomics.json`, the three global hooks in v1 format, with absolute paths to the interpreter and scripts.
5. Syntax-checks the installed scripts.
6. Finds and removes leftover per-workspace Kironomics installs.

`--scan-root ~ --prune` is what retires an old setup. Adjust the root if the user keeps code elsewhere, for example `--scan-root /d/projects`, and repeat the flag for multiple roots. Without `--prune` the installer only lists what it would remove.

**Why pruning matters:** if old per-workspace hooks survive alongside the global ones, every tool call is counted twice in those projects, which inflates the score and can trip the backend's anti-cheat checks.

### Step 4: Confirm

Tell the user:

> "Kironomics is wired globally. Installed:
> - `~/.kiro/kironomics/` for the counter, reporter and your API key
> - `~/.kiro/hooks/kironomics.json` for the three global hooks
>
> Restart Kiro once so the hooks register. After that every workspace you open is tracked automatically, new projects included. You never run this setup again. Your stats appear at https://www.awsugmdu.in/kironomics."

## Your Data, Your Rules

What leaves the machine, per session: prompt count, tool-call count, session length in seconds, and four credit fields read from `state.vscdb`.

What never leaves: prompt text, Kiro's replies, source code, file names, paths, repo names, and anything the user types. The credit database is opened read-only and immutable, so Kironomics cannot modify Kiro's data. Uninstall any time with `--uninstall`.

## License, Privacy and Support

- **License:** MIT (SPDX identifier: `MIT`). Copyright (c) 2026 AWS User Group Madurai. Full text in `LICENSE` at the repository root.
- **Privacy policy:** https://www.awsugmdu.in/kironomics#privacy
- **Support:** https://github.com/Poobalan1210/Kironomics/issues

No MCP servers are used by this power, so no third-party server licenses or privacy policies apply.

---

**Stack**

- Backend: hosted on API Gateway and Lambda
- Frontend: React, Vite and Tailwind dashboard at https://www.awsugmdu.in/kironomics
- Reporter: Python 3 standard library only, no `pip install`
- Auth: AWS Cognito, in the dashboard
