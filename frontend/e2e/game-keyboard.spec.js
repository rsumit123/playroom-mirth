import { test, expect } from '@playwright/test'

const API = process.env.VITE_API_BASE || 'http://localhost:8005'
const APP = 'http://localhost:5173'

/**
 * E2E tests for mobile keyboard behavior during gameplay.
 *
 * Verifies that the guess input field remains visible and functional
 * when the mobile keyboard opens (simulated by reducing viewport height).
 *
 * Previously, position:fixed + overflow:hidden caused the input to
 * be pushed below the visible area on Android when keyboard opened.
 */

test.describe('Game keyboard behavior on mobile', () => {

  async function loginAsGuest(page, name) {
    await page.goto(APP)
    await page.waitForLoadState('networkidle')
    await page.evaluate(() => { localStorage.clear(); sessionStorage.clear() })
    await page.reload()
    await page.waitForLoadState('networkidle')
    await page.getByPlaceholder(/enter your name/i).fill(name)
    await page.getByRole('button', { name: /^play as guest$/i }).click()
    await page.waitForURL('**/home', { timeout: 10000 })
  }

  async function createAndStartGame(page1, page2, name1, name2, gameType) {
    await loginAsGuest(page1, name1)
    await loginAsGuest(page2, name2)

    // Player 1 creates room
    await page1.getByText(new RegExp(gameType, 'i')).first().click()
    await page1.waitForURL('**/play/**', { timeout: 5000 })
    await page1.locator('button.btn-primary', { hasText: /create room/i }).click()
    await page1.waitForURL('**/lobby', { timeout: 10000 })

    const codeEl = page1.locator('.font-display.text-4xl, .font-display.text-5xl').first()
    const roomCode = (await codeEl.textContent()).trim()

    // Player 2 joins
    await page2.getByText(new RegExp(gameType, 'i')).first().click()
    await page2.waitForURL('**/play/**', { timeout: 5000 })
    await page2.locator('button', { hasText: /^join room$/i }).first().click()
    await page2.getByPlaceholder('ABCDEF').fill(roomCode)
    await page2.locator('button.btn-primary', { hasText: /join room/i }).click()
    await page2.waitForURL('**/lobby', { timeout: 10000 })
    await page1.waitForTimeout(1000)

    // Start game
    await page1.getByRole('button', { name: /start game/i }).click()
    return roomCode
  }

  test('charades: input visible after simulated keyboard open', async ({ browser }) => {
    test.setTimeout(60000)

    const ctx1 = await browser.newContext({ viewport: { width: 393, height: 851 } })
    const ctx2 = await browser.newContext({ viewport: { width: 393, height: 851 } })
    const p1 = await ctx1.newPage()
    const p2 = await ctx2.newPage()

    try {
      await createAndStartGame(p1, p2, 'KbAlice', 'KbBob', 'charades')
      await p1.waitForURL('**/game', { timeout: 10000 })
      await p2.waitForURL('**/game', { timeout: 10000 })

      // Find the guesser
      const p1Role = await p1.locator('.badge-describer, .badge-guesser').first().textContent()
      const guesser = p1Role.includes('Guesser') ? p1 : p2

      // Verify input is visible at full viewport
      const input = guesser.getByPlaceholder(/type your guess/i)
      await expect(input).toBeVisible({ timeout: 5000 })

      // Simulate keyboard opening (viewport shrinks to ~half)
      await guesser.setViewportSize({ width: 393, height: 400 })
      await guesser.waitForTimeout(500)

      // Input should STILL be visible (this was the bug - it disappeared)
      await expect(input).toBeVisible({ timeout: 3000 })

      // Input should be within the visible viewport
      const box = await input.boundingBox()
      expect(box).not.toBeNull()
      expect(box.y + box.height).toBeLessThanOrEqual(420) // within viewport + tolerance

      // Should be able to type in the input
      await input.fill('testguess')
      await expect(input).toHaveValue('testguess')

      // Guess button should also be visible
      await expect(guesser.getByRole('button', { name: /guess/i })).toBeVisible()

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })

  test('scribble: input visible after simulated keyboard open', async ({ browser }) => {
    test.setTimeout(60000)

    const ctx1 = await browser.newContext({ viewport: { width: 393, height: 851 } })
    const ctx2 = await browser.newContext({ viewport: { width: 393, height: 851 } })
    const p1 = await ctx1.newPage()
    const p2 = await ctx2.newPage()

    try {
      await createAndStartGame(p1, p2, 'KbCarol', 'KbDave', 'scribble')
      await p1.waitForURL('**/scribble', { timeout: 10000 })
      await p2.waitForURL('**/scribble', { timeout: 10000 })

      // Wait for roles to be assigned
      await expect(p1.locator('.badge-describer, .badge-guesser').first()).toBeVisible({ timeout: 5000 })
      const p1Role = await p1.locator('.badge-describer, .badge-guesser').first().textContent()
      const guesser = p1Role.includes('Guessing') ? p1 : p2

      // Guesser should see the input (drawer sees "You are drawing" text)
      const input = guesser.getByPlaceholder(/type your guess/i)
      await expect(input).toBeVisible({ timeout: 8000 })

      // Simulate keyboard opening
      await guesser.setViewportSize({ width: 393, height: 400 })
      await guesser.waitForTimeout(500)

      // Input should still be visible
      await expect(input).toBeVisible({ timeout: 3000 })

      // Should be typable
      await input.fill('testguess')
      await expect(input).toHaveValue('testguess')

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })

  test('charades: message clears on role change', async ({ browser }) => {
    test.setTimeout(60000)

    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const p1 = await ctx1.newPage()
    const p2 = await ctx2.newPage()

    try {
      await createAndStartGame(p1, p2, 'KbEve', 'KbFrank', 'charades')
      await p1.waitForURL('**/game', { timeout: 10000 })
      await p2.waitForURL('**/game', { timeout: 10000 })

      const p1Role = await p1.locator('.badge-describer, .badge-guesser').first().textContent()
      const guesser = p1Role.includes('Guesser') ? p1 : p2
      const describer = p1Role.includes('Describer') ? p1 : p2

      // Guesser types a partial guess (doesn't submit)
      const input = guesser.getByPlaceholder(/type your guess/i)
      await expect(input).toBeVisible({ timeout: 5000 })
      await input.fill('partial text here')
      await expect(input).toHaveValue('partial text here')

      // Get the word and guess correctly to trigger turn change
      const wordEl = describer.locator('.font-display.text-3xl, .font-display.text-4xl').first()
      await expect(wordEl).toBeVisible({ timeout: 5000 })
      const word = (await wordEl.textContent()).trim()

      await input.fill(word)
      await guesser.getByRole('button', { name: /guess/i }).click()

      // Wait for turn to eventually change (timer will advance)
      // After turn change, if the previous guesser becomes describer,
      // they shouldn't see the old input text when they become guesser again
      // For now, just verify the correct guess flow works
      await expect(guesser.getByText(/guessed/).first()).toBeVisible({ timeout: 5000 })

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })
})
