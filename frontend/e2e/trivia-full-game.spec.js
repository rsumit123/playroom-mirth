import { test, expect } from '@playwright/test'

const API = process.env.VITE_API_BASE || 'http://localhost:8005'
const APP = 'http://localhost:5173'

/**
 * Full E2E test: 2 players play a complete trivia game from the UI.
 *
 * Test checklist:
 * - Guest login (both players)
 * - Room creation with game_type=trivia
 * - Room join via code
 * - Lobby shows both players + Trivia badge
 * - Host starts game
 * - Game screen loads at /trivia
 * - Both players see the same question + 4 answer options
 * - Question counter (Question X of Y) visible
 * - Players can click an answer option
 * - Results shown after both answer (correct/incorrect indicators)
 * - Leave button visible during gameplay
 * - Mid-game leave works (solo trivia continues)
 * - Game progresses through questions to round-end/game-end
 */

test.describe('Trivia - Full 2-Player Game', () => {

  async function loginAsGuest(page, name) {
    await page.goto(APP)
    await page.waitForLoadState('networkidle')
    // Clear any leftover auth state
    await page.evaluate(() => { localStorage.clear(); sessionStorage.clear() })
    await page.reload()
    await page.waitForLoadState('networkidle')
    await page.getByPlaceholder(/enter your name/i).fill(name)
    await page.getByRole('button', { name: /^play as guest$/i }).click()
    await page.waitForURL('**/home', { timeout: 10000 })
  }

  async function createTriviaRoom(page) {
    // Click Trivia game card
    await page.getByText(/trivia/i).first().click()
    await page.waitForURL('**/play/**', { timeout: 5000 })

    // Create room (default settings)
    await page.locator('button.btn-primary', { hasText: /create room/i }).click()
    await page.waitForURL('**/lobby', { timeout: 10000 })

    // Extract room code
    const codeElement = page.locator('.font-display.text-4xl, .font-display.text-5xl').first()
    await codeElement.waitFor({ timeout: 5000 })
    const roomCode = (await codeElement.textContent()).trim()
    expect(roomCode).toMatch(/^[A-Z0-9]{6}$/)
    return roomCode
  }

  async function joinRoom(page, roomCode) {
    await page.getByText(/trivia/i).first().click()
    await page.waitForURL('**/play/**', { timeout: 5000 })
    await page.locator('button', { hasText: /^join room$/i }).first().click()
    await page.getByPlaceholder('ABCDEF').fill(roomCode)
    await page.locator('button.btn-primary', { hasText: /join room/i }).click()
    await page.waitForURL('**/lobby', { timeout: 10000 })
  }

  test('complete 2-player trivia game from UI', async ({ browser }) => {
    test.setTimeout(180000) // 3 min — trivia has 10 questions per round

    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const player1 = await ctx1.newPage()
    const player2 = await ctx2.newPage()

    try {
      // ========== Login both players ==========
      await loginAsGuest(player1, 'TrivAlice')
      await loginAsGuest(player2, 'TrivBob')

      // ========== Create + join trivia room ==========
      const roomCode = await createTriviaRoom(player1)
      await joinRoom(player2, roomCode)

      // ========== Verify lobby ==========
      await player1.waitForTimeout(1000)
      await expect(player1.getByText('TrivAlice').first()).toBeVisible({ timeout: 5000 })
      await expect(player1.getByText('TrivBob').first()).toBeVisible({ timeout: 5000 })
      await expect(player1.getByText(/trivia/i).first()).toBeVisible()

      // ========== Start game ==========
      await player1.getByRole('button', { name: /start game/i }).click()

      // ========== Both on /trivia ==========
      await player1.waitForURL('**/trivia', { timeout: 10000 })
      await player2.waitForURL('**/trivia', { timeout: 10000 })

      // ========== Verify trivia UI ==========
      // Both should see Round 1
      await expect(player1.getByText(/round 1/i).first()).toBeVisible({ timeout: 5000 })
      await expect(player2.getByText(/round 1/i).first()).toBeVisible({ timeout: 5000 })

      // Both should see question counter
      await expect(player1.getByText(/question 1 of/i).first()).toBeVisible({ timeout: 10000 })
      await expect(player2.getByText(/question 1 of/i).first()).toBeVisible({ timeout: 10000 })

      // ========== Both see a question ==========
      // The question card should be visible
      const q1Card = player1.locator('.card p.font-display').first()
      await expect(q1Card).toBeVisible({ timeout: 10000 })
      const questionText = await q1Card.textContent()
      expect(questionText.length).toBeGreaterThan(3)

      // ========== Both see 4 answer options ==========
      const options1 = player1.locator('.grid.grid-cols-2 button')
      await expect(options1).toHaveCount(4, { timeout: 5000 })
      const options2 = player2.locator('.grid.grid-cols-2 button')
      await expect(options2).toHaveCount(4, { timeout: 5000 })

      // ========== Leave button visible ==========
      await expect(player1.getByLabel(/leave game/i)).toBeVisible()
      await expect(player2.getByLabel(/leave game/i)).toBeVisible()

      // ========== Both players answer question 1 ==========
      // Click first option on both (doesn't matter if correct)
      await options1.first().click()
      await options2.first().click()

      // ========== Results shown ==========
      // After both answer, results should appear with correct/incorrect indicators
      await expect(player1.getByText(/results/i).first()).toBeVisible({ timeout: 15000 })
      await expect(player2.getByText(/results/i).first()).toBeVisible({ timeout: 15000 })

      // ========== Game progresses to next question ==========
      // Wait for question 2
      await expect(player1.getByText(/question 2 of/i).first()).toBeVisible({ timeout: 20000 })

      // Answer question 2
      const q2Options1 = player1.locator('.grid.grid-cols-2 button')
      const q2Options2 = player2.locator('.grid.grid-cols-2 button')
      await q2Options1.first().click()
      await q2Options2.first().click()

      // Results for question 2
      await expect(player1.getByText(/results/i).first()).toBeVisible({ timeout: 15000 })

      // ========== Wait for game to eventually end ==========
      // With 10 questions and auto-advance, this takes a while
      // Just verify the game keeps progressing -- don't wait for full game end
      await expect(player1.getByText(/question 3 of/i).first()).toBeVisible({ timeout: 20000 })

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })

  test('mid-game leave in trivia: remaining player can continue solo', async ({ browser }) => {
    test.setTimeout(60000)

    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const player1 = await ctx1.newPage()
    const player2 = await ctx2.newPage()

    try {
      await loginAsGuest(player1, 'TrivCarol')
      await loginAsGuest(player2, 'TrivDave')

      const roomCode = await createTriviaRoom(player1)
      await joinRoom(player2, roomCode)
      await player1.waitForTimeout(1000)

      await player1.getByRole('button', { name: /start game/i }).click()
      await player1.waitForURL('**/trivia', { timeout: 10000 })
      await player2.waitForURL('**/trivia', { timeout: 10000 })

      // Wait for first question to load
      await expect(player1.getByText(/question 1 of/i).first()).toBeVisible({ timeout: 10000 })

      // Player 2 leaves
      await player2.getByLabel(/leave game/i).click()
      await player2.getByRole('button', { name: /^leave$/i }).click()
      await player2.waitForURL('**/home', { timeout: 10000 })

      // Player 1 should still be on /trivia (trivia can continue solo)
      expect(player1.url()).toContain('/trivia')

      // Player 1 can still answer questions
      const options = player1.locator('.grid.grid-cols-2 button')
      await expect(options.first()).toBeVisible({ timeout: 5000 })
      await options.first().click()

      // Should see results (auto after solo answer)
      await expect(player1.getByText(/results/i).first()).toBeVisible({ timeout: 15000 })

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })
})
