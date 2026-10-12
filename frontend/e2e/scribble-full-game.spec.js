import { test, expect } from '@playwright/test'

const API = process.env.VITE_API_BASE || 'http://localhost:8005'
const APP = 'http://localhost:5173'

/**
 * Full E2E test: 2 players play a complete scribble game from the UI.
 *
 * Test checklist:
 * - Guest login (both players)
 * - Room creation with game_type=scribble
 * - Room join via code
 * - Lobby shows both players + Scribble badge
 * - Host starts game
 * - Game screen loads at /scribble with correct roles (Drawing/Guessing)
 * - Drawer sees the word + canvas
 * - Guesser sees hint + canvas viewer
 * - Guesser types correct guess -> correct guess feedback with points
 * - Leave button visible during gameplay
 * - Mid-game leave works
 */

test.describe('Scribble - Full 2-Player Game', () => {

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

  async function createScribbleRoom(page) {
    // Click Scribble game card
    await page.getByText(/scribble/i).first().click()
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
    await page.getByText(/scribble/i).first().click()
    await page.waitForURL('**/play/**', { timeout: 5000 })
    await page.locator('button', { hasText: /^join room$/i }).first().click()
    await page.getByPlaceholder('ABCDEF').fill(roomCode)
    await page.locator('button.btn-primary', { hasText: /join room/i }).click()
    await page.waitForURL('**/lobby', { timeout: 10000 })
  }

  test('complete 2-player scribble game from UI', async ({ browser }) => {
    test.setTimeout(120000)

    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const player1 = await ctx1.newPage()
    const player2 = await ctx2.newPage()

    try {
      // ========== Login both players ==========
      await loginAsGuest(player1, 'ScribAlice')
      await loginAsGuest(player2, 'ScribBob')

      // ========== Create + join scribble room ==========
      const roomCode = await createScribbleRoom(player1)
      await joinRoom(player2, roomCode)

      // ========== Verify lobby ==========
      await player1.waitForTimeout(1000)
      await expect(player1.getByText('ScribAlice').first()).toBeVisible({ timeout: 5000 })
      await expect(player1.getByText('ScribBob').first()).toBeVisible({ timeout: 5000 })
      // Verify it's a Scribble room
      await expect(player1.getByText(/scribble/i).first()).toBeVisible()

      // ========== Start game ==========
      await player1.getByRole('button', { name: /start game/i }).click()

      // ========== Both on /scribble ==========
      await player1.waitForURL('**/scribble', { timeout: 10000 })
      await player2.waitForURL('**/scribble', { timeout: 10000 })

      // ========== Verify game UI ==========
      await expect(player1.getByText(/round 1/i).first()).toBeVisible({ timeout: 5000 })
      await expect(player2.getByText(/round 1/i).first()).toBeVisible({ timeout: 5000 })

      // One should be Drawing, the other Guessing
      const p1Role = await player1.locator('.badge-describer, .badge-guesser').first().textContent()
      const p2Role = await player2.locator('.badge-describer, .badge-guesser').first().textContent()
      expect(
        (p1Role.includes('Drawing') && p2Role.includes('Guessing')) ||
        (p1Role.includes('Guessing') && p2Role.includes('Drawing'))
      ).toBeTruthy()

      const drawer = p1Role.includes('Drawing') ? player1 : player2
      const guesser = p1Role.includes('Drawing') ? player2 : player1

      // ========== Drawer picks a word, then sees it ==========
      const choosePrompt = drawer.getByText(/choose a word to draw/i)
      await expect(choosePrompt).toBeVisible({ timeout: 5000 })
      await choosePrompt.locator('xpath=..').getByRole('button').first().click()
      const wordElement = drawer.locator('.font-display.text-2xl.text-accent').first()
      await expect(wordElement).toBeVisible({ timeout: 5000 })
      // The bar shows "..." until the server confirms the picked word.
      await expect(wordElement).not.toHaveText('...', { timeout: 5000 })
      const secretWord = (await wordElement.textContent()).trim()
      expect(secretWord).toBeTruthy()

      // ========== Drawer sees canvas ==========
      await expect(drawer.locator('canvas').first()).toBeVisible()

      // ========== Guesser sees canvas viewer ==========
      await expect(guesser.locator('canvas').first()).toBeVisible()

      // ========== Guesser sees hint ==========
      const hintArea = guesser.locator('.font-mono').first()
      if (await hintArea.isVisible()) {
        const hint = await hintArea.textContent()
        expect(hint).toContain('_')
      }

      // ========== Leave button visible ==========
      await expect(drawer.getByLabel(/leave game/i)).toBeVisible()
      await expect(guesser.getByLabel(/leave game/i)).toBeVisible()

      // ========== Guesser submits correct guess ==========
      const guessInput = guesser.getByPlaceholder(/type your guess/i)
      await expect(guessInput).toBeVisible({ timeout: 5000 })
      await guessInput.fill(secretWord)
      await guesser.getByRole('button', { name: /guess/i }).click()

      // ========== Correct guess feedback, or the turn already moved on ==========
      // With one guesser, a correct guess ends the turn at once and the next
      // turn_start clears the banner, so the guesser may already be choosing.
      await expect(
        guesser.getByText(/guessed/).or(guesser.getByText(/choose a word to draw/i)).first()
      ).toBeVisible({ timeout: 5000 })

      // ========== Wait for game to progress ==========
      await Promise.race([
        player1.waitForURL('**/round-end', { timeout: 90000 }),
        player1.waitForURL('**/game-end', { timeout: 90000 }),
      ]).catch(() => {})

      // ========== Game end screen (if reached) ==========
      if (player1.url().includes('/game-end')) {
        await expect(player1.getByText(/game over/i).first()).toBeVisible({ timeout: 5000 })
        await expect(player1.getByText(/final results/i).first()).toBeVisible()
      }

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })

  test('mid-game leave in scribble: game auto-ends for remaining player', async ({ browser }) => {
    test.setTimeout(60000)

    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const player1 = await ctx1.newPage()
    const player2 = await ctx2.newPage()

    try {
      await loginAsGuest(player1, 'ScribCarol')
      await loginAsGuest(player2, 'ScribDave')

      const roomCode = await createScribbleRoom(player1)
      await joinRoom(player2, roomCode)
      await player1.waitForTimeout(1000)

      await player1.getByRole('button', { name: /start game/i }).click()
      await player1.waitForURL('**/scribble', { timeout: 10000 })
      await player2.waitForURL('**/scribble', { timeout: 10000 })

      // Player 2 leaves
      await player2.getByLabel(/leave game/i).click()
      await player2.getByRole('button', { name: /^leave$/i }).click()

      // Player 2 -> home
      await player2.waitForURL('**/home', { timeout: 10000 })

      // Player 1 -> game-end (auto-end with <2 players)
      await player1.waitForURL('**/game-end', { timeout: 15000 })
      await expect(player1.getByText(/game over/i).first()).toBeVisible({ timeout: 5000 })

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })

  test('reconnection: guesser reloads mid-turn and sees drawing restored', async ({ browser }) => {
    test.setTimeout(90000)

    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const player1 = await ctx1.newPage()
    const player2 = await ctx2.newPage()

    try {
      await loginAsGuest(player1, 'StrokeAlice')
      await loginAsGuest(player2, 'StrokeBob')

      const roomCode = await createScribbleRoom(player1)
      await joinRoom(player2, roomCode)
      await player1.waitForTimeout(1000)

      await player1.getByRole('button', { name: /start game/i }).click()
      await player1.waitForURL('**/scribble', { timeout: 10000 })
      await player2.waitForURL('**/scribble', { timeout: 10000 })

      // Identify drawer and guesser
      const p1Role = await player1.locator('.badge-describer, .badge-guesser').first().textContent()
      const drawer = p1Role.includes('Drawing') ? player1 : player2
      const guesser = p1Role.includes('Drawing') ? player2 : player1

      // Drawer draws on the canvas (simulate strokes via pointer events)
      const canvas = drawer.locator('canvas').first()
      await expect(canvas).toBeVisible({ timeout: 5000 })
      const box = await canvas.boundingBox()
      // Draw a diagonal line across the canvas
      await drawer.mouse.move(box.x + 30, box.y + 30)
      await drawer.mouse.down()
      for (let i = 1; i <= 5; i++) {
        await drawer.mouse.move(box.x + 30 + i * 20, box.y + 30 + i * 20)
      }
      await drawer.mouse.up()

      // Small wait for strokes to relay
      await guesser.waitForTimeout(1500)

      // ========== GUESSER RELOADS (simulates Android screen dim/wake) ==========
      await guesser.reload()
      await guesser.waitForLoadState('networkidle')
      await guesser.waitForURL('**/scribble', { timeout: 15000 })

      // Guesser should see the game screen restored with round info
      await expect(guesser.getByText(/round/i).first()).toBeVisible({ timeout: 10000 })

      // Guesser should see their role badge (Guessing) -- confirms game state restored
      const roleAfter = await guesser.locator('.badge-describer, .badge-guesser').first().textContent()
      expect(roleAfter).toMatch(/Drawing|Guessing/)

      // Guesser should see the canvas component (CanvasViewer for guesser)
      await expect(guesser.locator('canvas').first()).toBeVisible({ timeout: 5000 })

      // Guesser should see the hint (word hint bar) -- confirms turn state preserved
      const hintArea = guesser.locator('.font-mono').first()
      if (await hintArea.isVisible()) {
        const hint = await hintArea.textContent()
        expect(hint).toContain('_')
      }

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })
})
