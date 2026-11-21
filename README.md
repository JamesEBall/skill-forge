# skill-forge

My skills and MCP servers for Claude Code, in one repo.

## Skills

| Skill | What it does | Origin |
| --- | --- | --- |
| [unslop](skills/unslop/SKILL.md) | Rewrites text so it stops reading like AI output, using rules distilled from Wikipedia's "Signs of AI writing" page. | Mine |
| [overleaf-olcli](skills/overleaf-olcli/SKILL.md) | Drives Overleaf projects from the terminal with the `olcli` CLI: pull, push, sync, compile, comments. | Mine. The CLI itself is [aloth/olcli](https://github.com/aloth/olcli) (MIT) and is not included here. |
| [adb-style](skills/adb-style/SKILL.md) | Reviews a draft against the Asian Development Bank *Handbook of Style and Usage* (2024 edition) and rewrites it to comply. Comes with reference lists (member names, currencies, abbreviations, citation models) and a small regex linter. | Mine. The rules are condensed from [ADB's handbook](https://www.adb.org/sites/default/files/institutional-document/31385/hsu-2024.pdf), which is not included here. |

## MCP servers

| Server | What it does |
| --- | --- |
| [copilot-subagent](mcp-servers/copilot-subagent) | Lets Claude Code delegate tasks to GitHub Copilot CLI agents and manage Copilot's config. |
| [opencode-subagent](mcp-servers/opencode-subagent) | Lets Claude Code delegate tasks to OpenCode agents. |

Both are single-file Python servers with no dependencies beyond the standard library. You need the `copilot` or `opencode` CLI installed and signed in.

## Install

Clone the repo:

```bash
git clone https://github.com/JamesEBall/skill-forge.git
```

Install a skill by copying its folder into `~/.claude/skills/`:

```bash
cp -R skill-forge/skills/unslop ~/.claude/skills/
```

Install a server by copying its folder into `~/.claude/mcp-servers/` and registering it:

```bash
cp -R skill-forge/mcp-servers/copilot-subagent ~/.claude/mcp-servers/
```

```bash
claude mcp add --scope user copilot-subagent -- python3 ~/.claude/mcp-servers/copilot-subagent/server.py
```
