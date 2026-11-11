#!/usr/bin/env python3
"""MCP server that lets Claude Code spin up and configure GitHub Copilot CLI agents.

Each task runs `copilot -p ... --output-format json` (non-interactive), so it uses
the Copilot CLI's own login, models, MCP servers, skills and custom agents.
Standard library only; speaks MCP over stdio.

Tools:
  copilot_task      run one agent (foreground, or background=true to get a job id)
  copilot_parallel  run several agents concurrently
  copilot_job       list / status / wait / stop background agents
  copilot_sessions  list or read saved Copilot sessions (to resume them)
  copilot_agents    list / get / create / delete custom agent definitions
  copilot_models    live model list for this account; get / set the default model
  copilot_config    list / get / set / remove Copilot settings
  copilot_mcp       list / get / add / remove / enable / disable Copilot's MCP servers
  copilot_skills    list / add / remove / enable / disable skills
  copilot_plugins   plugins and plugin marketplaces
  copilot_update    check for and install Copilot CLI updates
  copilot_workflow  run a registered dynamic workflow
  copilot_info      version, instruction sources, language servers, help topics

Environment overrides:
  COPILOT_BIN             path to the copilot CLI
  COPILOT_DEFAULT_MODEL   default model, else Copilot's own default
  COPILOT_DEFAULT_ACCESS  default access preset (default: read_only)
"""

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

SERVER_NAME = "copilot-subagent"
SERVER_VERSION = "2.0.0"
COPILOT_HOME = os.path.expanduser(os.environ.get("COPILOT_HOME", "~/.copilot"))
JOBS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobs")
ACCESS = ["read_only", "edit", "full", "custom"]
DEFAULT_ACCESS = os.environ.get("COPILOT_DEFAULT_ACCESS", "read_only")
DEFAULT_MODEL = os.environ.get("COPILOT_DEFAULT_MODEL", "")
EFFORTS = ["none", "minimal", "low", "medium", "high", "xhigh", "max"]
DEFAULT_TIMEOUT = 900
MAX_PARALLEL = 6
SHELL_TOOLS = ["bash", "write_bash", "read_bash", "stop_bash", "list_bash"]
WRITE_TOOLS = ["create", "edit", "apply_patch"]
AGENT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

_write_lock = threading.Lock()
_jobs = {}            # job_id -> dict(proc, out, err, started, meta)
_jobs_lock = threading.Lock()


def find_copilot():
    for cand in (os.environ.get("COPILOT_BIN"), shutil.which("copilot"),
                 "/opt/homebrew/bin/copilot", "/usr/local/bin/copilot"):
        if cand and os.path.exists(cand):
            return cand
    raise RuntimeError("Copilot CLI not found; set COPILOT_BIN")


def _short(value, limit=160):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _list(value):
    if value is None:
        return []
    return [str(v) for v in (value if isinstance(value, list) else [value]) if str(v).strip()]


# ---------------------------------------------------------------- running agents

def build_command(a):
    """Translate task arguments into a copilot command line. Returns (cmd, cwd, meta)."""
    prompt = a.get("prompt")
    if not prompt or not str(prompt).strip():
        raise ValueError("prompt is empty")
    cwd = os.path.expanduser(a.get("cwd") or os.getcwd())
    if not os.path.isdir(cwd):
        raise ValueError(f"cwd does not exist: {cwd}")
    access = a.get("access") or DEFAULT_ACCESS
    if access not in ACCESS:
        raise ValueError(f"access must be one of {ACCESS}")
    model = a.get("model") or DEFAULT_MODEL

    cmd = [find_copilot(), f"--prompt={prompt}", "--output-format=json", "--stream=off",
           "--no-color", "--no-auto-update"]
    if not a.get("allow_questions"):
        cmd.append("--no-ask-user")
    if model:
        cmd.append(f"--model={model}")
    if a.get("reasoning_effort"):
        cmd.append(f"--reasoning-effort={a['reasoning_effort']}")
    if a.get("context"):
        cmd.append(f"--context={a['context']}")
    if a.get("experimental"):
        cmd.append("--experimental")
    if a.get("agent"):
        cmd.append(f"--agent={a['agent']}")
    if a.get("session_id"):
        cmd.append(f"--resume={a['session_id']}")
    if a.get("name"):
        cmd.append(f"--name={a['name']}")
    if a.get("mode"):
        cmd.append(f"--mode={a['mode']}")
    if a.get("fleet"):
        cmd.append("--fleet")
    if a.get("max_autopilot_continues") is not None:
        cmd.append(f"--max-autopilot-continues={int(a['max_autopilot_continues'])}")
    if a.get("max_ai_credits") is not None:
        cmd.append(f"--max-ai-credits={a['max_ai_credits']}")

    # Permissions. Deny rules beat allow rules, so presets are allow-all plus denials.
    # The presets also hide the tools they forbid, so the model reaches for view/grep/glob
    # instead of trying a shell command and being refused.
    deny, hidden = _list(a.get("deny_tools")), _list(a.get("excluded_tools"))
    if access == "read_only":
        deny += ["write", "shell"]
        hidden += SHELL_TOOLS + WRITE_TOOLS
    elif access == "edit":
        deny += ["shell"]
        hidden += SHELL_TOOLS
    if access != "custom":
        cmd.append("--allow-all-tools")
    for t in _list(a.get("allow_tools")):
        cmd.append(f"--allow-tool={t}")
    for t in dict.fromkeys(deny):
        cmd.append(f"--deny-tool={t}")
    for t in _list(a.get("available_tools")):
        cmd.append(f"--available-tools={t}")
    for t in dict.fromkeys(hidden):
        cmd.append(f"--excluded-tools={t}")
    if a.get("allow_all_paths"):
        cmd.append("--allow-all-paths")
    if a.get("disallow_temp_dir"):
        cmd.append("--disallow-temp-dir")
    if a.get("secret_env_vars"):
        cmd.append("--secret-env-vars=" + ",".join(_list(a["secret_env_vars"])))
    for d in _list(a.get("add_dirs")):
        cmd.append(f"--add-dir={os.path.expanduser(d)}")
    if a.get("allow_all_urls"):
        cmd.append("--allow-all-urls")
    for u in _list(a.get("allow_urls")):
        cmd.append(f"--allow-url={u}")
    for u in _list(a.get("deny_urls")):
        cmd.append(f"--deny-url={u}")

    # MCP servers / context for this run only.
    mcp = a.get("mcp_config")
    if mcp:
        if isinstance(mcp, dict) and "mcpServers" not in mcp:
            mcp = {"mcpServers": mcp}
        cmd.append("--additional-mcp-config=" + (mcp if isinstance(mcp, str) else json.dumps(mcp)))
    for s in _list(a.get("disable_mcp_servers")):
        cmd.append(f"--disable-mcp-server={s}")
    for s in _list(a.get("enable_mcp_servers")):
        cmd.append(f"--enable-mcp-server={s}")
    if a.get("disable_builtin_mcps"):
        cmd.append("--disable-builtin-mcps")
    for t in _list(a.get("github_mcp_toolsets")):
        cmd.append(f"--add-github-mcp-toolset={t}")
    for p in _list(a.get("plugin_dirs")):
        cmd.append(f"--plugin-dir={os.path.expanduser(p)}")
    for f in _list(a.get("attachments")):
        cmd.append(f"--attachment={os.path.expanduser(f)}")
    if a.get("no_custom_instructions"):
        cmd.append("--no-custom-instructions")
    if a.get("enable_memory"):
        cmd.append("--enable-memory")
    if a.get("share_path"):
        cmd.append(f"--share={os.path.expanduser(a['share_path'])}")

    env = a.get("env") or {}
    if not isinstance(env, dict):
        raise ValueError("env must be an object of NAME: value")
    meta = {"access": access, "model": model or "(copilot default)",
            "agent": a.get("agent") or "(default)", "cwd": cwd, "label": a.get("name") or _short(prompt, 60),
            "env": {str(k): str(v) for k, v in env.items()}}
    return cmd, cwd, meta


def prune_job_logs(max_age=3 * 86400):
    """Delete job logs older than max_age seconds that no live job owns."""
    with _jobs_lock:
        live = {j["id"] for j in _jobs.values() if j["proc"].poll() is None}
    try:
        for fn in os.listdir(JOBS_DIR):
            path = os.path.join(JOBS_DIR, fn)
            if fn.split(".")[0] not in live and time.time() - os.path.getmtime(path) > max_age:
                os.remove(path)
    except OSError:
        pass


def start_job(a):
    cmd, cwd, meta = build_command(a)
    os.makedirs(JOBS_DIR, exist_ok=True)
    prune_job_logs()
    job_id = uuid.uuid4().hex[:10]
    out_path = os.path.join(JOBS_DIR, f"{job_id}.jsonl")
    err_path = os.path.join(JOBS_DIR, f"{job_id}.err")
    out, err = open(out_path, "w"), open(err_path, "w")
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=out, stderr=err, stdin=subprocess.DEVNULL,
                            start_new_session=True, env=dict(os.environ, **meta.pop("env")))
    out.close()
    err.close()
    job = {"id": job_id, "proc": proc, "out": out_path, "err": err_path,
           "started": time.time(), "meta": meta, "stopped": None}
    with _jobs_lock:
        _jobs[job_id] = job
    return job


def kill_job(job, reason):
    if job["proc"].poll() is None:
        job["stopped"] = reason
        try:
            os.killpg(job["proc"].pid, signal.SIGTERM)
            job["proc"].wait(timeout=5)
        except Exception:
            try:
                os.killpg(job["proc"].pid, signal.SIGKILL)
            except Exception:
                pass


def _read(path, tail=None):
    try:
        with open(path, errors="replace") as fh:
            text = fh.read()
        return text[-tail:] if tail else text
    except OSError:
        return ""


def parse_events(stdout):
    session_id, answer, model = None, "", None
    tools, errors, usage = [], [], {}
    for line in (stdout or "").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        etype, data = ev.get("type") or "", ev.get("data") or {}
        if etype == "assistant.message":
            model = data.get("model") or model
            if (data.get("content") or "").strip():
                answer = data["content"].strip()
            for req in data.get("toolRequests") or []:
                tools.append({"tool": req.get("name"), "input": _short(req.get("arguments", {}))})
        elif etype == "result":
            session_id = ev.get("sessionId") or session_id
            usage = ev.get("usage") or {}
            if ev.get("exitCode"):
                errors.append(f"copilot exit code {ev['exitCode']}")
        elif "error" in etype or (etype == "model.call_finished" and data.get("outcome") not in (None, "success")):
            errors.append(_short(data.get("message") or data.get("error") or data, 800))
        elif etype == "session.info" and data.get("infoType") in ("warning", "error"):
            errors.append(_short(data.get("message", ""), 400))
        elif etype == "permission.denied" or etype.endswith("permission_denied"):
            errors.append("permission denied: " + _short(data, 300))
    return {"session_id": session_id, "answer": answer, "model_used": model,
            "tool_calls": tools, "usage": usage, "errors": errors}


def job_result(job):
    """Snapshot of a job: parsed output plus state (running / done / stopped)."""
    res = parse_events(_read(job["out"]))
    res.update(job["meta"])
    res["job_id"] = job["id"]
    code = job["proc"].poll()
    if code is not None:
        job.setdefault("ended", time.time())
    res["elapsed"] = int(job.get("ended", time.time()) - job["started"])
    if code is None:
        res["state"], res["ok"] = "running", True
    elif job["stopped"]:
        res["state"], res["ok"] = "stopped", False
        res["errors"].append(job["stopped"])
    else:
        res["state"] = "done"
        res["ok"] = code == 0 and not (res["errors"] and not res["answer"])
        if code != 0:
            tail = _read(job["err"], 1500).strip()
            if tail or not res["errors"]:
                res["errors"].append(f"exit code {code}" + (f": {tail}" if tail else ""))
    if any("is not available" in e and "Model" in e for e in res["errors"]):
        res["errors"].append("that model is not enabled on this Copilot account; run copilot_models "
                             "(action=list) for valid ids, or action=set_default to fix the saved default")
    return res


def run_task(a):
    try:
        timeout = max(10, min(int(a.get("timeout") or DEFAULT_TIMEOUT), 7200))
        job = start_job(a)
    except Exception as exc:
        return {"ok": False, "state": "failed", "errors": [str(exc)]}
    if a.get("background"):
        return job_result(job)
    try:
        job["proc"].wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_job(job, f"timed out after {timeout}s (partial output kept)")
    return job_result(job)


def format_result(res, label=None):
    head = f"## {label}\n" if label else ""
    state = res.get("state", "?") if res.get("ok") else f"FAILED ({res.get('state', '?')})"
    lines = [f"{head}status: {state} | access: {res.get('access', '?')} | agent: {res.get('agent', '?')} "
             f"| model: {res.get('model_used') or res.get('model', '?')} | {res.get('elapsed', 0)}s"]
    if res.get("job_id") and res.get("state") == "running":
        lines.append(f"job_id: {res['job_id']} (use copilot_job with action=wait/status/stop)")
    if res.get("session_id"):
        lines.append(f"session_id: {res['session_id']} (pass as session_id to continue this agent)")
    if res.get("tool_calls"):
        names = [t["tool"] for t in res["tool_calls"]]
        counts = {n: names.count(n) for n in dict.fromkeys(names)}
        lines.append("tools used: " + ", ".join(f"{n}×{c}" if c > 1 else str(n) for n, c in counts.items()))
    u = res.get("usage") or {}
    if u:
        changes = u.get("codeChanges") or {}
        lines.append(f"usage: {u.get('premiumRequests', 0)} premium request(s); "
                     f"+{changes.get('linesAdded', 0)}/-{changes.get('linesRemoved', 0)} lines"
                     + (f"; files: {', '.join(changes['filesModified'])}" if changes.get("filesModified") else ""))
    for err in res.get("errors") or []:
        lines.append(f"error: {err}")
    lines.append("")
    lines.append(res.get("answer") or ("(still running)" if res.get("state") == "running" else "(no answer text)"))
    return "\n".join(lines)


def job_tool(args):
    action = args.get("action") or "list"
    with _jobs_lock:
        jobs = dict(_jobs)
    if action == "list":
        if not jobs:
            return "(no background agents started in this server session)", False
        rows = []
        for j in jobs.values():
            r = job_result(j)
            rows.append(f"{j['id']}  {r['state']:8} {r['elapsed']:>5}s  {r['agent']}  {j['meta']['label']}")
        return "\n".join(rows), False
    job = jobs.get(args.get("job_id") or "")
    if not job:
        return f"error: unknown job_id (known: {', '.join(jobs) or 'none'})", True
    if action == "stop":
        kill_job(job, "stopped by request")
    elif action == "wait":
        try:
            job["proc"].wait(timeout=max(1, min(int(args.get("timeout") or 600), 3600)))
        except subprocess.TimeoutExpired:
            pass  # still running; report progress so far
    elif action != "status":
        return "error: action must be list, status, wait or stop", True
    res = job_result(job)
    return format_result(res), not res.get("ok")


# ---------------------------------------------------------------- sessions

def _yaml_fields(path):
    fields = {}
    for line in _read(path).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip().strip("'\"")
    return fields


def sessions_tool(args):
    root = os.path.join(COPILOT_HOME, "session-state")
    action = args.get("action") or "list"
    if action == "list":
        rows = []
        for sid in os.listdir(root) if os.path.isdir(root) else []:
            f = _yaml_fields(os.path.join(root, sid, "workspace.yaml"))
            if f:
                rows.append(f)
        flt = os.path.expanduser(args.get("cwd") or "")
        if flt:
            rows = [r for r in rows if r.get("cwd", "").startswith(flt.rstrip("/"))]
        rows.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
        rows = rows[: max(1, min(int(args.get("limit") or 20), 200))]
        return "\n".join(f"{r.get('id')}  {r.get('updated_at', '')[:19]}  {_short(r.get('name', ''), 60)}  [{r.get('cwd', '')}]"
                         for r in rows) or "(no sessions)", False
    if action == "read":
        sid = args.get("session_id") or ""
        if not re.fullmatch(r"[0-9a-fA-F-]{7,36}", sid):
            return "error: session_id required", True
        matches = [d for d in os.listdir(root) if d.startswith(sid)] if os.path.isdir(root) else []
        if len(matches) != 1:
            return f"error: {len(matches)} sessions match '{sid}'", True
        out = []
        for line in _read(os.path.join(root, matches[0], "events.jsonl")).splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            data = ev.get("data") or {}
            if ev.get("type") == "user.message":
                out.append("### user\n" + (data.get("content") or ""))
            elif ev.get("type") == "assistant.message":
                calls = ", ".join(str(r.get("name")) for r in data.get("toolRequests") or [])
                body = (data.get("content") or "").strip()
                if body or calls:
                    out.append("### copilot" + (f" [tools: {calls}]" if calls else "") + ("\n" + body if body else ""))
        text = "\n\n".join(out) or "(no messages)"
        limit = max(500, min(int(args.get("max_chars") or 12000), 100000))
        return (f"session {matches[0]}\n\n" + (text if len(text) <= limit else "…(truncated)…\n" + text[-limit:])), False
    return "error: action must be list or read", True


# ---------------------------------------------------------------- custom agents

def _agents_dir(args):
    if (args.get("scope") or "user") == "project":
        cwd = os.path.expanduser(args.get("cwd") or "")
        if not os.path.isdir(cwd):
            raise ValueError("scope=project needs cwd (the project root)")
        return os.path.join(cwd, ".github", "agents")
    return os.path.join(COPILOT_HOME, "agents")


def _yaml_str(value):
    return json.dumps(str(value), ensure_ascii=False)  # JSON strings are valid YAML scalars


def agents_tool(args):
    action = args.get("action") or "list"
    if action == "list":
        dirs = [("user", os.path.join(COPILOT_HOME, "agents"))]
        cwd = os.path.expanduser(args.get("cwd") or "")
        if cwd and os.path.isdir(cwd):
            dirs.append(("project", os.path.join(cwd, ".github", "agents")))
        rows = []
        for scope, d in dirs:
            for fn in sorted(os.listdir(d)) if os.path.isdir(d) else []:
                if fn.endswith(".md"):
                    m = re.search(r"^description:\s*(.*)$", _read(os.path.join(d, fn)), re.M)
                    rows.append(f"{fn.replace('.agent.md', '').replace('.md', '')}  ({scope})  "
                                f"{_short(m.group(1).strip(chr(34) + chr(39)), 100) if m else ''}")
        return "\n".join(rows) or "(no custom agents; create one with action=create)", False

    name = args.get("name") or ""
    if not AGENT_NAME_RE.match(name):
        return "error: name must be letters, digits, '.', '_' or '-'", True
    path = os.path.join(_agents_dir(args), f"{name}.agent.md")
    if action == "get":
        return (_read(path), False) if os.path.exists(path) else (f"error: no agent at {path}", True)
    if action == "delete":
        if not os.path.exists(path):
            return f"error: no agent at {path}", True
        os.remove(path)
        return f"deleted {path}", False
    if action == "create":
        if not args.get("description") or not args.get("instructions"):
            return "error: description and instructions are required", True
        if os.path.exists(path) and not args.get("overwrite"):
            return f"error: {path} exists; pass overwrite=true to replace it", True
        front = ["---", f"name: {_yaml_str(name)}", f"description: {_yaml_str(args['description'])}"]
        if args.get("model"):
            front.append(f"model: {_yaml_str(args['model'])}")
        if args.get("tools"):
            front.append("tools: [" + ", ".join(_yaml_str(t) for t in _list(args["tools"])) + "]")
        if args.get("mcp_servers"):
            front.append("mcp-servers: " + json.dumps(args["mcp_servers"]))
        front.append("---")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write("\n".join(front) + "\n\n" + str(args["instructions"]).strip() + "\n")
        return f"wrote {path}\nUse it with copilot_task agent=\"{name}\".", False
    return "error: action must be list, get, create or delete", True


# ---------------------------------------------------------------- copilot CLI passthroughs

def _cli(argv, timeout=120, cwd=None):
    proc = subprocess.run([find_copilot(), *argv], capture_output=True, text=True, timeout=timeout,
                          stdin=subprocess.DEVNULL, cwd=cwd, env=dict(os.environ, NO_COLOR="1"))
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", (proc.stdout + ("\n" + proc.stderr if proc.stderr.strip() else ""))).strip()
    return text or ("(no output)" if proc.returncode == 0 else f"(failed with exit code {proc.returncode})"), proc.returncode != 0


def _project(args, needed=False):
    cwd = os.path.expanduser(args.get("cwd") or "")
    if cwd and not os.path.isdir(cwd):
        raise ValueError(f"cwd does not exist: {cwd}")
    if needed and not cwd:
        raise ValueError("cwd (the project root) is required for this scope")
    return cwd or None


def mcp_tool(args):
    action, name = args.get("action") or "list", args.get("name") or ""
    if action == "list":
        return _cli(["mcp", "list"])
    if not name:
        return "error: name is required", True
    if action in ("get", "remove", "enable", "disable"):
        return _cli(["mcp", action, name])
    if action == "add":
        argv = ["mcp", "add", "--json"]
        for k, v in (args.get("env") or {}).items():
            argv.append(f"--env={k}={v}")
        for k, v in (args.get("headers") or {}).items():
            argv.append(f"--header={k}: {v}")
        if args.get("tools"):
            argv.append("--tools=" + ",".join(_list(args["tools"])))
        if args.get("url"):
            argv += [f"--transport={args.get('transport') or 'http'}", name, args["url"]]
        elif args.get("command"):
            argv += [name, "--", args["command"], *_list(args.get("args"))]
        else:
            return "error: add needs url (remote) or command (local stdio)", True
        return _cli(argv)
    return "error: action must be list, get, add, remove, enable or disable", True


# ---------------------------------------------------------------- models

MODELS_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models-cache.json")
MODELS_TTL = 900
_PROBE_MODEL = "copilot-subagent-model-list-probe"


def _static_models():
    text, _ = _cli(["help", "config"])
    ids, grab = [], False
    for line in text.splitlines():
        if re.match(r"\s*`model`:", line):
            grab = True
        elif grab:
            m = re.match(r'\s*-\s*"([^"]+)"', line)
            if not m:
                break
            ids.append(m.group(1))
    return ids


def fetch_models(refresh=False):
    """The account's live model catalog.

    The CLI has no 'list models' command, but it logs the catalog it fetches at
    debug level. Asking for a model id that cannot exist makes it fetch the
    catalog and stop before any model call, so this costs no premium requests.
    """
    if not refresh:
        try:
            cached = json.load(open(MODELS_CACHE))
            if time.time() - cached["at"] < MODELS_TTL:
                return cached["models"], cached["at"]
        except (OSError, ValueError, KeyError):
            pass
    work = tempfile.mkdtemp(prefix="copilot-models-")
    models = None
    try:
        proc = subprocess.run(
            [find_copilot(), "--prompt=hi", f"--model={_PROBE_MODEL}", "--log-level=all", f"--log-dir={work}",
             "--output-format=json", "--no-auto-update", "--no-custom-instructions", "--disable-builtin-mcps",
             "--no-ask-user"],
            cwd=work, capture_output=True, text=True, timeout=90, stdin=subprocess.DEVNULL)
        for fn in os.listdir(work):
            for line in _read(os.path.join(work, fn)).splitlines():
                if "fetched model catalog" in line and "{" in line:
                    try:
                        models = json.loads(json.loads(line[line.index("{"):])["models"])
                    except (ValueError, KeyError, TypeError):
                        continue
        # The probe leaves an empty failed session behind; remove it.
        for line in proc.stdout.splitlines():
            if '"type":"result"' in line:
                sid = (json.loads(line).get("sessionId") or "")
                if re.fullmatch(r"[0-9a-f-]{36}", sid):
                    shutil.rmtree(os.path.join(COPILOT_HOME, "session-state", sid), ignore_errors=True)
    except Exception:
        pass
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if not models:
        return None, None
    slim = []
    for m in models:
        caps = m.get("capabilities") or {}
        limits, supports = caps.get("limits") or {}, caps.get("supports") or {}
        slim.append({
            "id": m.get("id"), "name": m.get("name"), "vendor": m.get("vendor"),
            "type": caps.get("type"), "picker": bool(m.get("model_picker_enabled")),
            "category": m.get("model_picker_category"), "price": m.get("model_picker_price_category"),
            "preview": bool(m.get("preview")), "policy": (m.get("policy") or {}).get("state"),
            "context": limits.get("max_context_window_tokens"),
            "efforts": supports.get("reasoning_effort") or [], "vision": bool(supports.get("vision")),
        })
    at = time.time()
    try:
        with open(MODELS_CACHE, "w") as fh:
            json.dump({"at": at, "models": slim}, fh)
    except OSError:
        pass
    return slim, at


def selectable(models):
    return [m for m in models if m["picker"] and m["type"] == "chat" and m["policy"] != "disabled"]


def current_default():
    text, err = _cli(["config", "model"])
    return None if err else text.splitlines()[0].strip()


def models_tool(args):
    action = args.get("action") or "list"
    if action == "get_default":
        cur = current_default()
        return (cur or "(not set; Copilot picks its own default)"), False
    models, at = fetch_models(refresh=bool(args.get("refresh")) or action == "refresh")
    if action in ("list", "refresh"):
        cur = current_default()
        if not models:
            ids = _static_models()
            return ("Could not read the live catalog (is Copilot signed in?). CLI's built-in list, which may "
                    "include models this account cannot use:\n" + "\n".join(ids) + f"\n\ndefault: {cur}"), not ids
        shown = [m for m in models if m["type"] == "chat"] if args.get("all") else selectable(models)
        flt = (args.get("filter") or "").lower()
        shown = [m for m in shown if flt in f"{m['id']} {m['name']} {m['vendor']} {m['category']}".lower()]
        rows = []
        for m in sorted(shown, key=lambda m: (str(m["vendor"]), str(m["id"]))):
            bits = [m["id"] + (" *" if m["id"] == cur else ""), str(m["vendor"]), str(m["category"] or "-"),
                    f"price:{m['price'] or '-'}", f"ctx:{(m['context'] or 0) // 1000}k"]
            if m["efforts"]:
                bits.append("effort:" + "/".join(m["efforts"]))
            if m["preview"]:
                bits.append("preview")
            if not m["picker"]:
                bits.append("(not selectable)")
            rows.append("  ".join(bits))
        ok_ids = {m["id"] for m in selectable(models)}
        head = f"{len(rows)} model(s) usable on this account (also: auto). default: {cur or '(unset)'}"
        if cur and cur != "auto" and cur not in ok_ids:
            head += (f"\nWARNING: the saved default '{cur}' is not usable on this account, so runs without a "
                     "model fail. Fix with action=set_default.")
        return head + "\n" + "\n".join(rows) + f"\n(catalog fetched {int(time.time() - at)}s ago)", False
    if action == "set_default":
        model = (args.get("model") or "").strip()
        if not model:
            return "error: model is required", True
        if models and model != "auto" and model not in {m["id"] for m in selectable(models)}:
            return (f"error: '{model}' is not usable on this account. Valid ids: "
                    + ", ".join(sorted(m["id"] for m in selectable(models))) + ", auto"), True
        prev = current_default()
        text, err = _cli(["config", "model", model])
        return (text if err else f"default model set to {model} (was {prev or 'unset'})"), err
    return "error: action must be list, refresh, get_default or set_default", True


# ---------------------------------------------------------------- config / skills / plugins / update

def config_tool(args):
    action, key = args.get("action") or "list", (args.get("key") or "").strip()
    scope = args.get("scope") or "global"
    if scope not in ("global", "repo", "local"):
        return "error: scope must be global, repo or local", True
    flags = [] if scope == "global" else [f"--{scope}"]
    cwd = _project(args, needed=scope != "global")
    if action == "help":
        text, err = _cli(["help", "config"])
        flt = (args.get("filter") or "").lower()
        if flt:  # keep only the setting blocks that mention the filter
            blocks = re.split(r"\n(?=  `)", text)
            text = "\n".join(b for b in blocks if flt in b.lower()) or f"(no setting mentions '{flt}')"
        return text[:20000], err
    if action == "list":
        return _cli(["config", "--list", *flags], cwd=cwd)
    if not key:
        return "error: key is required", True
    if action == "get":
        text, err = _cli(["config", *flags, key], cwd=cwd)
        return (f"({key} is not set)" if err and text.startswith("(failed") else text), False if text.startswith("(failed") else err
    if action == "set":
        if args.get("value") is None:
            return "error: value is required", True
        value = args["value"]
        value = ("true" if value else "false") if isinstance(value, bool) else str(value)
        return _cli(["config", *flags, key, "--", value], cwd=cwd)
    if action == "remove":
        argv = ["config", *flags, "--rm", key]
        if args.get("value") is not None:
            argv += ["--", str(args["value"])]
        return _cli(argv, cwd=cwd)
    return "error: action must be list, get, set, remove or help", True


def skills_tool(args):
    action, cwd = args.get("action") or "list", _project(args)
    if action == "list":
        text, err = _cli(["skill", "list"], cwd=cwd)
        flt = (args.get("filter") or "").lower()
        lines = [(_short(l, 200) if l.startswith(" ") else l) for l in text.splitlines()
                 if not flt or not l.startswith(" ") or flt in l.lower()]
        return "\n".join(lines)[:30000], err
    if action == "add":
        if not args.get("source"):
            return "error: source (SKILL.md path, https URL, or directory) is required", True
        src = args["source"] if "://" in args["source"] else os.path.expanduser(args["source"])
        return _cli(["skill", "add", *(["--project"] if args.get("project") else []), src],
                    cwd=_project(args, needed=bool(args.get("project"))))
    if action in ("remove", "enable", "disable"):
        if not args.get("name"):
            return "error: name is required", True
        return _cli(["skill", action, args["name"]], cwd=cwd)
    return "error: action must be list, add, remove, enable or disable", True


def plugins_tool(args):
    action, name, cwd = args.get("action") or "list", args.get("name") or "", _project(args)
    if action == "list":
        return _cli(["plugin", "list"], cwd=cwd)
    if action == "marketplace_list":
        return _cli(["plugin", "marketplace", "list"])
    if action == "marketplace_update":
        return _cli(["plugin", "marketplace", "update", *([name] if name else [])], timeout=300)
    if action == "update" and not name:
        return _cli(["plugin", "update"], timeout=300)
    if not name:
        return "error: name is required", True
    if action == "install":   # name is plugin@marketplace, owner/repo, owner/repo:path or a git URL
        return _cli(["plugin", "install", name], timeout=300)
    if action in ("uninstall", "update", "enable", "disable"):
        return _cli(["plugin", action, name], timeout=300)
    if action in ("marketplace_add", "marketplace_remove", "marketplace_browse"):
        text, err = _cli(["plugin", "marketplace", action.split("_", 1)[1], name], timeout=300)
        return text[:30000], err
    return ("error: action must be list, install, uninstall, update, enable, disable, marketplace_list, "
            "marketplace_add, marketplace_remove, marketplace_browse or marketplace_update"), True


def update_tool(args):
    action = args.get("action") or "check"
    if action == "check":
        return _cli(["version"], timeout=60)
    if action == "update":
        channel = args.get("channel")
        if channel not in (None, "", "stable", "prerelease"):
            return "error: channel must be stable or prerelease", True
        before, _ = _cli(["--version"])
        text, err = _cli(["update", *([channel] if channel else [])], timeout=600)
        after, _ = _cli(["--version"])
        return f"before: {before.splitlines()[0]}\n{text}\nafter:  {after.splitlines()[0]}", err
    return "error: action must be check or update", True


def workflow_tool(args):
    if not args.get("name"):
        return "error: name is required", True
    argv = ["--experimental", "workflow", "run", args["name"], "--output-format=json"]
    if args.get("args") is not None:
        argv.append("--args=" + (args["args"] if isinstance(args["args"], str) else json.dumps(args["args"])))
    text, err = _cli(argv, timeout=max(10, min(int(args.get("timeout") or 900), 7200)), cwd=_project(args))
    return text[-30000:], err


HELP_TOPICS = ["billing", "commands", "config", "environment", "limits", "logging", "monitoring",
               "permissions", "providers", "sandbox"]


def info_tool(args):
    what, cwd = args.get("what") or "version", _project(args)
    if what == "version":
        return _cli(["--version"])
    if what == "instructions":
        return _cli(["instruction", "list"], cwd=cwd)
    if what == "lsp":
        return _cli(["lsp", "list"], cwd=cwd)
    if what == "help":
        topic = args.get("topic") or ""
        if topic and topic not in HELP_TOPICS:
            return f"error: topic must be one of {HELP_TOPICS}", True
        text, err = _cli(["help", topic] if topic else ["--help"])
        return text[:30000], err
    return "error: what must be version, instructions, lsp or help", True


# ---------------------------------------------------------------- tool schemas

S, B, A = {"type": "string"}, {"type": "boolean"}, {"type": "array", "items": {"type": "string"}}


def _d(schema, desc):
    return dict(schema, description=desc)


TASK_PROPS = {
    "prompt": _d(S, "Self-contained instructions for the Copilot agent. It sees none of this conversation, so include file paths and context."),
    "cwd": _d(S, "Absolute directory the agent works in. File access is limited to it (plus add_dirs) unless allow_all_paths."),
    "access": {"type": "string", "enum": ACCESS, "description": (
        f"Permission preset (default {DEFAULT_ACCESS}). read_only: read/search/web/MCP, no file writes or shell. "
        "edit: can also create and edit files, no shell. full: everything including shell commands. "
        "custom: only what allow_tools grants (anything else that needs approval is refused).")},
    "model": _d(S, "Model id for this run, or auto. Get valid ids from copilot_models. Omit for Copilot's saved default."),
    "reasoning_effort": {"type": "string", "enum": EFFORTS, "description": "Reasoning effort for the model (copilot_models shows what each model supports)."},
    "context": {"type": "string", "enum": ["default", "long_context"], "description": "Context window tier."},
    "agent": _d(S, "Custom agent to run as (see copilot_agents). Omit for the default Copilot agent."),
    "session_id": _d(S, "Resume an earlier Copilot session (id from a previous result or copilot_sessions) and send prompt as the next message."),
    "name": _d(S, "Name for the new session."),
    "mode": {"type": "string", "enum": ["plan", "autopilot"], "description": "plan: produce a plan only. autopilot: keep going autonomously until done."},
    "fleet": _d(B, "Fleet mode: Copilot orchestrates its own parallel subagents for the prompt."),
    "background": _d(B, "Return immediately with a job_id instead of waiting; follow up with copilot_job."),
    "timeout": {"type": "integer", "description": f"Seconds to wait before stopping the agent (default {DEFAULT_TIMEOUT}; ignored when background)."},
    "allow_tools": _d(A, "Extra permission patterns to allow: shell(git:*), shell(npm test), write, write(path), MyMcpServer, MyMcpServer(tool), url(github.com)."),
    "deny_tools": _d(A, "Permission patterns to deny (always win), e.g. shell(git push), shell(rm)."),
    "available_tools": _d(A, "Only these tools are visible to the model (e.g. view, grep, glob, bash, edit, create, web_fetch, task)."),
    "excluded_tools": _d(A, "Hide these tools from the model."),
    "add_dirs": _d(A, "Additional directories the agent may access."),
    "allow_all_paths": _d(B, "Let the agent touch any path on disk."),
    "allow_urls": _d(A, "URLs/domains the agent may fetch."),
    "deny_urls": _d(A, "URLs/domains the agent may not fetch."),
    "allow_all_urls": _d(B, "Allow fetching any URL."),
    "mcp_config": {"type": "object", "description": "Extra MCP servers for this run only: {name: {command, args, env} | {type: 'http', url, headers}}."},
    "disable_mcp_servers": _d(A, "Configured MCP servers to switch off for this run."),
    "enable_mcp_servers": _d(A, "Disabled MCP servers to switch on for this run."),
    "disable_builtin_mcps": _d(B, "Turn off the built-in GitHub MCP servers."),
    "github_mcp_toolsets": _d(A, "Extra GitHub MCP toolsets to enable ('all' for everything)."),
    "plugin_dirs": _d(A, "Local plugin directories to load for this run."),
    "attachments": _d(A, "Files (images, documents) to attach to the prompt."),
    "no_custom_instructions": _d(B, "Ignore AGENTS.md / copilot-instructions.md."),
    "enable_memory": _d(B, "Enable Copilot's memory for this run."),
    "allow_questions": _d(B, "Let the agent use ask_user (off by default; nobody is there to answer)."),
    "max_autopilot_continues": {"type": "integer", "description": "Max autopilot continuation turns (Copilot default 5)."},
    "max_ai_credits": {"type": "number", "description": "Spending cap in AI credits for this session."},
    "share_path": _d(S, "Write the session transcript to this markdown file when done."),
    "disallow_temp_dir": _d(B, "Do not give the agent automatic access to the system temp directory."),
    "secret_env_vars": _d(A, "Environment variable names to strip from the agent's shell/MCP environments and redact from output."),
    "env": {"type": "object", "description": "Extra environment variables for the Copilot process, e.g. BYOK provider settings (see copilot_info what=help topic=providers)."},
    "experimental": _d(B, "Enable Copilot's experimental features for this run."),
}
PARALLEL_PROPS = {k: v for k, v in TASK_PROPS.items() if k != "background"}

TOOLS = [
    {"name": "copilot_task",
     "description": (
         "Spin up a GitHub Copilot CLI agent on a task and return its final answer, tools used, usage and "
         "session id. Runs on the user's Copilot subscription (GPT, Claude, Gemini and other models). Good for "
         "second opinions, code review, codebase search, or delegating implementation. Defaults to read_only "
         "access; set access=edit or full to let it change files or run commands. Use background=true for "
         "long tasks, and session_id to continue a previous agent."),
     "inputSchema": {"type": "object", "properties": TASK_PROPS, "required": ["prompt", "cwd"]}},
    {"name": "copilot_parallel",
     "description": (
         f"Run several Copilot agents at once (up to {MAX_PARALLEL} concurrently) and return every result. Each "
         "task takes the same fields as copilot_task. Do not give two editing tasks the same files."),
     "inputSchema": {"type": "object", "properties": {
         "tasks": {"type": "array", "minItems": 1, "maxItems": 12,
                   "items": {"type": "object", "properties": PARALLEL_PROPS, "required": ["prompt", "cwd"]}},
         "max_concurrency": {"type": "integer", "description": f"Default 4, max {MAX_PARALLEL}."}},
         "required": ["tasks"]}},
    {"name": "copilot_job",
     "description": "Manage background Copilot agents started with copilot_task background=true: list them, check status (partial output so far), wait for one to finish, or stop it.",
     "inputSchema": {"type": "object", "properties": {
         "action": {"type": "string", "enum": ["list", "status", "wait", "stop"]},
         "job_id": S,
         "timeout": {"type": "integer", "description": "For wait: seconds to wait (default 600)."}},
         "required": ["action"]}},
    {"name": "copilot_sessions",
     "description": "List saved Copilot CLI sessions (newest first) or read one session's transcript. Session ids can be passed to copilot_task session_id to resume.",
     "inputSchema": {"type": "object", "properties": {
         "action": {"type": "string", "enum": ["list", "read"]},
         "cwd": _d(S, "list: only sessions under this directory."),
         "limit": {"type": "integer"},
         "session_id": _d(S, "read: session id or 7+ char prefix."),
         "max_chars": {"type": "integer"}},
         "required": ["action"]}},
    {"name": "copilot_agents",
     "description": (
         "Manage Copilot custom agents (reusable personas with their own instructions, model and tool list), "
         "stored as <name>.agent.md in ~/.copilot/agents (scope=user) or <cwd>/.github/agents (scope=project). "
         "Run one with copilot_task agent=<name>."),
     "inputSchema": {"type": "object", "properties": {
         "action": {"type": "string", "enum": ["list", "get", "create", "delete"]},
         "name": S,
         "scope": {"type": "string", "enum": ["user", "project"], "description": "Default user."},
         "cwd": _d(S, "Project root (for scope=project, or to include project agents in list)."),
         "description": _d(S, "create: one line on what the agent is for."),
         "instructions": _d(S, "create: the agent's system prompt (markdown)."),
         "model": _d(S, "create: model the agent uses."),
         "tools": _d(A, "create: tools the agent may use; omit for all."),
         "mcp_servers": {"type": "object", "description": "create: MCP servers private to this agent."},
         "overwrite": B},
         "required": ["action"]}},
    {"name": "copilot_mcp",
     "description": "Manage the MCP servers configured for the Copilot CLI (~/.copilot/mcp-config.json): list, get, add, remove, enable, disable. For a one-off server use copilot_task mcp_config instead.",
     "inputSchema": {"type": "object", "properties": {
         "action": {"type": "string", "enum": ["list", "get", "add", "remove", "enable", "disable"]},
         "name": S,
         "command": _d(S, "add (local stdio): executable."),
         "args": A,
         "env": {"type": "object"},
         "url": _d(S, "add (remote): server URL."),
         "transport": {"type": "string", "enum": ["http", "sse"]},
         "headers": {"type": "object"},
         "tools": _d(A, "add: tool filter; omit for all.")},
         "required": ["action"]}},
    {"name": "copilot_models",
     "description": (
         "See and select Copilot models. list: the models this account can actually use right now (live "
         "catalog, with vendor, tier, price band, context size and supported reasoning efforts; * marks the "
         "saved default). set_default: change the model Copilot uses when a run gives none (validated against "
         "the live list). For one run only, pass model to copilot_task instead."),
     "inputSchema": {"type": "object", "properties": {
         "action": {"type": "string", "enum": ["list", "refresh", "get_default", "set_default"]},
         "model": _d(S, "set_default: model id or auto."),
         "filter": _d(S, "list: only models matching this text (id, vendor or tier)."),
         "all": _d(B, "list: include chat models that exist but are not selectable."),
         "refresh": _d(B, "Bypass the 15-minute catalog cache.")},
         "required": ["action"]}},
    {"name": "copilot_config",
     "description": (
         "Read and change Copilot CLI settings (model, allowedUrls, autoUpdatesChannel, etc.). scope=global is "
         "~/.copilot/settings.json; repo and local are the project's .github/copilot settings (need cwd). "
         "action=help lists every setting and its accepted values."),
     "inputSchema": {"type": "object", "properties": {
         "action": {"type": "string", "enum": ["list", "get", "set", "remove", "help"]},
         "key": _d(S, "Setting key in dot notation, e.g. model or footer.showQuota."),
         "value": {"description": "set: the value (list settings append). remove: optional single list item to remove."},
         "scope": {"type": "string", "enum": ["global", "repo", "local"]},
         "cwd": _d(S, "Project root for scope=repo/local."),
         "filter": _d(S, "help: only settings mentioning this text.")},
         "required": ["action"]}},
    {"name": "copilot_skills",
     "description": "Manage Copilot skills (SKILL.md instructions): list, add from a file / https URL / directory, remove, enable, disable.",
     "inputSchema": {"type": "object", "properties": {
         "action": {"type": "string", "enum": ["list", "add", "remove", "enable", "disable"]},
         "name": _d(S, "remove/enable/disable: skill name (remove also accepts a registered directory)."),
         "source": _d(S, "add: SKILL.md path, https URL, or a directory of skills."),
         "project": _d(B, "add: install into <cwd>/.github/skills instead of the personal directory."),
         "cwd": _d(S, "Project root (to include project skills, or for project=true)."),
         "filter": _d(S, "list: only skills matching this text.")},
         "required": ["action"]}},
    {"name": "copilot_plugins",
     "description": (
         "Manage Copilot plugins (bundles of skills, agents, hooks, MCP and LSP servers) and plugin marketplaces. "
         "install takes plugin@marketplace, owner/repo, owner/repo:path or a git URL. Installs that need a "
         "terminal confirmation cannot be completed from here."),
     "inputSchema": {"type": "object", "properties": {
         "action": {"type": "string", "enum": ["list", "install", "uninstall", "update", "enable", "disable",
                                                "marketplace_list", "marketplace_add", "marketplace_remove",
                                                "marketplace_browse", "marketplace_update"]},
         "name": _d(S, "Plugin name/source, or marketplace name/repo for marketplace_* actions."),
         "cwd": S},
         "required": ["action"]}},
    {"name": "copilot_update",
     "description": "Check whether a newer Copilot CLI is available (check) or download and install it (update). Reports the version before and after.",
     "inputSchema": {"type": "object", "properties": {
         "action": {"type": "string", "enum": ["check", "update"]},
         "channel": {"type": "string", "enum": ["stable", "prerelease"]}},
         "required": ["action"]}},
    {"name": "copilot_workflow",
     "description": "Run a registered Copilot dynamic workflow directly (experimental; needs extensions enabled and usage-based billing).",
     "inputSchema": {"type": "object", "properties": {
         "name": S, "args": {"description": "Workflow arguments (object, or @path to a JSON file)."},
         "cwd": S, "timeout": {"type": "integer"}},
         "required": ["name"]}},
    {"name": "copilot_info",
     "description": "Look up Copilot CLI facts: version, the instruction sources a session in cwd would load, configured language servers, or a help topic (billing, commands, config, environment, limits, logging, monitoring, permissions, providers, sandbox).",
     "inputSchema": {"type": "object", "properties": {
         "what": {"type": "string", "enum": ["version", "instructions", "lsp", "help"]},
         "topic": {"type": "string", "enum": HELP_TOPICS},
         "cwd": S}}},
]


def call_tool(name, args):
    if name == "copilot_task":
        res = run_task(args)
        return format_result(res), not res.get("ok")
    if name == "copilot_parallel":
        tasks = args.get("tasks") or []
        if not 1 <= len(tasks) <= 12:
            return "error: tasks must contain between 1 and 12 items", True
        conc = max(1, min(int(args.get("max_concurrency") or 4), MAX_PARALLEL))
        with ThreadPoolExecutor(max_workers=conc) as pool:
            results = list(pool.map(lambda t: run_task(dict(t, background=False)), tasks))
        body = "\n\n".join(format_result(r, f"Task {i + 1}") for i, r in enumerate(results))
        failed = sum(1 for r in results if not r.get("ok"))
        return f"{len(results) - failed}/{len(results)} tasks succeeded\n\n{body}", failed == len(results)
    handlers = {"copilot_job": job_tool, "copilot_sessions": sessions_tool, "copilot_agents": agents_tool,
                "copilot_mcp": mcp_tool, "copilot_info": info_tool, "copilot_models": models_tool,
                "copilot_config": config_tool, "copilot_skills": skills_tool, "copilot_plugins": plugins_tool,
                "copilot_update": update_tool, "copilot_workflow": workflow_tool}
    if name in handlers:
        return handlers[name](args)
    raise ValueError(f"unknown tool: {name}")


# ---------------------------------------------------------------- MCP stdio plumbing

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
            result = {"content": [{"type": "text", "text": text}], "isError": bool(is_error)}
        elif method == "ping":
            result = {}
        else:
            send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"method not found: {method}"}})
            return
        send({"jsonrpc": "2.0", "id": rid, "result": result})
    except Exception as exc:
        send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32603, "message": str(exc)}})


def main():
    try:
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
    finally:
        with _jobs_lock:
            for job in _jobs.values():
                kill_job(job, "server shut down")


if __name__ == "__main__":
    main()
