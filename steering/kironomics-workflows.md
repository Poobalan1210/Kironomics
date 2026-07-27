# Kironomics Workflows

Read this when the user asks to verify, migrate, rotate credentials, or otherwise operate an existing Kironomics install. First-time setup lives in POWER.md, not here.

All commands assume the power repo is at `~/.kiro/powers/repos/kironomics/`. If it is not, find it with `ls ~/.kiro/powers/repos/`. On Windows use `python` instead of `python3`.

## Setting up on a new machine

Run the Onboarding steps in POWER.md once. Every workspace on that machine is covered from then on.

## "I started a new project, do I need to set this up?"

No. That is the entire point of the global install. The hooks live in `~/.kiro/hooks/` and fire in every workspace, including ones that do not exist yet.

If the user wants reassurance, run `--status` and show them that the hooks are present.

## Verifying tracking is active

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py --status
```

This reports the detected Kiro version, whether the global hooks and scripts are present, and a masked view of the stored API key.

To confirm hooks are actually firing, send a few prompts in any workspace and then list the live counters:

```bash
python3 -c "import glob,os,tempfile;[print(os.path.basename(f),open(f).read()) for f in glob.glob(os.path.join(tempfile.gettempdir(),'kironomics_*'))]"
```

Counts should be climbing. They clear when the agent stops and the session reports.

The strongest test is to create an empty directory that has never had Kironomics in it, open it in Kiro, and send a prompt without running any setup. Counters appearing there is proof the global wiring works.

## Migrating from the old per-workspace setup

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py \
  --api-key "<API_KEY>" --scan-root ~ --prune
```

Run it without `--prune` first if the user wants to review the list before anything is deleted. Repeat `--scan-root` for multiple code directories, and use `--max-depth` if their projects are nested deeper than four levels.

Only Kironomics-owned files are ever touched. Other hooks in the same directory are left alone, and the global hook file itself is explicitly skipped.

This step is not optional for anyone upgrading from a per-workspace install. Leaving the old hooks in place double-counts every tool call in those projects.

## Rotating the API key

The key lives in `~/.kiro/kironomics/config.json`, not in the hooks, so nothing else has to change:

```bash
python3 -c "import json,pathlib;p=pathlib.Path.home()/'.kiro/kironomics/config.json';c=json.loads(p.read_text());c['api_key']='<NEW_KEY>';p.write_text(json.dumps(c,indent=2))"
```

Or re-run the installer with the new `--api-key`. No restart is needed, since the reporter reads the config on each run.

## Pointing at a self-hosted backend

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py \
  --api-key "<API_KEY>" --api-base "https://your-backend.example.com"
```

The reporter appends `/kironomics/session` to whatever base is configured.

## Manually triggering a session report

```bash
python3 ~/.kiro/kironomics/kironomics_report.py
```

Reads the current workspace's counters, reads `state.vscdb`, POSTs to the backend, and clears the counters. Run it from the workspace you want to report. Useful for confirming the backend received data without waiting for the agent to stop.

## Uninstalling

```bash
python3 ~/.kiro/powers/repos/kironomics/scripts/kironomics_install.py --uninstall
```

Removes `~/.kiro/hooks/kironomics.json`, both scripts, and the stored key. Restart Kiro; tracking stops immediately.

## Installer flag reference

| Flag | Effect |
|---|---|
| `--api-key <KEY>` | Install globally. This is the default action. |
| `--status` | Show detected Kiro version and current install state. |
| `--scan-root <DIR>` | Directory to scan for old per-workspace installs. Repeatable. |
| `--max-depth <N>` | Scan depth for `--scan-root`. Defaults to 4. |
| `--prune` | Actually delete the per-workspace files found. Without it, they are only listed. |
| `--api-base <URL>` | Use a self-hosted backend. |
| `--python <PATH>` | Pin the interpreter recorded in the hook commands. |
| `--force` | Install even if the Kiro version check fails. |
| `--uninstall` | Remove everything. |
