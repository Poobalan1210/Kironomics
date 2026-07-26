# Kironomics Scoring, Titles and Badges

Read this when the user asks how their score is calculated, what a title or badge means, how plans are detected, or how the anti-cheat system works.

## Score Formula

Primary, credit-based and tamper-proof:

```
score = (credits_consumed × 100) + (tool_calls × 1) + (prompts × 2)
```

Fallback, used for accounts with no credit data yet such as Auto-Auto:

```
score = (tool_calls × 3) + (prompts × 5) + (elapsed_minutes)
```

Credits dominate deliberately. Tool calls and prompts are cheap to generate, credits are not, so weighting credits at 100x makes the honest path the highest-scoring one.

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

Plans are auto-detected from `usageLimit` in `state.vscdb`:

| Plan | Limit | Price |
|---|---|---|
| Kiro Free | 50 credits/mo | $0 |
| Kiro Pro | 1,000 credits/mo | $20/mo |
| Kiro Pro+ | 2,000 credits/mo | $40/mo |
| Kiro Power | 10,000 credits/mo | $200/mo |
| Auto-Auto | no usageState present | not detected |

Auto-Auto users skip credit tracking but still earn hook-based scores through the fallback formula.

`state.vscdb` is located per platform:

| Platform | Path |
|---|---|
| macOS | `~/Library/Application Support/Kiro/User/globalStorage/state.vscdb` |
| Windows | `%APPDATA%\Kiro\User\globalStorage\state.vscdb` |
| Linux | `~/.config/Kiro/User/globalStorage/state.vscdb` |

It is always opened with `mode=ro&immutable=1`. Kironomics never writes to Kiro's database.

## Anti-Cheat

Credit data comes from Kiro's own SQLite database, which is server-synced from AWS billing. It cannot be faked without modifying Kiro's internals, which would corrupt the IDE.

Backend sanity checks:

1. **Repeated zero-credit sessions with high hook activity** are flagged after three or more consecutive sessions.
2. **A credits-to-events ratio over 50x** is flagged, since it is not reachable even on heavy Opus usage.
3. **Optional AWS Cost Explorer verification** cross-references hook data against actual AWS billing to award the AWS Verified badge.

Flagged users are hidden from the leaderboard until reviewed.

Note for anyone migrating from a per-workspace install: leaving old workspace hooks alongside the global ones double-counts tool calls, which can look like check 2 above. If a user reports being flagged shortly after migrating, have them re-run the installer with `--scan-root ~ --prune`.
