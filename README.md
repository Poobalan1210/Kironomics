<div align="center">

# 🏆 Kironomics

### *Turn your Kiro grind into glory.*

**A gamified leaderboard for Kiro IDE users — track your prompts, tool calls, credits, and session time. Climb the ranks. Earn badges. Roast your friends.**

[![Made for Kiro](https://img.shields.io/badge/Made%20for-Kiro-8b5cf6?style=for-the-badge)](https://kiro.dev)
[![Knowledge Base Power](https://img.shields.io/badge/Type-Knowledge%20Base%20Power-green?style=for-the-badge)](https://kiro.dev/docs/powers/create/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](#)

</div>

---

## 🎯 What is this?

You and your team write code with Kiro. You ship features. You crush bugs. But nobody knows who's actually pulling their weight in the AI revolution.

**Kironomics fixes that.**

It's a private leaderboard that quietly tracks how much you actually use Kiro — the prompts you fire off, the tools the AI calls, the credits you burn through, the sessions that go past midnight. Then it ranks everyone, hands out badges, and shows who's the real **Session Immortal** of the team.

Think Strava for AI coding. Or GitHub contributions, but spicier.

---

## 🎮 Why you'll love it

| | |
|---|---|
| 🥇 **Compete with friends** | Daily, weekly, all-time leaderboards |
| 🏅 **Earn 7 badges** | First Session, Century Club, Marathon Runner, and more |
| 👑 **Unlock 7 titles** | Climb from "Kiro Novice" 🌱 to "Session Immortal" 🏆 |
| 🔥 **Streak tracking** | GitHub-style heatmap of your last 365 days |
| 💳 **Real credit tracking** | See your Kiro plan usage live (Free/Pro/Pro+/Power) |
| 📊 **Burn rate analytics** | "You'll run out of credits in 9 days at this pace" |
| 🛡️ **Anti-cheat verified** | Reads your actual AWS-synced credit data |
| 🤫 **Zero overhead** | Everything batches at session end |
| 🌍 **Set up once, ever** | Global hooks track every workspace, new projects included |

---

## ✅ Requirements

| | Minimum | Why |
|---|---|---|
| **Kiro IDE** | **1.0.182** (Jul 20, 2026) | Added user-level global hooks (`~/.kiro/hooks/`) |
| *or* **Kiro CLI** | **2.13.0** (Jul 17, 2026) | Same feature on the CLI |
| **Python 3** | 3.8+ | Runs the counter + reporter (stdlib only) |

> **On an older Kiro?** Hook files in `~/.kiro/hooks/` are simply never loaded, so the install would look fine and track nothing. The installer detects this and tells you to upgrade instead of leaving you with a dead setup. Update via **Kiro menu → Check for Updates**.

---

## ⚡ Quick Start (2 minutes, once per machine)

### Step 1 — Install the Power

In Kiro, open the **Powers panel** (left sidebar) and click **+ Add Custom Power**.

**Option A — From GitHub (recommended):**
```
https://github.com/Poobalan1210/Kironomics
```

**Option B — From local folder:**
Point to the path of this repo on your machine.

### Step 2 — Get your API key

Open the leaderboard site → **https://www.awsugmdu.in/kironomics** → scroll to **"Your API key"** → sign in → click **Generate my API key** → copy it.

### Step 3 — Activate the power

In Kiro chat, just say:

> "Set up Kironomics"

Kiro reads POWER.md, checks your Kiro version, asks for your API key, and runs the installer. Everything lands in your home directory. **Nothing is written into your project.**

Prefer doing it yourself? Run the installer directly:

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py \
  --api-key "<YOUR_KEY>" --scan-root ~ --prune
```

*(Windows: use `python` instead of `python3`.)*

### Step 4 — Restart Kiro once

Kiro scans hook files at startup. After this restart, tracking is live.

### Step 5 — Use Kiro normally, in any project

Every workspace on this machine is now tracked automatically, including projects you haven't created yet. **You never run setup again.**

Check state any time:

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py --status
```

### Step 6 — Check your rank

Open the dashboard whenever you want. Watch yourself climb.

---

## 🌍 One setup, every workspace

Kironomics used to be installed per project: files in every repo's `.kiro/`, with that repo's absolute path baked into the `Stop` hook, re-done by hand each time you started something new. Kiro IDE **1.0.182** fixed that by adding user-level global hooks.

Kironomics now installs **once per machine**:

```
~/.kiro/
├── kironomics/
│   ├── kironomics_counter.py   ← PostToolUse + UserPromptSubmit
│   ├── kironomics_report.py    ← Stop
│   └── config.json             ← your API key (mode 600)
└── hooks/
    └── kironomics.json         ← all three hooks, v1 format
```

The trick is that every path in the hook file points at your **home directory** instead of a workspace. A home path is stable for the life of the machine, so one hook file serves every project you'll ever open.

**Already had the old per-workspace setup?** Pass `--scan-root ~ --prune` and the installer retires it for you. This matters: leaving the old hooks in place alongside the global ones **double-counts every tool call**, which inflates your score and can trip the backend's anti-cheat checks. Other hooks in the same folder are never touched.

**Coming from Kiro 0.x?** Hooks changed format in IDE 1.0. The old one-file-per-hook `.kiro.hook` schema was replaced by a structured v1 JSON document, and triggers were renamed (`promptSubmit` → `UserPromptSubmit`, `postToolUse` → `PostToolUse`, `agentStop` → `Stop`). Legacy files show an upgrade badge in the Agent Hooks panel and stop executing. Upgrading and running the installer replaces them in one step.

---

## 🏗️ How it actually works

This is a **Knowledge Base Power**. When you activate it, Kiro reads POWER.md and runs `scripts/kironomics_install.py`, which writes three global hooks plus two scripts into your home directory:

```
~/.kiro/
├── kironomics/
│   ├── kironomics_counter.py   (increments the counters)
│   ├── kironomics_report.py    (reads credits, sends the session)
│   └── config.json             (API key + backend URL)
└── hooks/
    └── kironomics.json         (PostToolUse + UserPromptSubmit + Stop)
```

Then on every session, in every workspace:

```
┌────────────────────────────────────────────────────────────────────┐
│                          YOUR LAPTOP                                │
│                                                                     │
│   ┌──────────────┐    auto-writes    ┌────────────────────────┐    │
│   │  Kiro IDE    │ ─────────────────►│ state.vscdb            │    │
│   │              │                   │ └─ kiro.kiroAgent      │    │
│   │              │                   │     └─ usageState      │    │
│   └──────────────┘                   │         ├─ currentUsage│    │
│         │                            │         ├─ usageLimit  │    │
│         │                            │         └─ resetDate   │    │
│         ▼                            └────────────────────────┘    │
│   ┌────────────────────────────────────────┴────────────────┐      │
│   │   3 Global Hooks  (~/.kiro/hooks/kironomics.json)        │      │
│   │   fire in EVERY workspace, no per-project setup          │      │
│   │                                                          │      │
│   │   1️⃣ PostToolUse      → <tmp>/kironomics_<ws>_tools     │      │
│   │   2️⃣ UserPromptSubmit → <tmp>/kironomics_<ws>_prompts   │      │
│   │   3️⃣ Stop → runs the reporter:                          │      │
│   │       • reads this workspace's counters                  │      │
│   │       • reads state.vscdb credit data (read-only)        │      │
│   │       • POSTs once, then clears the counters             │      │
│   │                                                          │      │
│   │   <ws> = hash of the workspace path, so two open Kiro    │      │
│   │   windows never pool into one bogus session.             │      │
│   └─────────────────────────────────────────────────────────┘      │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS POST (1 request per session)
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│   📊 KIRONOMICS BACKEND                                           │
│   • Validates token                                                │
│   • Detects plan (Free / Pro / Pro+ / Power)                       │
│   • Calculates score                                               │
│   • Updates leaderboard                                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🎖️ Title Tiers

| Title | Score Range | Icon |
|---|---|---|
| Kiro Novice | 0 – 99 | 🌱 |
| Prompt Apprentice | 100 – 499 | 📝 |
| Hook Wrangler | 500 – 1,999 | 🪝 |
| Tool Wielder | 2,000 – 4,999 | 🔧 |
| Session Warrior | 5,000 – 14,999 | ⚔️ |
| Token Legend | 15,000 – 49,999 | 👑 |
| **Session Immortal** | **50,000+** | **🏆** |

**Score formula** (credit-based, the cheat-proof one):

```
score = (credits_consumed × 100) + (tool_calls × 1) + (prompts × 2)
```

Fallback for users without credit data yet:

```
score = (tool_calls × 3) + (prompts × 5) + (elapsed_minutes)
```

---

## 🏅 Badges

| Badge | Criteria | Icon |
|---|---|---|
| First Session | 1 session completed | 🎯 |
| Century Club | 100 tool calls | 💯 |
| Hook Hero | 50 prompts | 🦸 |
| Token Titan | 500 tool calls | 💎 |
| Marathon Runner | 10+ hours total | 🏃 |
| Week Warrior | 7-day streak | 🔥 |
| Monthly Master | 30-day streak | 🌟 |

---

## 💳 Real Credit Tracking

Kironomics reads your **actual Kiro usage** straight from Kiro's local database (`state.vscdb`) — the same data Kiro shows in its own UI.

That means:

- 📊 **Live credit balance** — see how many credits you've burned this month
- 📈 **Burn rate** — "73 credits/day at current pace"
- ⏰ **Days remaining** — "9 days until your monthly reset"
- 🎯 **Plan auto-detected** — Free, Pro, Pro+, Power, Auto-Auto
- 🛡️ **Tamper-proof** — you can't fake AWS billing data

Personal Metrics card preview:

```
┌────────────────────────────────────────────────────┐
│ 📊 Plan & Credits          Kiro Pro+    $40/mo     │
│ Live data from Kiro IDE                            │
│                                                     │
│ 1,246.79 / 2,000 credits             62.3%         │
│ ████████████░░░░░░░░                                │
│                                                     │
│ ┌────────┬──────────┬──────────┬──────────────┐    │
│ │ 753    │ 17 days  │ 73/day   │ 9 days       │    │
│ │ Remain │ Resets in│ Burn rate│ Will run out │    │
│ └────────┴──────────┴──────────┴──────────────┘    │
└────────────────────────────────────────────────────┘
```

---

## 🛡️ Anti-Cheat (it's smarter than you think)

The credit data comes from Kiro's own SQLite database, server-synced from AWS. Cheating attempts:

1. **Fake hook counters?** → Backend cross-references with `state.vscdb` credit deltas. Caught.
2. **Hooks claim 1000 events but credits show 0?** → Sanity check fails after 3 zero-credit sessions. Flagged.
3. **Credits-to-events ratio over 50x?** → Impossible even on heavy Opus. Flagged.
4. **Optional AWS Cost Explorer verification** → Cross-reference with actual AWS billing for ✅ Verified badge.

Cheaters get hidden from the leaderboard. The honest crew rules.

---

## 🤔 FAQ

<details>
<summary><b>Q: Will this slow down Kiro?</b></summary><br>

No. The 3 hooks fire in <2ms each (just incrementing a number in a temp file). The actual data send happens **once** when the agent stops — not during your work.
</details>

<details>
<summary><b>Q: What does it actually track?</b></summary><br>

- Number of prompts you submit
- Number of tools the AI calls (read_file, str_replace, execute_bash, etc.)
- Session duration
- Credits consumed (real, from Kiro's own data)
- Your plan (Free / Pro / Pro+ / Power)

Nothing about *what* you typed or what the code looked like. Just counts.
</details>

<details>
<summary><b>Q: Where does the credit data come from?</b></summary><br>

From `state.vscdb`, Kiro's own SQLite database:

| Platform | Path |
|---|---|
| macOS | `~/Library/Application Support/Kiro/User/globalStorage/state.vscdb` |
| Windows | `%APPDATA%\Kiro\User\globalStorage\state.vscdb` |
| Linux | `~/.config/Kiro/User/globalStorage/state.vscdb` |

We open it `mode=ro&immutable=1`, read-only and immutable, so Kiro IDE is never affected.
</details>

<details>
<summary><b>Q: I started a new project. Do I set this up again?</b></summary><br>

No. That's the whole point of the global install. The hooks live in `~/.kiro/hooks/` and fire in every workspace you open, including ones that don't exist yet.
</details>

<details>
<summary><b>Q: I'm on an older Kiro. What happens?</b></summary><br>

The installer refuses and tells you to upgrade. Global hooks landed in **IDE 1.0.182** (Jul 20, 2026) and **CLI 2.13.0** (Jul 17, 2026). Before that, `~/.kiro/hooks/` isn't read at all, so an install would silently track nothing. Better to be told than to sit at zero on the leaderboard wondering why.
</details>

<details>
<summary><b>Q: Does this work on Windows?</b></summary><br>

Yes. The counter and reporter resolve the temp directory and the `state.vscdb` location per platform, and the installer records absolute interpreter and script paths, so there's no dependency on `bash`, `/tmp`, or `python3` being on `PATH`.
</details>

<details>
<summary><b>Q: I'm on the Free plan. Will I see plan info?</b></summary><br>

Yes — Kironomics auto-detects all plans (50 credits = Free, 1000 = Pro, 2000 = Pro+, 10000 = Power). Auto-Auto users skip credit tracking.
</details>

<details>
<summary><b>Q: Do I need to share AWS credentials?</b></summary><br>

No. Credit data is read locally from your machine. AWS Cost Explorer verification is **optional** and only used for the ✅ AWS Verified badge.
</details>

<details>
<summary><b>Q: Can I uninstall it?</b></summary><br>

One command:

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py --uninstall
```

That removes the hooks, both scripts, and your stored key. Restart Kiro and tracking stops immediately.
</details>

<details>
<summary><b>Q: How do I rotate my API key?</b></summary><br>

Edit `~/.kiro/kironomics/config.json`. The key lives there, not in the hooks, so nothing else changes. Or re-run the installer with the new `--api-key`.
</details>

<details>
<summary><b>Q: Why no MCP server?</b></summary><br>

This is a Knowledge Base Power following Kiro's official pattern. POWER.md tells the Kiro agent exactly what to run, and Kiro does it. Simpler, more reliable, and there's no server process to keep alive.
</details>

---

## 📁 What's in this repo

```
.
├── POWER.md                        ← Power manifest + onboarding (Kiro reads this on activation)
├── LICENSE                         ← MIT
├── README.md                       ← This file (for GitHub viewers)
├── steering/                       ← Loaded on demand, keeps POWER.md small
│   ├── kironomics-workflows.md         (verify, migrate, rotate key, uninstall)
│   ├── kironomics-troubleshooting.md   (nothing tracked, score wrong, etc.)
│   ├── kironomics-scoring.md           (score, titles, badges, plans, anti-cheat)
│   └── kironomics-hook-reference.md    (hook internals, 0.x migration, fallback)
└── scripts/
    ├── kironomics_install.py       ← One-shot installer (version gate, migration, uninstall)
    ├── kironomics_counter.py       ← Increments per-workspace counters
    └── kironomics_report.py        ← Reads credits, sends the session
```

No MCP server, no node_modules, no `pip install`. The scripts use only the Python standard library.

POWER.md stays deliberately short because everything in it loads into agent context on activation. Deep-dive content lives in `steering/`, which Kiro loads only when the task calls for it.

> **Why an installer, rather than shipping the hooks in this repo?** Powers can deliver `steering/` files, but not hooks. A `hooks/` directory in a power repo is copied to `~/.kiro/powers/installed/<name>/hooks/` and then ignored, so it never fires. That is tracked in [kirodotdev/Kiro#9007](https://github.com/kirodotdev/Kiro/issues/9007), still open. Until it lands, writing `~/.kiro/hooks/kironomics.json` from a script is the only route to global hooks from a power.

### Installer reference

| Command | What it does |
|---|---|
| `--api-key <KEY>` | Install globally (default action) |
| `--status` | Show detected Kiro version and what's installed |
| `--scan-root <DIR> --prune` | Find and remove old per-workspace installs |
| `--api-base <URL>` | Point at your own backend |
| `--python <PATH>` | Pin a specific interpreter for the hooks |
| `--force` | Install despite a failed version check |
| `--uninstall` | Remove everything |

---

## 🛠️ For developers — running the backend + frontend locally

The Kironomics backend and dashboard live in a separate repo. To run them:

**Backend (Express.js):**

```bash
cd backend
npm install
npm start
# → http://localhost:8080
```

**Frontend (React + Vite):**

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

**Environment:**

```bash
# Frontend
VITE_API_BASE_URL=http://localhost:8080
VITE_COGNITO_USER_POOL_ID=us-west-2_XXX
VITE_COGNITO_CLIENT_ID=XXX
```

---

## 🤝 Contributing

PRs welcome. Ideas worth submitting:

- New badges
- Team challenges
- Slack/Discord integration
- More dashboard charts
- A roast feature for the bottom of the leaderboard 😈

---

## 📜 License, Privacy & Support

- **License:** MIT (SPDX: `MIT`), Copyright (c) 2026 AWS User Group Madurai. Full text in [LICENSE](LICENSE). Go wild.
- **Privacy:** https://www.awsugmdu.in/kironomics#privacy
- **Support:** [open an issue](https://github.com/Poobalan1210/Kironomics/issues)

---

<div align="center">

**Built with ❤️ and probably too many late-night Kiro sessions.**

⭐ **Star this repo if you'd actually use it.**

</div>
