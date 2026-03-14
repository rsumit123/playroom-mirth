import { test, expect } from '@playwright/test'

const API = process.env.VITE_API_BASE || 'http://localhost:8005'
const APP = 'http://localhost:5173'

/**
 * E2E tests for:
 * 1. Room join via share link (/join/:roomCode)
 * 2. Play Again flow (game-end → play again → back to lobby)
 */

test.describe('Join via Link & Play Again', () => {

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

  async function createCharadesRoom(page) {
    await page.getByText(/charades/i).first().click()
    await page.waitForURL('**/play/**', { timeout: 5000 })
    await page.locator('button.btn-primary', { hasText: /create room/i }).click()
    await page.waitForURL('**/lobby', { timeout: 10000 })
    const codeElement = page.locator('.font-display.text-4xl, .font-display.text-5xl').first()
    await codeElement.waitFor({ timeout: 5000 })
    return (await codeElement.textContent()).trim()
  }

  // ============================================================
  // #2: Join via share link
  // ============================================================

  test('join room via /join/:roomCode link', async ({ browser }) => {
    test.setTimeout(30000)

    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const player1 = await ctx1.newPage()
    const player2 = await ctx2.newPage()

    try {
      // Player 1 creates room normally
      await loginAsGuest(player1, 'LinkHost')
      const roomCode = await createCharadesRoom(player1)

      // Player 2 navigates directly to /join/:roomCode (share link)
      await player2.goto(`${APP}/join/${roomCode}`)
      await player2.waitForLoadState('networkidle')

      // Should see invite banner with room code
      await expect(player2.getByText(new RegExp(`invited.*${roomCode}`, 'i')).or(
        player2.getByText(new RegExp(roomCode))
      ).first()).toBeVisible({ timeout: 5000 })

      // Should see Welcome screen (not logged in yet)
      await expect(player2.getByPlaceholder(/enter your name/i)).toBeVisible({ timeout: 5000 })

      // Enter name and click Play as Guest
      await player2.getByPlaceholder(/enter your name/i).fill('LinkJoiner')
      await player2.getByRole('button', { name: /^play as guest$/i }).click()

      // Should auto-join and navigate to lobby
      await player2.waitForURL('**/lobby', { timeout: 15000 })

      // Verify both players visible in lobby
      await expect(player1.getByText('LinkJoiner').first()).toBeVisible({ timeout: 5000 })
      await expect(player2.getByText('LinkHost').first()).toBeVisible({ timeout: 5000 })

      // Room code should match
      await expect(player2.getByText(roomCode).first()).toBeVisible()

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })

  test('join link with already-authenticated user skips welcome', async ({ browser }) => {
    test.setTimeout(30000)

    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const player1 = await ctx1.newPage()
    const player2 = await ctx2.newPage()

    try {
      // Player 1 creates room
      await loginAsGuest(player1, 'LinkHost2')
      const roomCode = await createCharadesRoom(player1)

      // Player 2 logs in first, then uses join link
      await loginAsGuest(player2, 'LinkAuth')
      await player2.goto(`${APP}/join/${roomCode}`)

      // Should auto-join (already authenticated) → directly to lobby
      await player2.waitForURL('**/lobby', { timeout: 15000 })
      await expect(player2.getByText('LinkHost2').first()).toBeVisible({ timeout: 5000 })
      await expect(player2.getByText('LinkAuth').first()).toBeVisible({ timeout: 5000 })

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })

  // ============================================================
  // #3: Play Again flow
  // ============================================================

  test('play again: both vote → back to lobby → can start new game', async ({ browser }) => {
    test.setTimeout(60000)

    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const player1 = await ctx1.newPage()
    const player2 = await ctx2.newPage()

    try {
      // Setup: create room, join, start game
      await loginAsGuest(player1, 'AgainAlice')
      await loginAsGuest(player2, 'AgainBob')

      await player1.getByText(/charades/i).first().click()
      await player1.waitForURL('**/play/**', { timeout: 5000 })
      await player1.locator('button.btn-primary', { hasText: /create room/i }).click()
      await player1.waitForURL('**/lobby', { timeout: 10000 })

      const codeEl = player1.locator('.font-display.text-4xl, .font-display.text-5xl').first()
      const roomCode = (await codeEl.textContent()).trim()

      // Player 2 joins
      await player2.getByText(/charades/i).first().click()
      await player2.waitForURL('**/play/**', { timeout: 5000 })
      await player2.locator('button', { hasText: /^join room$/i }).first().click()
      await player2.getByPlaceholder('ABCDEF').fill(roomCode)
      await player2.locator('button.btn-primary', { hasText: /join room/i }).click()
      await player2.waitForURL('**/lobby', { timeout: 10000 })
      await player1.waitForTimeout(1000)

      // Start game
      await player1.getByRole('button', { name: /start game/i }).click()
      await player1.waitForURL('**/game', { timeout: 10000 })
      await player2.waitForURL('**/game', { timeout: 10000 })

      // Player 2 leaves → game auto-ends for player 1 → game-end screen
      await player2.getByLabel(/leave game/i).click()
      await player2.getByRole('button', { name: /^leave$/i }).click()
      await player2.waitForURL('**/home', { timeout: 10000 })

      // Player 1 should be on game-end
      await player1.waitForURL('**/game-end', { timeout: 15000 })
      await expect(player1.getByText(/game over/i).first()).toBeVisible({ timeout: 5000 })

      // Player 1 clicks "Back to Home" (since player 2 left, play-again won't work)
      await player1.getByRole('button', { name: /back to home/i }).click()
      await player1.waitForURL('**/home', { timeout: 10000 })

      // Verify player 1 is back on home
      expect(player1.url()).toContain('/home')

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })

  test('play again: both players vote and return to lobby', async ({ browser }) => {
    test.setTimeout(120000)

    // Use API to set up a quick game and drive it to game-end
    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const page1 = await ctx1.newPage()
    const page2 = await ctx2.newPage()

    try {
      // Create guests and room via API for speed
      const g1 = await (await page1.request.post(`${API}/guest`, { data: { display_name: 'VoteA' } })).json()
      const g2 = await (await page2.request.post(`${API}/guest`, { data: { display_name: 'VoteB' } })).json()
      const roomData = await (await page1.request.post(`${API}/rooms/guest`, {
        data: { guest_token: g1.guest_token, display_name: 'VoteA', game_type: 'charades', rounds_total: 1, difficulty: 1, turn_seconds: 60 },
      })).json()
      const roomCode = roomData.room.code
      const joinData = await (await page2.request.post(`${API}/rooms/join`, {
        data: { room_code: roomCode, guest_token: g2.guest_token },
      })).json()

      // Set up browser state for both
      for (const [page, gt, name, spid] of [
        [page1, g1.guest_token, 'VoteA', roomData.self_player_id],
        [page2, g2.guest_token, 'VoteB', joinData.self_player_id],
      ]) {
        await page.goto(APP)
        await page.waitForLoadState('networkidle')
        await page.evaluate(({ guestToken, roomCode, selfPlayerId, displayName }) => {
          localStorage.setItem('charade_auth', JSON.stringify({
            token: null, guestToken, guestDisplayName: displayName, user: null,
          }))
          sessionStorage.setItem('charade_room', JSON.stringify({
            code: roomCode, selfPlayerId,
          }))
        }, { guestToken: gt, roomCode, selfPlayerId: spid, displayName: name })
      }

      // Navigate both to lobby
      await page1.goto(`${APP}/lobby`)
      await page1.waitForLoadState('networkidle')
      await page1.waitForTimeout(1500)
      await page2.goto(`${APP}/lobby`)
      await page2.waitForLoadState('networkidle')
      await page2.waitForTimeout(1500)

      // Both vote via REST API (faster than playing a full game)
      await page1.request.post(`${API}/rooms/${roomCode}/play-again?guest_token=${g1.guest_token}`)
      await page2.request.post(`${API}/rooms/${roomCode}/play-again?guest_token=${g2.guest_token}`)

      // Poll to verify ready
      const poll = await (await page1.request.get(`${API}/rooms/${roomCode}/play-again`)).json()
      expect(poll.status).toBe('ready')
      expect(poll.voted).toBe(2)

      // Verify room is back in lobby state
      const room = await (await page1.request.get(`${API}/rooms/${roomCode}?guest_token=${g1.guest_token}`)).json()
      expect(room.room.status).toBe('lobby')
      expect(room.players.length).toBe(2)

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })
})
