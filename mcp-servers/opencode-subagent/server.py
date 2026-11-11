#!/usr/bin/env python3
"""MCP server that lets Claude Code delegate tasks to OpenCode v2 subagents.

Each task runs `opencode run --format json` against the OpenCode desktop app's
background service (so the same config, providers and API keys are used, e.g.
University of Edinburgh ELM). Standard library only; speaks MCP over stdio.

Tools:
  opencode_task      run one task and return the agent's answer
  opencode_parallel  run several tasks concurrently
  opencode_models    list models OpenCode can use

Environment overrides:
  OPENCODE_BIN            path to the opencode CLI
  OPENCODE_DEFAULT_MODEL  default model (provider/model), else OpenCode's own default
  OPENCODE_DEFAULT_AGENT  default agent (default: plan)
"""

import glob
import json
import os
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

SERVER_NAME = "opencode-subagent"
SERVER_VERSION = "1.0.0"
AGENTS = ["plan", "explore", "general", "build"]
DEFAULT_AGENT = os.environ.get("OPENCODE_DEFAULT_AGENT", "plan")
DEFAULT_MODEL = os.environ.get("OPENCODE_DEFAULT_MODEL", "")
DEFAULT_TIMEOUT = 600
MAX_PARALLEL = 6

_write_lock = threading.Lock()


def _version_key(path):
    ver = os.path.basename(os.path.dirname(path)).split("-")[0]
    try:
        return tuple(int(x) for x in ver.split("."))
    except ValueError:
        return (0,)


def find_opencode():
    env = os.environ.get("OPENCODE_BIN")
    if env and os.path.exists(env):
        return env
    pattern = os.path.expanduser(
        "~/Library/Application Support/ai.opencode.desktop/cli/*/opencode-cli")
    bundled = sorted(glob.glob(pattern), key=_version_key)
    if bundled:
        return bundled[-1]
    for cand in (shutil.which("opencode"), os.path.expanduser("~/.opencode/bin/opencode")):
        if cand and os.path.exists(cand):
            return cand
    raise RuntimeError("OpenCode CLI not found; set OPENCODE_BIN")


def _short(value, limit=160):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def run_task(prompt, cwd=None, model=None, agent=None, session_id=None,
             timeout=None, show_in_gui=False, title=None):
    if not prompt or not str(prompt).strip():
        return {"ok": False, "error": "prompt is empty"}
    cwd = os.path.expanduser(cwd or os.getcwd())
    if not os.path.isdir(cwd):
        return {"ok": False, "error": f"cwd does not exist: {cwd}"}
    agent = agent or DEFAULT_AGENT
    if agent not in AGENTS:
        return {"ok": False, "error": f"agent must be one of {AGENTS}"}
    model = model or DEFAULT_MODEL
    timeout = max(10, min(int(timeout or DEFAULT_TIMEOUT), 3600))

    cmd = [find_opencode(), "run", "--format", "json", "--agent", agent]
    if model:
        cmd += ["--model", model]
    if session_id:
        cmd += ["--session", session_id]
    elif not show_in_gui:
        cmd.append("--archived")
    if title:
        cmd += ["--title", title]
    cmd += ["--", prompt]

    # OpenCode takes its project directory from $PWD, so set it as well as cwd.
    env = dict(os.environ, PWD=cwd)
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                              timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired as exc:
        partial = parse_events(exc.stdout or "")
        partial.update(ok=False, error=f"timed out after {timeout}s")
        return partial

    result = parse_events(proc.stdout)
    result["agent"] = agent
    result["model"] = model or "(opencode default)"
    result["cwd"] = cwd
    if proc.returncode != 0 or result.get("errors"):
        result["ok"] = False
        tail = (proc.stderr or "").strip()[-1500:]
        if tail:
            result.setdefault("errors", []).append(tail)
    else:
        result["ok"] = True
    return result


def parse_events(stdout):
    session_id = None
    texts = []          # (messageID, text)
    tools = []
    errors = []
    tokens = {"input": 0, "output": 0, "reasoning": 0}
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        session_id = ev.get("sessionID") or session_id
        part = ev.get("part") or {}
        etype = ev.get("type")
        if etype == "text" and part.get("text"):
            texts.append((part.get("messageID"), part["text"]))
        elif etype == "tool_use":
            state = part.get("state") or {}
            tools.append({
                "tool": part.get("tool"),
                "status": state.get("status"),
                "input": _short(state.get("input", {})),
            })
            if state.get("status") == "error":
                errors.append(f"tool {part.get('tool')} failed: {_short(state.get('error', ''), 400)}")
        elif etype == "step_finish":
            for key in tokens:
                tokens[key] += int((part.get("tokens") or {}).get(key) or 0)
        elif etype == "error" or (etype != "tool_use" and "error" in ev):
            errors.append(_short(ev.get("error") or ev, 800))

    # The answer is the text of the last assistant message; keep earlier text as notes.
    answer = ""
    if texts:
        last_msg = texts[-1][0]
        answer = "".join(t for m, t in texts if m == last_msg).strip()
    return {
        "session_id": session_id,
        "answer": answer,
        "tool_calls": tools,
        "tokens": tokens,
        "errors": errors,
    }


def format_result(res, label=None):
    head = f"## {label}\n" if label else ""
    status = "ok" if res.get("ok") else "FAILED"
    lines = [f"{head}status: {status} | agent: {res.get('agent', '?')} | model: {res.get('model', '?')}",
             f"session_id: {res.get('session_id')} (pass as session_id to continue)"]
    if res.get("tool_calls"):
        lines.append("tools used: " + ", ".join(
            f"{t['tool']}({t['status']})" for t in res["tool_calls"]))
    if res.get("tokens"):
        t = res["tokens"]
        lines.append(f"tokens: in {t['input']}, out {t['output']}, reasoning {t['reasoning']}")
    for err in res.get("errors") or ([res["error"]] if res.get("error") else []):
        lines.append(f"error: {err}")
    lines.append("")
    lines.append(res.get("answer") or "(no answer text)")
    return "\n".join(lines)


TASK_PROPS = {
    "prompt": {"type": "string", "description": "Self-contained instructions for the OpenCode agent. It sees none of this conversation, so include file paths and context."},
    "cwd": {"type": "string", "description": "Absolute directory the agent works in (its project root)."},
    "model": {"type": "string", "description": "provider/model, e.g. elm/Qwen/Qwen3.5-397B-A17B-FP8 or elm/mistralai/Mistral-Small-4-119B-2603. Omit for OpenCode's default."},
    "agent": {"type": "string", "enum": AGENTS, "description": "plan (default): cannot edit files. explore: fast search (grep/glob/shell). general: multi-step research and tasks, can edit. build: full access, can edit files and run commands."},
    "session_id": {"type": "string", "description": "Continue an earlier OpenCode session (from a previous result)."},
    "timeout": {"type": "integer", "description": f"Seconds before giving up (default {DEFAULT_TIMEOUT})."},
    "show_in_gui": {"type": "boolean", "description": "Keep the session visible in the OpenCode app's session list (default false: archived)."},
    "title": {"type": "string", "description": "Session title shown in OpenCode."},
}

TOOLS = [
    {
        "name": "opencode_task",
        "description": (
            "Delegate a task to an OpenCode v2 subagent (runs on the user's OpenCode providers, "
            "e.g. University of Edinburgh ELM models) and return its final answer, tool calls and "
            "session id. Good for second opinions, code review, searching a codebase, or offloading "
            "work to a different model. Defaults to the 'plan' agent, which cannot edit files."),
        "inputSchema": {"type": "object", "properties": TASK_PROPS, "required": ["prompt", "cwd"]},
    },
    {
        "name": "opencode_parallel",
        "description": (
            "Run several OpenCode subagent tasks at once (up to "
            f"{MAX_PARALLEL} concurrently) and return every result. Each task takes the same "
            "fields as opencode_task. Do not give two editing (build/general) tasks the same files."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "tasks": {"type": "array", "minItems": 1, "maxItems": 12,
                          "items": {"type": "object", "properties": TASK_PROPS, "required": ["prompt", "cwd"]}},
                "max_concurrency": {"type": "integer", "description": f"Default 4, max {MAX_PARALLEL}."},
            },
            "required": ["tasks"],
        },
    },
    {
        "name": "opencode_models",
        "description": "List the models OpenCode can use (provider/model ids for the model field).",
        "inputSchema": {"type": "object", "properties": {"filter": {"type": "string", "description": "Only ids containing this text, e.g. 'elm'."}}},
    },
]


def call_tool(name, args):
    if name == "opencode_task":
        res = run_task(**{k: v for k, v in args.items() if k in TASK_PROPS})
        return format_result(res), not res.get("ok")
    if name == "opencode_parallel":
        tasks = args.get("tasks") or []
        if not 1 <= len(tasks) <= 12:
            return "error: tasks must contain between 1 and 12 items", True
        conc = max(1, min(int(args.get("max_concurrency") or 4), MAX_PARALLEL))
        with ThreadPoolExecutor(max_workers=conc) as pool:
            futures = [pool.submit(run_task, **{k: v for k, v in t.items() if k in TASK_PROPS}) for t in tasks]
            results = [f.result() for f in futures]
        body = "\n\n".join(format_result(r, f"Task {i + 1}") for i, r in enumerate(results))
        failed = sum(1 for r in results if not r.get("ok"))
        return f"{len(results) - failed}/{len(results)} tasks succeeded\n\n{body}", failed == len(results)
    if name == "opencode_models":
        proc = subprocess.run([find_opencode(), "models"], capture_output=True, text=True, timeout=60)
        ids = [l.strip() for l in proc.stdout.splitlines() if "/" in l]
        flt = (args.get("filter") or "").lower()
        ids = [i for i in ids if flt in i.lower()]
        if proc.returncode != 0:
            return f"error: opencode models failed: {(proc.stderr or '').strip()[-1000:]}", True
        return "\n".join(ids) or "(no models found)", False
    raise ValueError(f"unknown tool: {name}")


def send(msg):
    with _write_lock:
        sys.stdout.write(json.dumps(msg) + "\n")
        sys.stdout.flush()


def handle(req):
    method, rid = req.get("method"), req.get("id")
    if rid is None:
        return  # notification
    try:
        if method == "initialize":
            client_ver = (req.get("params") or {}).get("protocolVersion") or "2025-06-18"
            result = {"protocolVersion": client_ver, "capabilities": {"tools": {}},
                      "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION}}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            params = req.get("params") or {}
            try:
                text, is_error = call_tool(params.get("name"), params.get("arguments") or {})
            except Exception as exc:  # report tool failures to the model, not as protocol errors
                text, is_error = f"error: {exc}", True
            result = {"content": [{"type": "text", "text": text}], "isError": is_error}
        elif method == "ping":
            result = {}
        else:
            send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"method not found: {method}"}})
            return
        send({"jsonrpc": "2.0", "id": rid, "result": result})
    except Exception as exc:
        send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32603, "message": str(exc)}})


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        if req.get("method") == "tools/call":
            threading.Thread(target=handle, args=(req,), daemon=True).start()
        else:
            handle(req)


if __name__ == "__main__":
    main()
