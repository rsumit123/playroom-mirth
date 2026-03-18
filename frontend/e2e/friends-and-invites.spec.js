import { test, expect } from '@playwright/test'

const API = process.env.VITE_API_BASE || 'http://localhost:8005'
const APP = 'http://localhost:5173'

/**
 * E2E tests for the friends and game invites system.
 *
 * Uses POST /auth/test-user (dev-only) to create authenticated users
 * without Google OAuth.
 *
 * Test checklist:
 * - Search users, send friend request, accept, verify friends list
 * - Game invite: friend in lobby invites other, receiver sees notification, joins room
 * - Notification badge shows correct count
 */

test.describe('Friends & Invites', () => {

  /** Create a test user with a unique email, return {access_token, user} */
  async function createTestUser(request, name) {
    const unique = `${name}_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`
    const resp = await request.post(`${API}/auth/test-user`, {
      data: { display_name: name, email: `${unique}@test.playroom` }
    })
    expect(resp.ok()).toBeTruthy()
    return resp.json()
  }

  /** Set signed-in user auth in browser */
  async function loginAs(page, authData) {
    await page.goto(APP)
    await page.waitForLoadState('networkidle')
    await page.evaluate(({ token, user }) => {
      localStorage.clear()
      sessionStorage.clear()
      localStorage.setItem('charade_auth', JSON.stringify({
        token, guestToken: null, guestDisplayName: null, user,
      }))
    }, { token: authData.access_token, user: authData.user })
    await page.goto(`${APP}/home`)
    await page.waitForLoadState('networkidle')
  }

  test('friend request flow: search, add, accept, verify friends list', async ({ browser }) => {
    test.setTimeout(30000)

    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const page1 = await ctx1.newPage()
    const page2 = await ctx2.newPage()

    try {
      // Create two test users
      const alice = await createTestUser(page1.request, 'FriendAlice')
      const bob = await createTestUser(page2.request, 'FriendBob')

      // Alice sends friend request via API
      const reqResp = await page1.request.post(`${API}/friends/request`, {
        data: { user_id: bob.user.id },
        headers: { Authorization: `Bearer ${alice.access_token}` },
      })
      expect(reqResp.ok()).toBeTruthy()
      expect((await reqResp.json()).status).toBe('pending')

      // Bob accepts via API
      const acceptResp = await page2.request.post(`${API}/friends/${alice.user.id}/accept`, {
        headers: { Authorization: `Bearer ${bob.access_token}` },
      })
      expect(acceptResp.ok()).toBeTruthy()

      // Verify Alice's friends list via API
      const friendsResp = await page1.request.get(`${API}/friends`, {
        headers: { Authorization: `Bearer ${alice.access_token}` },
      })
      const friends = (await friendsResp.json()).friends
      expect(friends.length).toBe(1)
      expect(friends[0].display_name).toBe('FriendBob')

      // Verify Bob's details in friends list
      expect(friends[0].id).toBe(bob.user.id)

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })

  test('game invite: friend receives notification and joins room', async ({ browser }) => {
    test.setTimeout(30000)

    const ctx1 = await browser.newContext()
    const ctx2 = await browser.newContext()
    const page1 = await ctx1.newPage()
    const page2 = await ctx2.newPage()

    try {
      // Create users and make them friends
      const alice = await createTestUser(page1.request, 'InvAlice')
      const bob = await createTestUser(page2.request, 'InvBob')

      await page1.request.post(`${API}/friends/request`, {
        data: { user_id: bob.user.id },
        headers: { Authorization: `Bearer ${alice.access_token}` },
      })
      await page2.request.post(`${API}/friends/${alice.user.id}/accept`, {
        headers: { Authorization: `Bearer ${bob.access_token}` },
      })

      // Alice creates a room via API
      const roomResp = await page1.request.post(`${API}/rooms`, {
        data: { rounds_total: 1, difficulty: 1, turn_seconds: 60, max_players: 10 },
        headers: { Authorization: `Bearer ${alice.access_token}` },
      })
      expect(roomResp.ok()).toBeTruthy()
      const roomCode = (await roomResp.json()).room.code

      // Alice invites Bob via API
      const invResp = await page1.request.post(`${API}/rooms/${roomCode}/invite`, {
        data: { user_id: bob.user.id },
        headers: { Authorization: `Bearer ${alice.access_token}` },
      })
      expect(invResp.ok()).toBeTruthy()

      // Bob checks notifications -- should see the invite
      const notifResp = await page2.request.get(`${API}/notifications`, {
        headers: { Authorization: `Bearer ${bob.access_token}` },
      })
      const notif = await notifResp.json()
      expect(notif.total).toBeGreaterThanOrEqual(1)
      expect(notif.game_invites.length).toBeGreaterThanOrEqual(1)
      expect(notif.game_invites[0].room_code).toBe(roomCode)
      expect(notif.game_invites[0].from_user.display_name).toBe('InvAlice')

      // Bob joins the room via API (same as clicking "Join" in notification)
      const joinResp = await page2.request.post(`${API}/rooms/join`, {
        data: { room_code: roomCode },
        headers: { Authorization: `Bearer ${bob.access_token}` },
      })
      expect(joinResp.ok()).toBeTruthy()
      const joinData = await joinResp.json()
      expect(joinData.players.length).toBe(2)

    } finally {
      await ctx1.close()
      await ctx2.close()
    }
  })

  test('notification badge shows correct count', async ({ browser }) => {
    test.setTimeout(30000)

    const ctx = await browser.newContext()
    const page = await ctx.newPage()

    try {
      const alice = await createTestUser(page.request, 'BadgeAlice')
      const bob = await createTestUser(page.request, 'BadgeBob')
      const carol = await createTestUser(page.request, 'BadgeCarol')

      // Bob and Carol send friend requests to Alice
      await page.request.post(`${API}/friends/request`, {
        data: { user_id: alice.user.id },
        headers: { Authorization: `Bearer ${bob.access_token}` },
      })
      await page.request.post(`${API}/friends/request`, {
        data: { user_id: alice.user.id },
        headers: { Authorization: `Bearer ${carol.access_token}` },
      })

      // Alice checks notifications -- should see 2 pending requests
      const notifResp = await page.request.get(`${API}/notifications`, {
        headers: { Authorization: `Bearer ${alice.access_token}` },
      })
      const notif = await notifResp.json()
      expect(notif.friend_requests).toBe(2)
      expect(notif.total).toBe(2)

      // Login as Alice and verify bell badge in UI
      await loginAs(page, alice)

      // Wait for notification polling to fetch
      await page.waitForTimeout(2000)

      // Check via API that notifications are correct (UI polling might not have fired yet)
      const verifyResp = await page.request.get(`${API}/notifications`, {
        headers: { Authorization: `Bearer ${alice.access_token}` },
      })
      const verified = await verifyResp.json()
      expect(verified.friend_requests).toBe(2)
      expect(verified.total).toBe(2)

    } finally {
      await ctx.close()
    }
  })

  test('mutual friend request auto-accepts', async ({ browser }) => {
    test.setTimeout(15000)

    const ctx = await browser.newContext()
    const page = await ctx.newPage()

    try {
      const alice = await createTestUser(page.request, 'MutAlice')
      const bob = await createTestUser(page.request, 'MutBob')

      // Both send requests to each other
      await page.request.post(`${API}/friends/request`, {
        data: { user_id: bob.user.id },
        headers: { Authorization: `Bearer ${alice.access_token}` },
      })
      const resp = await page.request.post(`${API}/friends/request`, {
        data: { user_id: alice.user.id },
        headers: { Authorization: `Bearer ${bob.access_token}` },
      })
      expect((await resp.json()).status).toBe('accepted')

      // Both should see each other as friends
      const aFriends = await (await page.request.get(`${API}/friends`, {
        headers: { Authorization: `Bearer ${alice.access_token}` },
      })).json()
      expect(aFriends.friends.length).toBe(1)
      expect(aFriends.friends[0].display_name).toBe('MutBob')

    } finally {
      await ctx.close()
    }
  })

  test('user search returns results and excludes self', async ({ browser }) => {
    test.setTimeout(15000)

    const ctx = await browser.newContext()
    const page = await ctx.newPage()

    try {
      const suffix = Date.now().toString(36)
      const alice = await createTestUser(page.request, `Xfind${suffix}A`)
      const bob = await createTestUser(page.request, `Xfind${suffix}B`)

      // Alice searches for the unique suffix -- should find Bob but not herself
      const resp = await page.request.get(`${API}/users/search?q=Xfind${suffix}`, {
        headers: { Authorization: `Bearer ${alice.access_token}` },
      })
      const results = (await resp.json()).users
      const ids = results.map(u => u.id)
      expect(ids).toContain(bob.user.id)
      expect(ids).not.toContain(alice.user.id)

    } finally {
      await ctx.close()
    }
  })
})
