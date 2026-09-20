import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const POKER = resolve(dirname(fileURLToPath(import.meta.url)), '..')

/** Vite bundles every imported stylesheet into one file for the whole app, so
 *  a rule in here applies everywhere whether or not a poker screen is open.
 *  `.card` means a playing card here and a panel everywhere else in Mirth, and
 *  for one deploy every card on the site was 5:7 and tall. */
describe('the poker stylesheet stays inside the poker screen', () => {
  const sheets = readdirSync(POKER).filter((name) => name.endsWith('.css'))

  it('has stylesheets to check', () => {
    expect(sheets.length).toBeGreaterThan(0)
  })

  it.each(sheets)('%s scopes every selector', (name) => {
    const css = readFileSync(join(POKER, name), 'utf-8')
      .replace(/\/\*[\s\S]*?\*\//g, '')
    const unscoped = []
    let depth = 0
    let buffer = ''
    for (const char of css) {
      if (char === '{') {
        if (depth === 0) {
          const selector = buffer.trim()
          const atRule = selector.startsWith('@')
          const inKeyframes = /^\d+%|^(from|to)$/.test(selector)
          if (selector && !atRule && !inKeyframes) {
            for (const one of selector.split(',')) {
              if (one.trim() && !one.trim().startsWith('.poker-root')) unscoped.push(one.trim())
            }
          }
        }
        depth += 1
        buffer = ''
      } else if (char === '}') {
        depth = Math.max(0, depth - 1)
        buffer = ''
      } else if (depth <= 1) {
        buffer += char
      }
    }
    expect(unscoped).toEqual([])
  })
})
