import { expect, test } from 'claude-code/testing'
import type { EngineInterface } from 'claude-code'

import { dirFromSettings, startIfStopped } from '../hooks/register'

test('finds Molina\'s folder from the hook line the installer writes', async () => {
  const fwd = '{"command": "\\"C:/Python312/python.exe\\" -S \\"D:/Claude Code/Molina/hook/molina_hook.py\\""}'
  expect(dirFromSettings(fwd)).toBe('D:\\Claude Code\\Molina')
  const back = '{"command": "\\"C:\\\\Py\\\\python.exe\\" -S \\"E:\\\\pets\\\\Molina\\\\hook\\\\molina_hook.py\\""}'
  expect(dirFromSettings(back)).toBe('E:\\pets\\Molina')
  expect(dirFromSettings('{"hooks": {}}')).toBeUndefined()
})

test('/pet with an unknown word shows the usage', async $ => {
  const { text } = await $.command.run({ command: 'pet', args: 'dance' })
  expect(text).toContain('Usage: /pet on | off')
})

/** A $ whose process.run answers `status` with the given exit code and records every argv. */
function fakeEngine(statusExit: number) {
  const calls: string[][] = []
  const $ = { process: { run: async (argv: string[]) => {
    calls.push(argv)
    return { exitCode: argv.includes('status') ? statusExit : 0, stdout: '', stderr: '' }
  } } } as unknown as EngineInterface
  return { $, calls }
}

test('starts Molina only when she is not running', async () => {
  const stopped = fakeEngine(1)
  expect(await startIfStopped(stopped.$, 'D:\\Molina')).toBe(true)
  expect(stopped.calls[1][0]).toBe('powershell')
  expect(stopped.calls[1].join(' ')).toContain("'D:\\Molina\\.venv\\Scripts\\pythonw.exe'")

  const running = fakeEngine(0)
  expect(await startIfStopped(running.$, 'D:\\Molina')).toBe(false)
  expect(running.calls).toHaveLength(1)  // hidden stays hidden: no show sent
})
