"""Send fake Claude Code events to the hook, or test them all.

  python tools/send_fake.py waiting            # send one fixture to the real ~/.molina
  python tools/send_fake.py read --session s2  # as another session
  python tools/send_fake.py --test             # check every fixture in a temp folder
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "hook" / "molina_hook.py"
FIXTURES = ROOT / "samples" / "fake_events"


def load(name, session=None):
    text = (FIXTURES / f"{name}.json").read_text(encoding="utf-8")
    text = text.replace("{project}", str(ROOT / "samples" / "project").replace("\\", "\\\\"))
    text = text.replace("{samples}", str(ROOT / "samples").replace("\\", "\\\\"))
    fx = json.loads(text)
    if session:
        fx["event"]["session_id"] = session
    return fx


def run(stdin, env=None):
    """Run the hook; return (exit code, stdout, ms)."""
    t = time.perf_counter()
    p = subprocess.run([sys.executable, "-S", str(HOOK)], input=stdin, capture_output=True, env=env)
    return p.returncode, p.stdout, (time.perf_counter() - t) * 1000


def test():
    home = tempfile.mkdtemp(prefix="molina_test_")
    env = {**os.environ, "MOLINA_HOME": home}
    fails, worst = 0, 0.0
    order = ["session_start"] + sorted(p.stem for p in FIXTURES.glob("*.json") if p.stem not in ("session_start", "session_end")) + ["session_end"]
    for name in order:
        fx = load(name)
        code, out, ms = run(json.dumps(fx["event"]).encode(), env)
        worst = max(worst, ms)
        s = json.loads((Path(home) / "sessions" / f"{fx['event']['session_id']}.json").read_text(encoding="utf-8"))
        expect = dict(fx["expect"])
        if fx["event"]["session_id"] == "fake1" and name != "session_end":
            expect.update(stage_index=4, stage_total=5, stage_text="1.4 Debloat batch 2 (disable) + test")
        bad = {k: (s.get(k), v) for k, v in expect.items() if s.get(k) != v}
        if code or out or bad:
            fails += 1
        print(f"{'FAIL' if code or out or bad else 'ok  '} {name:14} {ms:5.0f} ms {bad or ''}")
    # broken input: must exit 0, print nothing, and log the error
    code, out, ms = run(b"{not json", env)
    logged = (Path(home) / "hook_errors.log").exists()
    ok = code == 0 and not out and logged
    fails += not ok
    print(f"{'ok  ' if ok else 'FAIL'} broken_input   {ms:5.0f} ms exit={code} logged={logged}")
    lines = (Path(home) / "events.jsonl").read_text(encoding="utf-8").splitlines()
    print(f"events.jsonl: {len(lines)} lines, slowest run {worst:.0f} ms (includes Python start-up)")
    print("ALL OK" if not fails else f"{fails} FAILED")
    shutil.rmtree(home, ignore_errors=True)
    return 1 if fails else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__ + "\nFixtures: " + ", ".join(sorted(p.stem for p in FIXTURES.glob("*.json"))))
    elif args[0] == "--test":
        sys.exit(test())
    else:
        session = args[args.index("--session") + 1] if "--session" in args else None
        fx = load(args[0], session)
        code, _, ms = run(json.dumps(fx["event"]).encode())
        print(f"sent {args[0]} ({fx['event']['hook_event_name']}) exit={code} {ms:.0f} ms")
