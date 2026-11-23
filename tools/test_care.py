"""Check the pet care rules in a temp folder: python tools/test_care.py"""
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ["MOLINA_HOME"] = tempfile.mkdtemp(prefix="molina_care_")  # before molina reads it
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from molina import care  # noqa: E402


def events(*rows, mode="a"):
    with open(care.EVENTS, mode, encoding="utf-8") as f:
        for e, tool in rows:
            f.write(json.dumps({"event": e, "tool": tool}) + "\n")


care.EVENTS.parent.mkdir(parents=True, exist_ok=True)
events(("PreToolUse", "Edit"), mode="w")  # written before Molina ever ran: not counted
c = care.Care()
events(("PreToolUse", "Edit"), ("PreToolUse", "Write"), ("PreToolUse", "Bash"), ("Stop", ""), ("PostToolUseFailure", "Bash"))
c.update("idle")
assert c.p["xp"] == 2 + 2 + 1 + 10, c.p
assert c.p["happiness"] == 80 + 1 - 3, c.p

events(*[("Stop", "")] * 4)  # +40 -> 55: level 2 needs 50, 5 left over
c.update("idle")
assert (c.p["level"], c.p["xp"]) == (2, 5), c.p

# the hook trimmed the file to its last lines: count only what is new
lines = care.EVENTS.read_text(encoding="utf-8").splitlines()
care.EVENTS.write_text("\n".join(lines[-2:]) + "\n", encoding="utf-8")
events(("PreToolUse", "Edit"))
c.update("idle")
assert (c.p["level"], c.p["xp"]) == (2, 7), c.p

c.add_xp(10 ** 6)
assert c.p["level"] == 10 and c.acc() == "scarf hat glow", c.p

for _ in range(3):
    c.feed()
before = c.p["hunger"]
c.feed()  # a 4th feed within the hour is refused
assert c.p["hunger"] == before and c.feeds_left() == 0, c.p

print("care rules: ALL OK")
