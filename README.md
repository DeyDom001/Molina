# Molina

A small pixel axolotl that lives on your Windows desktop and shows what Claude Code is doing right now: the current action, the project stage from `PROGRESS.md`, and a chime when Claude needs you.

## Install

Needs Windows, Python 3.12, and this folder at `D:\Claude Code\Molina`.

1. Create the venv (once):
   ```powershell
   py -3.12 -m venv .venv; .venv\Scripts\python -m pip install PySide6 PyInstaller
   ```
2. Add Molina's hooks to Claude Code (backs up `~\.claude\settings.json` first and keeps all your other hooks):
   ```powershell
   .venv\Scripts\python setup\install.py
   ```
3. Start her:
   - from source: `.venv\Scripts\pythonw -m molina`
   - or build the exe: `.venv\Scripts\python setup\build_exe.py`, then run `dist\Molina\Molina.exe`. On the owner's PC, Bitdefender's Advanced Threat Defense blocks the exe even with a folder exception, so Molina runs from source there. It works the same, but keep the `.venv` folder.

New Claude Code sessions (terminal or the desktop app's Code tab) now update her. Claude **Chat** in the desktop app is followed too: while a reply is being written she shows its current step ("Searching the web", "Reading a page", "Thinking…") and then **Done**. Chat has no hooks, so this reads the app window. It only works while the chat is on screen, and an app update may need the labels adjusting in `molina\chat_watch.ps1`.

## Use

| Do this | Gets you |
|---|---|
| Drag her | Moves her. The spot is remembered. |
| Left click | Details: every session, stage bar, time running, last 5 actions, care stats, **Feed** and **Play** |
| Right click | Hide · Mute sounds · Sleep/Wake · Always on top · Size 2×–5× · Start with Windows · Quit |
| Tray icon | Show/Hide, Quit |

- The bubble shows the session that needs you first, otherwise the most recently active one. It fades 10 s after **Done**.
- **Needs you:** she hops and plays a rising chime, repeated at most once a minute while you're still needed.
- She falls asleep after 10 minutes without events.
- Care: XP from edits (+2), commands (+1), and finished replies (+10). Level n needs 50 × n XP. You get a scarf at level 3, a hat at 5, and glowing gill tips at 8. Low hunger, happiness or energy only changes her face; she never dies.

Data lives in `%USERPROFILE%\.molina\`: sessions, `events.jsonl`, `pet.json`, `window.json`, sounds, and `hook_errors.log`.

## Uninstall

```powershell
.venv\Scripts\python setup\uninstall.py
```
This removes only Molina's hook entries (after a backup) and asks before deleting `%USERPROFILE%\.molina\`. Turn off "Start with Windows" first if you turned it on.

## Folders

| Folder | What |
|---|---|
| `hook\` | `molina_hook.py`, the only file Claude Code runs (stdlib only, always exits 0, never prints) |
| `molina\` | the window app |
| `setup\` | install, uninstall, build the exe |
| `tools\` | `send_fake.py` (test without Claude: `--test` checks every fixture), `sprite_preview.py` |
| `samples\` | fake hook events and a sample `PROGRESS.md` |
