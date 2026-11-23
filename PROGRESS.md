# Molina — PROGRESS

**Now:** Stage 12 — one day of real use (Code + Chat), then a fix list
**Next:** —

Rules: one stage at a time · run the check · tick it · one status line · wait for the owner's OK.

- [x] 0. Setup: create `D:\Claude Code\Molina` structure, venv, install PySide6 + PyInstaller, `git init`
  - Check: `python -c "import PySide6"` works inside the venv
- [x] 1. Hook script + state files (`hook\molina_hook.py`), tested with fake events only
  - Check: every fixture in `samples\fake_events\` (`python tools\send_fake.py --test`) gives the right state/action/stage; each run < 100 ms; a broken input still exits 0 and logs the error
- [x] 2. Installer + uninstaller (backup + merge), then a real test from the Code tab — installed 2026-11-23, live session file written
  - Check: backup file exists; existing hooks and mods untouched; a real session writes `sessions\<id>.json`; uninstall removes only Molina's entries
- [x] 3. Window: transparent, frameless, always on top, drag, position memory, tray icon
  - Check: drag, restart → same spot; tray Show/Hide/Quit work; no taskbar button
- [x] 4. Molina sprite + palette + idle animation (blink, breathing) + `tools\sprite_preview.py`
  - Check: owner approves the look in the preview at 3× — approved (pink redesign, 2026-11-23)
- [x] 5. All state animations, connected to live state
  - Check: each fake event shows the right animation; asleep after 10 min idle
- [x] 6. Speech bubble: action + stage, most recent session, fade after done
  - Check: matches the live session; no stage line when `PROGRESS.md` is missing
- [x] 7. Details panel (left click): all sessions, stage bars, timers, last 5 actions
  - Check: two Code tab sessions at once both appear correctly — passed live: a Code session and a Chat session shown together (2026-11-23)
- [x] 8. Right-click menu: Hide, Mute, Sleep/Wake, Always on top, Size, Start with Windows, Quit
  - Check: every item works; settings survive a restart
- [x] 9. Alerts: synthesized chimes + waiting hop
  - Check: approval prompt → hop + rising chime; repeat ≤ once per 60 s; Mute silences it
- [x] 10. Pet care: XP, levels, accessories, hunger/happiness/energy, Feed and Play
  - Check: numbers follow the rules in `CLAUDE.md`; state survives a restart
- [x] 11. Packaging: `Molina.exe` (PyInstaller one-folder) + `README.md` (install, use, uninstall)
  - Check: runs on the owner's PC without the venv — owner chose to run from source (`pythonw -m molina`) because Bitdefender ATD blocks Molina.exe (2026-11-23)
- [ ] 12. One day of real use, then a fix list
  - Check: owner signs off

---
<sub>Compiled by Claude - Opus 5.5</sub>
