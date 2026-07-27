<!--
Title format: <type>(<scope>): <what changed>
Types: feat, fix, docs, refactor, test, chore
Example: feat(hooks): install once per machine via global hooks
-->

## What this changes

<!-- One or two sentences. What is different after this merges? -->

## Why

<!-- The problem this solves. If it fixes a user-visible failure, describe the failure. -->

## Kiro compatibility

<!-- Powers break quietly across Kiro versions, so state this explicitly. -->

- Minimum Kiro IDE / CLI version required:
- Hook format affected (v1 / legacy 0.x / not applicable):
- Triggers touched (`PostToolUse`, `UserPromptSubmit`, `Stop`, other):
- Does this change what is written to `~/.kiro/` or a workspace `.kiro/`?

## How this was tested

<!--
Powers run on other people's machines, so "it works for me" is not enough.
List what you actually ran, on which OS and which Kiro version.
Paste real output or log lines as proof where you can.
-->

- [ ] Tested on a real Kiro install (state version and OS)
- [ ] Tested the failure path, not just the happy path
- [ ] Verified nothing is written into a workspace unless intended
- [ ] `POWER.md` still parses and its frontmatter uses only the five permitted fields

## Impact on existing users

<!-- Anything an already-installed user must do. Say "none" if there is nothing. -->

- Migration required:
- Breaking change:
- Uninstall / rollback path:

## Privacy

<!-- Kironomics is a tracking tool, so this section is not optional. -->

- Does this change what data leaves the user's machine? If yes, exactly what?
- Does this touch `state.vscdb`? Confirm it is still opened read-only.
- Are credentials stored anywhere new?

## Checklist

- [ ] No secrets, API keys, or personal paths committed
- [ ] Docs updated (`POWER.md`, `steering/`, `README.md`) to match behaviour
- [ ] Scripts remain Python standard library only, no new dependencies
- [ ] Works on macOS, Linux and Windows, or the limitation is documented
