# Molina — Desktop Work Pet for Claude Code

## What this is
Molina is a small pixel **axolotl** that lives in her own always-on-top window on the Windows desktop, **outside** Claude. She shows what Claude Code is doing right now (the exact action plus the project stage), alerts the owner when Claude needs them, and can be clicked, dragged and cared for.

- Owner: Deydom (Windows 11, Python 3.12, PowerShell 5.1)
- Project folder: `D:\Claude Code\Molina`
- Source of events: Claude Code **hooks** (terminal CLI and the Code tab of the Claude desktop app)
- Window only. This is **not** a Claude app mod and has no pane inside Claude.

## Hard rules for Claude Code
1. **Work in stages.** Follow `PROGRESS.md` top to bottom, one stage at a time. Finish the stage, run its check, tick it `- [x]`, then send one status line. Do not start the next stage without the owner's OK.
2. **Never break Claude Code.** The hook script must:
   - finish in under 100 ms (measure it),
   - always exit with code 0, even on errors (log the error to `%USERPROFILE%\.molina\hook_errors.log`),
   - never print to stdout (stdout can be read by Claude Code).
3. **Never overwrite `~/.claude/settings.json`.** Back it up first (`settings.json.molina-backup-YYYYMMDD-HHMM`), merge only Molina's entries, and keep every existing hook, mod and setting. The uninstaller removes only Molina's entries.
4. **Check the current hook docs before writing the hook code** (event names, stdin JSON fields, the settings format, whether `async` hooks are supported). Do not trust memory or this file over the docs.
5. **Original art only.** Molina is an original axolotl. Do not draw, trace or imitate Anthropic's Claude Code mascot (the crab) or any other existing character, logo or icon. All art is drawn in code as pixel arrays.
6. **No new dependencies** beyond PySide6 and PyInstaller without asking.
7. **Smallest complete change.** No extra features "for later".
8. If the usage limit is close, stop at a clean point, update `PROGRESS.md` (Now / Next) and say where to resume.

## Architecture
```
Claude Code ──hooks (stdin JSON)──▶ hook\molina_hook.py ──atomic write──▶ %USERPROFILE%\.molina\sessions\<session_id>.json
                                                         └─append──────▶ %USERPROFILE%\.molina\events.jsonl (keep last 500)
Molina window (PySide6) ──polls every 300 ms──▶ sessions\*.json + pet.json
```
- **One file per session** avoids write clashes when several sessions run at once.
- **Atomic writes:** write `*.tmp`, then `os.replace`.
- The window never talks to Claude Code. It only reads the state files.

### Folder layout
```
D:\Claude Code\Molina\
  CLAUDE.md, PROGRESS.md, README.md
  hook\              molina_hook.py (the only file Claude Code runs)
  molina\            app package: __main__, window, sprites, ui (bubble), panel, care, sound, state, startup
  setup\             install.py, uninstall.py, build_exe.py
  tools\             send_fake.py, sprite_preview.py, test_hook.py
  samples\           fake_events\*.json (fixtures), PROGRESS.md sample
```

### Session state file (`sessions\<id>.json`)
| Field | Example |
|---|---|
| `session_id` | `abc123` |
| `project` | `pova-tune-focus` (folder name of `cwd`) |
| `cwd` | `C:\Users\vatha\...\pova-tune-focus` |
| `state` | `thinking` / `reading` / `writing` / `running` / `searching` / `browsing` / `waiting` / `done` / `error` |
| `action` | `Running: adb devices` |
| `stage_index`, `stage_total`, `stage_text` | `4`, `16`, `1.3 Debloat batch 1 (disable) + test` |
| `started`, `last_event` | ISO timestamps |
| `recent` | last 5 actions with times |
| `ended` | true after SessionEnd (remove the file after 2 min) |

### Event → state and action text
| Hook event / tool | State | Action text |
|---|---|---|
| SessionStart | idle | `Session started` |
| UserPromptSubmit | thinking | `Thinking…` |
| PreToolUse Read | reading | `Reading <filename>` |
| PreToolUse Edit / Write / MultiEdit / NotebookEdit | writing | `Editing <filename>` |
| PreToolUse Bash | running | `Running: <command, max 40 chars>` |
| PreToolUse Grep / Glob | searching | `Searching <pattern>` |
| PreToolUse WebFetch / WebSearch | browsing | `Browsing the web` |
| PreToolUse Task / Agent | thinking | `Delegating a sub-task` |
| PreToolUse TodoWrite | thinking | `Updating the plan` |
| PreToolUse mcp__<server>__* | running | `Using <server>` |
| PostToolUse with an error / failure event | error | `<tool> failed` |
| Notification (permission or input needed) | waiting | `Needs you` |
| Stop | done | `Done` |
| SessionEnd | (ended) | — |

### Stage (read by the hook)
- Look for `PROGRESS.md` in the session `cwd`.
- Stage text = the first line matching `- [ ]`. Total = count of `- [ ]` + `- [x]`. Index = ticked count + 1.
- No file, or no checkboxes → no stage line (show the action only).
- Re-read only when the file's modified time changes (cache it in the session file), so the hook stays fast.

## Molina's look: Claude Code dark theme
| Use | Color |
|---|---|
| Outline | `#141413` |
| Body | `#4A4845` |
| Belly / shading | `#6B6862` |
| Gills (accent) | `#D97757` |
| Gill tips / highlights | `#E8A387` |
| Eyes / bubble text | `#F0EEE6` |
| Bubble and panel background | `#1F1E1D`, border `#30302E`, muted text `#9C9A92` |

- Base sprite 32×32 px, shown at 3× (setting: 2×–5×), nearest-neighbour scaling so the pixels stay sharp.
- She needs the dark outline so she stays visible on both light and dark desktops.

### Animations (4–6 frames each, ~8 fps)
| State | Animation |
|---|---|
| idle | Slow breathing, blink every 3–6 s, gills sway gently |
| thinking | Gills ripple in a wave, three dots above her head |
| reading | Holds a tiny open book, eyes move side to side |
| writing | Holds a tiny pencil, quick scribble |
| running | Tail swishes fast, small bubbles rise |
| searching | Peers around with a tiny magnifier |
| browsing | Little globe bubble floats by |
| waiting | Hops, gills flash bright `#E8A387` |
| done | Happy bounce, small sparkle |
| error | Worried face, gills droop |
| asleep | Curled up, `z` bubbles (after 10 min without events, or from the menu) |
| eating / playing | Short one-off animations for pet care |

Also build `tools\sprite_preview.py`, which shows every animation in a grid so the owner can check the art.

## Window behaviour
- Frameless, transparent background, always on top, no taskbar button (tool window), plus a **tray icon** (Show/Hide, Quit).
- **Drag** her anywhere. Save the position in `%USERPROFILE%\.molina\window.json` and restore it on start; if the saved spot is off-screen, use the bottom-right corner.
- **Speech bubble** above her:
  - Line 1: action (`Running: adb devices`)
  - Line 2: stage (`Stage 4/16 · 1.3 Debloat batch 1`), only when a stage exists
  - Shows the **most recently active** session. Fades out 10 s after `done`.
- **Left click → details panel** (dark popup):
  - **Every active session**: project name, state, action, stage bar `4/16`, time running
  - Last 5 actions of the selected session
  - Care stats (level, XP bar, hunger, happiness, energy) + **Feed** and **Play** buttons
- **Right-click menu:** Hide · Mute sounds · Sleep / Wake · Always on top ✓ · Size (2×–5×) · Start with Windows ✓ · Quit
  - "Start with Windows" adds or removes a shortcut in the user's Startup folder.

## Alerts and sound
- Molina's chime is an **original** sound synthesized in code (no downloaded or copied sounds). It's a warm, marimba-like tone: a sine wave plus a soft 4× partial with fast exponential decay, about 35% volume.
  - **Needs you:** rising D4 → A4 → E5 (steps of a fifth)
  - **Done:** falling E5 → A4 → D4
  - **Error:** one soft A3
- Generate the WAV files once into `%USERPROFILE%\.molina\sounds\` with the `wave` + `math` modules and play them with `QSoundEffect`.
- **Waiting:** the hop animation plus the chime. Repeat the chime at most once every 60 s while still waiting. Respect Mute.

## Pet care (stage 10 only)
Stored in `%USERPROFILE%\.molina\pet.json`.
- **XP:** edit/write +2, command +1, finished session (Stop) +10. Level n needs `50 × n` XP. Max level 10.
- **Level accessories:** level 3 tiny scarf, level 5 tiny hat, level 8 glowing gill tips.
- **Hunger** 0–100: drops 5 per hour while the PC is on. **Feed** +30, at most 3 times per hour.
- **Happiness** 0–100: +1 per finished session, −3 per error, **Play** +15 (short play animation).
- **Energy** 0–100: drops while Claude is working, refills while asleep.
- Low stats only change her face (hungry, sad, tired). She never dies, and nothing is lost.

## Installer
- `install.py`: checks Python + PySide6, backs up `settings.json`, adds Molina's hook entries for the events above (command: `python "D:\Claude Code\Molina\hook\molina_hook.py"`), creates `%USERPROFILE%\.molina\`, and prints what it changed.
- `uninstall.py`: removes only Molina's hook entries (matched by the script path) and offers to delete `%USERPROFILE%\.molina\`.
- Package the **window** with PyInstaller (one-folder build) as `Molina.exe`. The hook stays a plain Python script so it starts fast.

---
<sub>Compiled by Claude - Opus 5.5</sub>
