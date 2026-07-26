# Kironomics Troubleshooting

Read this when a user reports that tracking is not working, their score looks wrong, or the leaderboard is not updating.

Start by running the status check, which answers most of these questions at once:

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py --status
```

On Windows use `python` instead of `python3`.

## Setup ran but nothing is tracked

**Cause:** Kiro is older than 1.0.182, so `~/.kiro/hooks/` is not read at all.

**Solution:** Check the version reported by `--status`. Upgrade Kiro via **Kiro menu > Check for Updates**, restart, and re-run the installer. Global hooks shipped in IDE 1.0.182 (Jul 20, 2026) and CLI 2.13.0 (Jul 17, 2026).

## Hooks are not firing right after install

**Cause:** Kiro scans hook files at startup.

**Solution:** Restart Kiro, or reload the window, once. The three Kironomics hooks then appear in the Agent Hooks panel in every workspace.

## My score jumped unrealistically

**Cause:** Old per-workspace hooks are still present alongside the global ones, so every tool call in those projects is counted twice.

**Solution:** Re-run the installer with `--scan-root ~ --prune` and restart Kiro. Run it once without `--prune` first if the user wants to review the list before anything is deleted.

## Legacy hooks show an "upgrade" badge in the Agent Hooks panel

**Cause:** They are 0.x `.kiro.hook` files left over from a per-workspace install. IDE 1.0 replaced that format, and these no longer execute.

**Solution:** Let the installer prune them. The global v1 hooks replace them entirely.

## `python3: command not found` in the hook output

**Cause:** The interpreter recorded at install time no longer exists. This is common after deleting a virtualenv that was active when the user installed.

**Solution:** Re-run the installer, pinning a stable system interpreter:

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py \
  --api-key "<API_KEY>" --python /usr/bin/python3
```

## Nothing shows on the leaderboard

**Cause:** Invalid API key, or the agent has not finished a turn yet.

**Solution:** Check the stored key with `--status` and confirm it matches the key from https://www.awsugmdu.in/kironomics. Send a prompt, let the agent finish so the `Stop` hook fires, then refresh the leaderboard. The reporter can also be run manually to test:

```bash
python3 ~/.kiro/kironomics/kironomics_report.py
```

Run it from the workspace you want to report, since counters are workspace-keyed.

## Plan shows "Auto-Auto" but the user is on Kiro Pro

**Cause:** Kiro's `state.vscdb` does not have `usageState` populated yet. This happens occasionally on first install or right after a Kiro update.

**Solution:** Use Kiro for one full session, then check again. Kiro syncs usage periodically and the next session report picks it up.

## Two Kiro windows produced one merged session

**Cause:** The hooks ran with the same working directory for both windows, so the workspace key collapsed into one bucket.

**Solution:** Expected degradation rather than data loss. Counts are still correct in total, they are just attributed to one session instead of two.

## A session was lost after a network outage

**Cause:** The reporter clears counters even when the POST fails.

**Solution:** This is deliberate. Keeping the counters would roll the failed session into the next one and produce a single implausible session, which is more likely to trip the backend's anti-cheat checks than a single missing report. One lost session is the cheaper failure.

## The user wants to remove Kironomics

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py --uninstall
```

Removes the hooks, both scripts, and the stored key. Restart Kiro and tracking stops immediately.
