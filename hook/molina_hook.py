"""Molina hook: Claude Code event (stdin JSON) -> ~/.molina/sessions/<id>.json + events.jsonl.

Rules: stdlib only, never print to stdout, always exit 0, log errors to hook_errors.log.
"""
import json
import os
import re
import sys
import time

HOME = os.environ.get("MOLINA_HOME") or os.path.join(os.path.expanduser("~"), ".molina")
SESSIONS = os.path.join(HOME, "sessions")
EVENTS = os.path.join(HOME, "events.jsonl")
NEEDS_YOU = {"permission_prompt", "elicitation_dialog", "elicitation_url_dialog", "agent_needs_input"}
CHECKBOX = re.compile(r"^\s*- \[([ xX])\]\s*(.*)")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def short(text, n):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


def tool_state(name, inp):
    """(state, action) for a PreToolUse event."""
    base = os.path.basename(str(inp.get("file_path") or inp.get("notebook_path") or ""))
    if name == "Read":
        return "reading", f"Reading {base}"
    if name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        return "writing", f"Editing {base}"
    if name in ("Bash", "PowerShell"):
        return "running", f"Running: {short(inp.get('command', ''), 40)}"
    if name in ("Grep", "Glob"):
        return "searching", f"Searching {short(inp.get('pattern', ''), 30)}"
    if name in ("WebFetch", "WebSearch"):
        return "browsing", "Browsing the web"
    if name in ("Task", "Agent"):
        return "thinking", "Delegating a sub-task"
    if name == "TodoWrite":
        return "thinking", "Updating the plan"
    if name.startswith("mcp__"):
        return "running", f"Using {name.split('__')[1]}"
    return "thinking", f"Using {name}"


def stage(cwd, old):
    """Return stage fields from <cwd>/PROGRESS.md, re-reading only when its mtime changes."""
    path = os.path.join(cwd, "PROGRESS.md")
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return {"stage_mtime": None, "stage_index": None, "stage_total": None, "stage_text": None}
    if old.get("stage_mtime") == mtime:
        return {k: old.get(k) for k in ("stage_mtime", "stage_index", "stage_total", "stage_text")}
    done = total = 0
    text = None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = CHECKBOX.match(line)
            if m:
                total += 1
                if m.group(1) == " ":
                    text = text or short(m.group(2), 60)
                else:
                    done += 1
    if not total:
        return {"stage_mtime": mtime, "stage_index": None, "stage_total": None, "stage_text": None}
    return {"stage_mtime": mtime, "stage_index": min(done + 1, total), "stage_total": total, "stage_text": text}


def write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


def append_event(rec):
    with open(EVENTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    if os.path.getsize(EVENTS) > 200_000:  # ~1000+ lines: trim to the last 500
        with open(EVENTS, encoding="utf-8") as f:
            lines = f.readlines()[-500:]
        with open(EVENTS + ".tmp", "w", encoding="utf-8") as f:
            f.writelines(lines)
        os.replace(EVENTS + ".tmp", EVENTS)


def handle(ev):
    sid = re.sub(r"[^\w-]", "_", str(ev.get("session_id") or "unknown"))
    event = ev.get("hook_event_name", "")
    tool = ev.get("tool_name", "")
    cwd = ev.get("cwd") or ""
    path = os.path.join(SESSIONS, sid + ".json")
    os.makedirs(SESSIONS, exist_ok=True)
    try:
        with open(path, encoding="utf-8") as f:
            s = json.load(f)
    except (OSError, ValueError):
        s = {"session_id": sid, "started": now(), "recent": [], "state": "idle", "action": ""}

    new = None  # (state, action)
    if event == "SessionStart":
        new = ("idle", "Session started")
        s["ended"] = False
    elif event == "UserPromptSubmit":
        new = ("thinking", "Thinking…")
    elif event == "PreToolUse":
        new = tool_state(tool, ev.get("tool_input") or {})
    elif event == "PostToolUse":
        if s.get("state") == "waiting":  # permission granted, tool ran
            new = ("thinking", "Thinking…")
    elif event in ("PostToolUseFailure", "StopFailure"):
        if not ev.get("is_interrupt"):
            new = ("error", f"{tool or 'Claude'} failed")
    elif event == "Notification":
        if ev.get("notification_type") in NEEDS_YOU:
            new = ("waiting", "Needs you")
    elif event == "Stop":
        new = ("done", "Done")
    elif event == "SessionEnd":
        s["ended"] = True

    t = now()
    s.update(project=os.path.basename(cwd.rstrip("\\/")) or s.get("project", ""), cwd=cwd or s.get("cwd", ""), last_event=t)
    if new:
        s["state"], s["action"] = new
        s["recent"] = (s.get("recent", []) + [{"time": t, "action": new[1]}])[-5:]
    if cwd:
        s.update(stage(cwd, s))
    write_json(path, s)
    append_event({"time": t, "session_id": sid, "event": event, "tool": tool, "state": s.get("state")})


def main():
    try:
        handle(json.loads(sys.stdin.buffer.read() or b"{}"))
    except Exception as e:
        try:
            tb = e.__traceback__
            while tb.tb_next:  # line where it failed; `traceback` costs ~20 ms to import
                tb = tb.tb_next
            os.makedirs(HOME, exist_ok=True)
            with open(os.path.join(HOME, "hook_errors.log"), "a", encoding="utf-8") as f:
                f.write(f"{now()} line {tb.tb_lineno}: {e!r}\n")
        except Exception:
            pass
    sys.exit(0)


if __name__ == "__main__":
    main()
