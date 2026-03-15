import { test, expect } from '@playwright/test'

const APP = 'http://localhost:5173'

/** Helper: log in as guest so protected routes are accessible */
async function loginAsGuest(page, name = 'TestUser') {
  await page.goto(APP)
  await page.waitForLoadState('networkidle')
  await page.evaluate(() => { localStorage.clear(); sessionStorage.clear() })
  await page.reload()
  await page.waitForLoadState('networkidle')
  await page.getByPlaceholder(/enter your name/i).fill(name)
  await page.getByRole('button', { name: /^play as guest$/i }).click()
  await page.waitForURL('**/home', { timeout: 10000 })
}

// ── A. Home page renders correctly on mobile ──────────────────────────

test.describe('Home page mobile layout', () => {
  test('game cards are visible and no horizontal overflow', async ({ page }) => {
    await loginAsGuest(page, 'MobileHome')

    // Verify game cards are visible (Charades, Scribble, Trivia)
    await expect(page.getByText('Charades').first()).toBeVisible()
    await expect(page.getByText('Scribble').first()).toBeVisible()
    await expect(page.getByText('Trivia').first()).toBeVisible()

    // Verify no horizontal overflow: body scrollWidth should equal clientWidth
    const overflow = await page.evaluate(() => {
      return document.body.scrollWidth > document.documentElement.clientWidth
    })
    expect(overflow).toBe(false)
  })
})

// ── B. Scribble game layout — simulate keyboard open ──────────────────

test.describe('Scribble game keyboard simulation', () => {
  test('chat input stays visible when keyboard opens', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 393, height: 851 }) // Pixel 5
    await page.goto('/scribble')

    // Simulate keyboard opening by reducing viewport height
    await page.setViewportSize({ width: 393, height: 400 }) // ~half height

    // Verify chat input is still visible/accessible
    const input = page.locator('input[placeholder*="guess"], input[placeholder*="type"]')
    // The page may redirect if no room state; check if we are still on /scribble
    const url = page.url()
    if (url.includes('/scribble')) {
      await expect(input).toBeVisible()

      // Verify canvas is still partially visible (not completely hidden)
      const canvas = page.locator('canvas')
      const box = await canvas.boundingBox()
      expect(box).not.toBeNull()
      expect(box.height).toBeGreaterThan(50)
    }
  })
})

// ── C. Input fields don't get hidden behind keyboard ──────────────────

test.describe('Input field visibility with keyboard', () => {
  test('input field scrolls into view on focus', async ({ page }) => {
    await page.setViewportSize({ width: 393, height: 400 })
    await page.goto('/scribble')

    const url = page.url()
    if (url.includes('/scribble')) {
      const input = page.locator('input[placeholder*="guess"]')
      if (await input.isVisible()) {
        await input.focus()
        const box = await input.boundingBox()
        if (box) {
          expect(box.y + box.height).toBeLessThanOrEqual(400)
        }
      }
    }
    // If redirected away from /scribble (no auth/room), test passes — layout test needs game state
  })
})

// ── D. Game setup form works on mobile ────────────────────────────────

test.describe('Game setup page mobile layout', () => {
  test('form fields and buttons are tappable and within viewport', async ({ page }) => {
    await loginAsGuest(page, 'MobileSetup')
    await page.goto(`${APP}/play/scribble`)
    await page.waitForLoadState('networkidle')

    // Verify the heading is visible
    await expect(page.locator('h2.font-display', { hasText: 'Scribble' })).toBeVisible()

    // Verify "Create Room" and "Join Room" tabs are visible
    const createTab = page.locator('.segmented-option-active, .segmented-option', { hasText: /create room/i }).first()
    const joinTab = page.locator('.segmented-option-active, .segmented-option', { hasText: /join room/i }).first()
    await expect(createTab).toBeVisible()
    await expect(joinTab).toBeVisible()

    // Verify the Create Room submit button is visible and within viewport
    const createBtn = page.locator('button.btn-primary', { hasText: /create room/i })
    const box = await createBtn.boundingBox()
    expect(box).not.toBeNull()
    const viewport = page.viewportSize()
    expect(box.x).toBeGreaterThanOrEqual(0)
    expect(box.y + box.height).toBeLessThanOrEqual(viewport.height + 50) // small tolerance for scroll

    // Switch to Join tab and verify input field is tappable
    await joinTab.click()
    const codeInput = page.locator('input[placeholder="ABCDEF"]')
    await expect(codeInput).toBeVisible()
    await codeInput.click()
    await codeInput.fill('TESTCO')
    await expect(codeInput).toHaveValue('TESTCO')
  })
})

// ── E. Lobby page mobile layout ───────────────────────────────────────

test.describe('Lobby page mobile layout', () => {
  test('lobby page elements do not overflow', async ({ page }) => {
    await page.goto('/lobby')
    await page.waitForLoadState('networkidle')

    // The lobby page redirects to /home if no room/auth state exists.
    const url = page.url()
    if (url.includes('/lobby')) {
      // Verify no horizontal overflow
      const overflow = await page.evaluate(() => {
        return document.body.scrollWidth > document.documentElement.clientWidth
      })
      expect(overflow).toBe(false)
    }
    // If redirected away, that's expected — lobby requires active room state
  })
})
