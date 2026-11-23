---
name: molina-setup
description: Install, start, control or uninstall Molina, a free pixel-axolotl desktop pet for Windows that shows what Claude Code and Claude Chat are doing right now. Use when the user asks to set up, install, start, fix or remove Molina. Works with Claude Code on Windows only.
---

# Molina setup

Molina is a small pixel axolotl in her own always-on-top window on the Windows desktop. Her speech bubble shows what Claude is doing right now ("Running: npm test", "Searching the web") and the project stage from `PROGRESS.md`. She chimes when Claude needs the user. Source, MIT license: https://github.com/DeyDom001/Molina

## Requirements (check these first, and stop if one is missing)

- **Windows 10 or 11.** She doesn't run on macOS or Linux.
- **Python 3.10 or newer**: `py --version`. If it's missing, send the user to https://www.python.org/downloads/. Don't install Python for them.
- **Claude Code.** Molina reads Claude Code's hooks. Cursor, Copilot and other agents aren't supported.
- **Git**, or the user downloads the ZIP from the GitHub page.
- About 700 MB of disk space for the Python environment (mostly PySide6).

## What installing changes on the computer (tell the user before step 3)

- Adds Molina's hook to 9 events in `~\.claude\settings.json`, after saving a backup named `settings.json.molina-backup-<date>`. Every other hook and setting is kept.
- Creates `%USERPROFILE%\.molina\` for her state, sounds and logs.
- Runs a small window in the background. A hidden PowerShell script reads the Claude desktop app's window (its accessibility labels) so she can follow Claude Chat too. Nothing is sent anywhere.

## Install (one command)

`setup.ps1`, next to this file, does steps 1–4 below: it checks Python, clones the repo, creates the venv, installs PySide6, adds the hooks and starts her. It's safe to run again, and it stops with a clear message if something is missing. Ask the user where to put Molina (default `%USERPROFILE%\Molina`), then:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<this skill's folder>\setup.ps1" -Dir "$env:USERPROFILE\Molina"
```

Add `-NoStart` to install without starting her. Without git, the user downloads the ZIP from the GitHub page and passes its unzipped folder as `-Dir`. Then go on with step 5.

## Install (step by step)

The same steps by hand, if the script can't run. Run these in PowerShell.

1. Get the code:
   ```powershell
   git clone https://github.com/DeyDom001/Molina.git "$env:USERPROFILE\Molina"; cd "$env:USERPROFILE\Molina"
   ```
   Without git: the user downloads the ZIP from the GitHub page (Code → Download ZIP), unzips it, and you `cd` into that folder.
2. Create the Python environment:
   ```powershell
   py -m venv .venv; .venv\Scripts\python -m pip install PySide6
   ```
3. Add the hooks to Claude Code (prints the backup's path and what it added):
   ```powershell
   .venv\Scripts\python setup\install.py
   ```
4. Start her:
   ```powershell
   Start-Process .venv\Scripts\pythonw.exe -ArgumentList '-m','molina'
   ```
5. Tell the user: open a **new** Claude Code session (already-open sessions don't load new hooks). Right-click Molina → **Start with Windows** to have her start on her own.
6. Optional, the `/pet` command. The user types this in a terminal Claude Code session:
   ```
   /plugin install molina-pet --marketplace DeyDom001/Molina
   ```

Check it worked: `.venv\Scripts\python -m molina status` prints a line like `Molina: visible · awake · sound on · level 1 · 0 session(s)`.

## Control her

From her folder: `.venv\Scripts\python -m molina <show|hide|sleep|wake|mute|unmute|status|quit>`. With the plugin: `/pet on|off|hide|show|sleep|wake|mute|unmute|status`. Left-click her for every session and her care stats; right-click for the menu.

## Uninstall

```powershell
.venv\Scripts\python setup\uninstall.py
```
This quits her, removes her Startup shortcut, removes only Molina's hooks (after a backup) and asks before deleting `%USERPROFILE%\.molina\`. Then the user can delete the folder.

## Troubleshooting

- **She doesn't react:** the session was opened before step 3. Open a new one. Check `%USERPROFILE%\.molina\hook_errors.log`.
- **The folder was moved:** run step 3 again; the hook points at the folder it was installed from.
- **Antivirus blocks or quarantines Python files** (seen with Bitdefender's Advanced Threat Defense): the user decides whether to add an exception. Don't change security settings yourself.
- **"Molina could not save … (locked)"** in the log: antivirus is holding her settings file. Her position and pet stats won't save until that's cleared.
- **Claude Chat isn't followed:** it only works in the desktop app, in English, with the Chat tab on screen.
