import { expect, test } from 'claude-code/testing'

import { dirFromSettings } from '../hooks/register'

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
