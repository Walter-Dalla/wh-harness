# Security Policy

## Supported versions

Only the latest version on `main` receives security fixes. The current version is the `version` field of [`plugins/wh/.claude-plugin/plugin.json`](plugins/wh/.claude-plugin/plugin.json).

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Report it privately through GitHub: [**Security → Report a vulnerability**](https://github.com/Walter-Dalla/wh-harness/security/advisories/new). Include:

- what the problem is and what an attacker could do with it
- steps to reproduce, or a proof of concept
- the plugin version and your Claude Code version

You should get a first answer within 7 days. Once a fix is released, the advisory is published with credit to you, unless you prefer otherwise.

## Scope

The plugin runs shell and Python scripts and a `UserPromptSubmit` hook on the user's machine, and it drives agents that edit code and open pull requests. Reports of particular interest: command injection through file names, branch names or profile contents; a script that writes outside the repository or its worktrees; the hook leaking content it should not add to the prompt.
