# opencode-subagent

MCP server that lets Claude Code delegate work to OpenCode v2 agents (e.g. University of Edinburgh ELM models).
Runs `opencode run --format json` against the OpenCode desktop app's background service, so it uses the same config and API keys as the GUI.
Standard library Python only.

## Tools
- `opencode_task`: run one task (`prompt`, `cwd`, optional `model`, `agent`, `session_id`, `timeout`, `show_in_gui`, `title`).
- `opencode_parallel`: run up to 12 tasks, 4 at a time by default (max 6).
- `opencode_models`: list the model ids you can use.

## Agents
- `plan` (default): cannot edit files, but can still run shell commands.
- `explore`: fast search (grep, glob, shell).
- `general`: multi-step tasks, can edit.
- `build`: full access.

Nothing is auto-approved: the server never passes `--auto`.
Sessions are archived (hidden from the OpenCode app) unless `show_in_gui` is true.

## Config (environment variables)
- `OPENCODE_BIN`: path to the CLI. Default: the newest CLI bundled with OpenCode.app.
- `OPENCODE_DEFAULT_MODEL`: model to use when a task doesn't name one.
- `OPENCODE_DEFAULT_AGENT`: agent to use when a task doesn't name one (default `plan`).

## Manage
Register:
```bash
claude mcp add --scope user opencode-subagent -- python3 ~/.claude/mcp-servers/opencode-subagent/server.py
```
Remove:
```bash
claude mcp remove opencode-subagent -s user
```
