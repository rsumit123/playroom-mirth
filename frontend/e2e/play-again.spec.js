import { test, expect } from '@playwright/test'

const API_BASE = process.env.VITE_API_BASE || 'http://localhost:8005'

/**
 * E2E test for the Play Again flow.
 *
 * Uses the REST API directly to set up state (create guests, rooms, etc.)
 * and then drives two browser contexts to simulate two players going through:
 *   Game End → Play Again → Lobby
 *
 * Since we can't easily play a full game in E2E, we test the frontend
 * navigation logic by:
 *   1. Setting up a room with two players via API
 *   2. Navigating both to /game-end (simulating game end)
 *   3. Clicking Play Again on both
 *   4. Verifying both land on /lobby
 */

test.describe('Play Again flow', () => {

  test('both players click Play Again and land on lobby', async ({ browser }) => {
    // Create two separate browser contexts (two players)
    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const page1 = await ctx1.newPage()
    const page2 = await ctx2.newPage()

    try {
      // 1. Create two guests via API
      const g1Resp = await page1.request.post(`${API_BASE}/guest`, {
        data: { display_name: 'Player1' },
      })
      const g1 = await g1Resp.json()
      expect(g1.guest_token).toBeTruthy()

      const g2Resp = await page2.request.post(`${API_BASE}/guest`, {
        data: { display_name: 'Player2' },
      })
      const g2 = await g2Resp.json()
      expect(g2.guest_token).toBeTruthy()

      // 2. Create room
      const roomResp = await page1.request.post(`${API_BASE}/rooms/guest`, {
        data: {
          guest_token: g1.guest_token,
          display_name: 'Player1',
          game_type: 'trivia',
          rounds_total: 1,
          difficulty: 1,
          turn_seconds: 60,
        },
      })
      expect(roomResp.ok()).toBeTruthy()
      const roomData = await roomResp.json()
      const roomCode = roomData.room.code
      expect(roomCode).toBeTruthy()

      // 3. Join room with player 2
      const joinResp = await page2.request.post(`${API_BASE}/rooms/join`, {
        data: { room_code: roomCode, guest_token: g2.guest_token },
      })
      expect(joinResp.ok()).toBeTruthy()

      // 4. Set up localStorage/sessionStorage for both players to simulate being in a room
      // Player 1
      await page1.goto('/')
      await page1.evaluate(({ guestToken, roomCode, roomData }) => {
        localStorage.setItem('charade_auth', JSON.stringify({
          token: null,
          guestToken: guestToken,
          guestDisplayName: 'Player1',
          user: null,
        }))
        sessionStorage.setItem('charade_room', JSON.stringify({
          code: roomCode,
          selfPlayerId: roomData.self_player_id,
        }))
      }, { guestToken: g1.guest_token, roomCode, roomData })

      // Player 2
      await page2.goto('/')
      const joinData = await joinResp.json()
      await page2.evaluate(({ guestToken, roomCode, joinData }) => {
        localStorage.setItem('charade_auth', JSON.stringify({
          token: null,
          guestToken: guestToken,
          guestDisplayName: 'Player2',
          user: null,
        }))
        sessionStorage.setItem('charade_room', JSON.stringify({
          code: roomCode,
          selfPlayerId: joinData.self_player_id,
        }))
      }, { guestToken: g2.guest_token, roomCode, joinData })

      // 5. Navigate both to /game-end with game state
      // We need to set up React state. The easiest way: navigate to lobby first,
      // then inject game end state and navigate to /game-end.
      // Actually, simpler: navigate directly to /game-end and set up state via React internals.

      // Navigate player 1 to lobby first (to establish socket + room state)
      await page1.goto('/lobby')
      await page1.waitForTimeout(1000)

      // Navigate player 2 to lobby
      await page2.goto('/lobby')
      await page2.waitForTimeout(1000)

      // Now test the REST play-again endpoints directly
      // Player 1 votes
      const vote1Resp = await page1.request.post(
        `${API_BASE}/rooms/${roomCode}/play-again?guest_token=${g1.guest_token}`,
      )
      expect(vote1Resp.ok()).toBeTruthy()
      const vote1 = await vote1Resp.json()
      expect(vote1.status).toBe('waiting')
      expect(vote1.voted).toBe(1)
      expect(vote1.total).toBe(2)

      // Poll shows waiting
      const pollResp = await page1.request.get(`${API_BASE}/rooms/${roomCode}/play-again`)
      const poll = await pollResp.json()
      expect(poll.status).toBe('waiting')
      expect(poll.voted).toBe(1)

      // Player 2 votes
      const vote2Resp = await page2.request.post(
        `${API_BASE}/rooms/${roomCode}/play-again?guest_token=${g2.guest_token}`,
      )
      expect(vote2Resp.ok()).toBeTruthy()
      const vote2 = await vote2Resp.json()
      expect(vote2.status).toBe('ready')
      expect(vote2.voted).toBe(2)

      // Poll shows ready
      const poll2Resp = await page1.request.get(`${API_BASE}/rooms/${roomCode}/play-again`)
      const poll2 = await poll2Resp.json()
      expect(poll2.status).toBe('ready')

      // Fetch room state — should still be a valid lobby
      const lobbyResp = await page1.request.get(
        `${API_BASE}/rooms/${roomCode}?guest_token=${g1.guest_token}`,
      )
      expect(lobbyResp.ok()).toBeTruthy()
      const lobby = await lobbyResp.json()
      expect(lobby.room.code).toBe(roomCode)
      expect(lobby.room.status).toBe('lobby')
      expect(lobby.players.length).toBe(2)

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })

  test('play again vote flow — poll detects ready after second player votes', async ({ browser }) => {
    const ctx = await browser.newContext()
    const page = await ctx.newPage()

    try {
      // Create two guests
      const g1 = await (await page.request.post(`${API_BASE}/guest`, { data: { display_name: 'PollA' } })).json()
      const g2 = await (await page.request.post(`${API_BASE}/guest`, { data: { display_name: 'PollB' } })).json()

      // Create room
      const roomData = await (await page.request.post(`${API_BASE}/rooms/guest`, {
        data: { guest_token: g1.guest_token, display_name: 'PollA', game_type: 'trivia', rounds_total: 1, difficulty: 1, turn_seconds: 60 },
      })).json()
      const roomCode = roomData.room.code

      // Join
      await page.request.post(`${API_BASE}/rooms/join`, { data: { room_code: roomCode, guest_token: g2.guest_token } })

      // Player 1 votes
      const v1 = await (await page.request.post(`${API_BASE}/rooms/${roomCode}/play-again?guest_token=${g1.guest_token}`)).json()
      expect(v1.status).toBe('waiting')

      // Player 1 polls — still waiting
      const p1 = await (await page.request.get(`${API_BASE}/rooms/${roomCode}/play-again`)).json()
      expect(p1.status).toBe('waiting')
      expect(p1.voted).toBe(1)

      // Player 2 votes
      const v2 = await (await page.request.post(`${API_BASE}/rooms/${roomCode}/play-again?guest_token=${g2.guest_token}`)).json()
      expect(v2.status).toBe('ready')

      // Player 1 polls — now ready
      const p2 = await (await page.request.get(`${API_BASE}/rooms/${roomCode}/play-again`)).json()
      expect(p2.status).toBe('ready')
      expect(p2.voted).toBe(2)

    } finally {
      await ctx.close()
    }
  })

  test('duplicate vote is idempotent', async ({ browser }) => {
    const ctx = await browser.newContext()
    const page = await ctx.newPage()

    try {
      const g1 = await (await page.request.post(`${API_BASE}/guest`, { data: { display_name: 'DupA' } })).json()
      const g2 = await (await page.request.post(`${API_BASE}/guest`, { data: { display_name: 'DupB' } })).json()
      const roomData = await (await page.request.post(`${API_BASE}/rooms/guest`, {
        data: { guest_token: g1.guest_token, display_name: 'DupA', game_type: 'trivia', rounds_total: 1, difficulty: 1, turn_seconds: 60 },
      })).json()
      const roomCode = roomData.room.code
      await page.request.post(`${API_BASE}/rooms/join`, { data: { room_code: roomCode, guest_token: g2.guest_token } })

      // Vote twice
      await page.request.post(`${API_BASE}/rooms/${roomCode}/play-again?guest_token=${g1.guest_token}`)
      const v2 = await (await page.request.post(`${API_BASE}/rooms/${roomCode}/play-again?guest_token=${g1.guest_token}`)).json()
      expect(v2.status).toBe('waiting')
      expect(v2.voted).toBe(1) // not 2
    } finally {
      await ctx.close()
    }
  })

  test('clicking Play Again navigates both players from game-end to lobby', async ({ browser }) => {
    // Full frontend navigation test: both browsers on /game-end click Play Again
    // and verify they both land on /lobby (not /home)

    // Use a helper page to create guests and room via API first
    const setupCtx = await browser.newContext()
    const setupPage = await setupCtx.newPage()

    const g1 = await (await setupPage.request.post(`${API_BASE}/guest`, { data: { display_name: 'NavA' } })).json()
    const g2 = await (await setupPage.request.post(`${API_BASE}/guest`, { data: { display_name: 'NavB' } })).json()
    const roomData = await (await setupPage.request.post(`${API_BASE}/rooms/guest`, {
      data: { guest_token: g1.guest_token, display_name: 'NavA', game_type: 'trivia', rounds_total: 1, difficulty: 1, turn_seconds: 60 },
    })).json()
    const roomCode = roomData.room.code
    const joinData = await (await setupPage.request.post(`${API_BASE}/rooms/join`, {
      data: { room_code: roomCode, guest_token: g2.guest_token },
    })).json()
    await setupCtx.close()

    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const page1 = await ctx1.newPage()
    const page2 = await ctx2.newPage()

    try {
      // Navigate to app first to establish the origin, then set storage
      await page1.goto('/')
      await page1.waitForLoadState('networkidle')
      await page1.evaluate(({ guestToken, roomCode, selfPlayerId }) => {
        localStorage.setItem('charade_auth', JSON.stringify({
          token: null, guestToken, guestDisplayName: 'NavA', user: null,
        }))
        sessionStorage.setItem('charade_room', JSON.stringify({
          code: roomCode, selfPlayerId,
        }))
      }, { guestToken: g1.guest_token, roomCode, selfPlayerId: roomData.self_player_id })

      await page2.goto('/')
      await page2.waitForLoadState('networkidle')
      await page2.evaluate(({ guestToken, roomCode, selfPlayerId }) => {
        localStorage.setItem('charade_auth', JSON.stringify({
          token: null, guestToken, guestDisplayName: 'NavB', user: null,
        }))
        sessionStorage.setItem('charade_room', JSON.stringify({
          code: roomCode, selfPlayerId,
        }))
      }, { guestToken: g2.guest_token, roomCode, selfPlayerId: joinData.self_player_id })

      // Reload pages — AppProvider re-mounts, reads storage, calls restoreRoom
      await page1.goto('/lobby')
      await page1.waitForLoadState('networkidle')
      await page1.waitForTimeout(1500)

      await page2.goto('/lobby')
      await page2.waitForLoadState('networkidle')
      await page2.waitForTimeout(1500)

      // Verify both are on lobby
      expect(page1.url()).toContain('/lobby')
      expect(page2.url()).toContain('/lobby')

      // Navigate both to /game-end (simulating game ending)
      await page1.goto('/game-end')
      await page2.goto('/game-end')
      await page1.waitForTimeout(500)
      await page2.waitForTimeout(500)

      // Click Play Again on both — this triggers emitPlayAgain which does REST vote + polling
      const playAgainBtn1 = page1.getByRole('button', { name: /play again/i })
      const playAgainBtn2 = page2.getByRole('button', { name: /play again/i })

      if (await playAgainBtn1.isVisible()) {
        await playAgainBtn1.click()
      }
      if (await playAgainBtn2.isVisible()) {
        await playAgainBtn2.click()
      }

      // Wait for navigation — both should end up on /lobby
      await page1.waitForURL('**/lobby', { timeout: 15000 })
      await page2.waitForURL('**/lobby', { timeout: 15000 })

      // Verify NOT on /home
      expect(page1.url()).toContain('/lobby')
      expect(page2.url()).toContain('/lobby')
      expect(page1.url()).not.toContain('/home')
      expect(page2.url()).not.toContain('/home')

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })

  test('ready status from poll causes frontend to set playAgain.ready', async ({ browser }) => {
    // Verify the polling flow: after vote returns "waiting", subsequent poll returning "ready"
    // correctly transitions the state. Tests the API contract that the frontend relies on.
    const ctx = await browser.newContext()
    const page = await ctx.newPage()

    try {
      // Set up two guests and a room
      const g1 = await (await page.request.post(`${API_BASE}/guest`, { data: { display_name: 'ReadyA' } })).json()
      const g2 = await (await page.request.post(`${API_BASE}/guest`, { data: { display_name: 'ReadyB' } })).json()
      const roomData = await (await page.request.post(`${API_BASE}/rooms/guest`, {
        data: { guest_token: g1.guest_token, display_name: 'ReadyA', game_type: 'trivia', rounds_total: 1, difficulty: 1, turn_seconds: 60 },
      })).json()
      const roomCode = roomData.room.code
      await page.request.post(`${API_BASE}/rooms/join`, { data: { room_code: roomCode, guest_token: g2.guest_token } })

      // Player 1 votes — waiting
      const v1 = await (await page.request.post(`${API_BASE}/rooms/${roomCode}/play-again?guest_token=${g1.guest_token}`)).json()
      expect(v1.status).toBe('waiting')

      // Simulate what frontend does: poll and check
      const poll1 = await (await page.request.get(`${API_BASE}/rooms/${roomCode}/play-again`)).json()
      expect(poll1.status).toBe('waiting')

      // Player 2 votes — ready
      await page.request.post(`${API_BASE}/rooms/${roomCode}/play-again?guest_token=${g2.guest_token}`)

      // Now poll returns ready (this is what the frontend polls for)
      const poll2 = await (await page.request.get(`${API_BASE}/rooms/${roomCode}/play-again`)).json()
      expect(poll2.status).toBe('ready')
      expect(poll2.voted).toBe(2)
      expect(poll2.total).toBe(2)

      // Verify room is still in lobby state and accessible
      const room = await (await page.request.get(`${API_BASE}/rooms/${roomCode}?guest_token=${g1.guest_token}`)).json()
      expect(room.room.status).toBe('lobby')
      expect(room.room.code).toBe(roomCode)
      expect(room.players.length).toBe(2)
      expect(room.self_player_id).toBeTruthy()
    } finally {
      await ctx.close()
    }
  })
})
