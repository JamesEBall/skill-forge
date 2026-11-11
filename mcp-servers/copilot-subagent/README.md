# copilot-subagent

MCP server that lets Claude Code start and configure GitHub Copilot CLI agents.
Each task runs `copilot -p ... --output-format json`, so it uses the Copilot CLI's own login, models, MCP servers, skills, and custom agents.
Standard library Python only.

## Tools
- `copilot_task`: run one agent, in the foreground or with `background=true` to get a job id.
- `copilot_parallel`: run several agents concurrently.
- `copilot_job`: list, check, wait on, or stop background agents.
- `copilot_sessions`: list or read saved Copilot sessions, to resume them.
- `copilot_agents`: list, get, create, or delete custom agent definitions.
- `copilot_models`: live model list for the account; get or set the default model.
- `copilot_config`: list, get, set, or remove Copilot settings.
- `copilot_mcp`: manage Copilot's own MCP servers.
- `copilot_skills`: list, add, remove, enable, or disable skills.
- `copilot_plugins`: plugins and plugin marketplaces.
- `copilot_update`: check for and install Copilot CLI updates.
- `copilot_workflow`: run a registered dynamic workflow.
- `copilot_info`: version, instruction sources, language servers, help topics.

## Config (environment variables)
- `COPILOT_BIN`: path to the `copilot` CLI.
- `COPILOT_DEFAULT_MODEL`: default model. Falls back to Copilot's own default.
- `COPILOT_DEFAULT_ACCESS`: default access preset (default `read_only`).

The server writes job logs to `jobs/` and a model list to `models-cache.json` next to `server.py`. Both are ignored by git.

## Manage
Register:
```bash
claude mcp add --scope user copilot-subagent -- python3 ~/.claude/mcp-servers/copilot-subagent/server.py
```
Remove:
```bash
claude mcp remove copilot-subagent -s user
```
