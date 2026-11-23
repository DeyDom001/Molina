# Molina

A small pixel axolotl that lives on your Windows desktop and shows what Claude Code is doing right now: the current action, the project stage from `PROGRESS.md`, and a chime when Claude needs you.

## Install

Needs Windows 10/11, [Python 3.10+](https://www.python.org/downloads/) (3.12 tested) and [Claude Code](https://claude.com/claude-code).

1. Get the code: **Code → Download ZIP** on [the GitHub page](https://github.com/DeyDom001/Molina) and unzip it anywhere, or `git clone https://github.com/DeyDom001/Molina.git`. Open PowerShell in that folder.
2. Create the venv (once):
   ```powershell
   py -m venv .venv; .venv\Scripts\python -m pip install PySide6
   ```
3. Add Molina's hooks to Claude Code. This backs up `~\.claude\settings.json` first and keeps all your other hooks. The hook points at this folder, so if you move the folder later, run it again.
   ```powershell
   .venv\Scripts\python setup\install.py
   ```
4. Start her:
   ```powershell
   Start-Process .venv\Scripts\pythonw.exe -ArgumentList '-m','molina'
   ```
   Right-click her → **Start with Windows** to have her start on her own after that.
5. Optional, the `/pet` command in Claude Code (`/pet on`, `off`, `hide`, `show`, `sleep`, `wake`, `mute`, `unmute`, `status`). In a terminal Claude Code session:
   ```
   /plugin install molina-pet --marketplace DeyDom001/Molina
   ```
   Answer `y` to add the marketplace, then pick a scope (user is fine). From a shell, the same is `claude plugin install molina-pet --marketplace DeyDom001/Molina`. In the desktop app: **+** next to the prompt box → **Plugins** → **Add marketplace** `DeyDom001/Molina` → **Add plugin**. `/pet` finds Molina's folder from step 3, so do step 3 first.

Optional exe: `.venv\Scripts\python -m pip install PyInstaller; .venv\Scripts\python setup\build_exe.py` builds `dist\Molina\Molina.exe`. Some antivirus tools (Bitdefender's Advanced Threat Defense, for example) block unsigned PyInstaller exes. Running from source works the same.

New Claude Code sessions (terminal or the desktop app's Code tab) now update her. Claude **Chat** in the desktop app is followed too: while a reply is being written she shows its current step ("Searching the web", "Reading a page", "Thinking…") and then **Done**. Chat has no hooks, so this reads the app window. It only works while the chat is on screen, and an app update may need the labels adjusting in `molina\chat_watch.ps1`.

## Use

| Do this | Gets you |
|---|---|
| Drag her | Moves her. The spot is remembered. |
| Left click | Details: every session, stage bar, time running, last 5 actions, care stats, **Feed** and **Play** |
| Right click | Hide · Mute sounds · Sleep/Wake · Always on top · Size 2×–5× · Start with Windows · Quit |
| Tray icon | Show/Hide, Quit |
| `/pet <cmd>` in Claude Code | Same commands, from the prompt (step 5) |
| `.venv\Scripts\python -m molina <cmd>` | Control her from a shell: `show`, `hide`, `sleep`, `wake`, `mute`, `unmute`, `status`, `quit` |

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

## License

[MIT](LICENSE): free to use, copy, change and share, as long as the copyright notice stays with it.

---
<sub>Built with [Claude Code](https://claude.com/claude-code) · Compiled by Claude - Opus 5.5</sub>
