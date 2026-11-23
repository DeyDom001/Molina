import type { EngineInterface, Register } from 'claude-code'

// /pet word -> the command Molina's own control channel takes (`python -m molina <cmd>`).
const ACTIONS: Record<string, string> = {
  on: 'show', show: 'show', hide: 'hide', off: 'quit', quit: 'quit',
  sleep: 'sleep', wake: 'wake', mute: 'mute', unmute: 'unmute', status: 'status',
}
const USAGE = 'Usage: /pet on | off | show | hide | sleep | wake | mute | unmute | status'

/** Molina's folder, found from the hook her installer put in ~/.claude/settings.json. */
export async function molinaDir($: EngineInterface): Promise<string | undefined> {
  const home = await $.env.get('USERPROFILE')
  if (!home) return undefined
  try {
    return dirFromSettings(await $.fs.read(`${home}\\.claude\\settings.json`))
  } catch {
    return undefined
  }
}

/** The folder above `hook\molina_hook.py` in the settings.json text, with Windows slashes. */
export function dirFromSettings(text: string): string | undefined {
  const hook = /"([^"]*?)[\\/]+hook[\\/]+molina_hook\.py\\?"/.exec(text)  // JSON doubles backslashes
  return hook?.[1]?.replace(/\\\\/g, '\\').replace(/\//g, '\\')
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'pet',
      description: 'Control Molina, the desktop pet: on, off, show, hide, sleep, wake, mute, unmute, status',
      argumentHint: 'on|off|show|hide|sleep|wake|mute|unmute|status',
      immediate: true,
    })
    return next(e)
  })

  on('command.run', { command: 'pet' }, async ($, e) => {
    const word = e.args.trim().toLowerCase() || 'status'
    const cmd = ACTIONS[word]
    if (!cmd) return { text: USAGE, isTextDisplayOnly: true }
    const dir = await molinaDir($)
    if (!dir) return { text: 'Molina is not installed: run `setup\\install.py` from her folder first.', isTextDisplayOnly: true }

    const python = `${dir}\\.venv\\Scripts\\python.exe`
    const ran = await $.process.run([python, '-m', 'molina', cmd === 'show' ? 'status' : cmd], { cwd: dir, timeoutMs: 10000 })
    const reply = ran.stdout.trim()
    if (cmd === 'show' && ran.exitCode === 1) {
      // Not running: start her detached through PowerShell, so she outlives this call.
      const q = (s: string) => s.replace(/'/g, "''")
      await $.process.run(['powershell', '-NoProfile', '-Command',
        `Start-Process -FilePath '${q(dir)}\\.venv\\Scripts\\pythonw.exe' -ArgumentList '-m','molina' -WorkingDirectory '${q(dir)}'`])
      return { text: 'Molina is waking up on your desktop.', isTextDisplayOnly: true }
    }
    if (cmd === 'show') {
      const shown = await $.process.run([python, '-m', 'molina', 'show'], { cwd: dir, timeoutMs: 10000 })
      return { text: shown.stdout.trim(), isTextDisplayOnly: true }
    }
    return { text: reply || ran.stderr.trim() || `Molina did not answer (exit ${ran.exitCode}).`, isTextDisplayOnly: true }
  })
}
