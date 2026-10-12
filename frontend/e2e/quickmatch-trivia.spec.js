import { test, expect } from '@playwright/test'
import { loginAsTestUser } from './helpers/auth.js'

test('two signed-in users matchmake and play a quickmatch game', async ({ browser }) => {
  test.setTimeout(240_000)
  const ctxA = await browser.newContext()
  const ctxB = await browser.newContext()
  const pageA = await ctxA.newPage()
  const pageB = await ctxB.newPage()

  await loginAsTestUser(pageA, 'PlayerA')
  await loginAsTestUser(pageB, 'PlayerB')

  await pageA.goto('/play/trivia')
  await pageB.goto('/play/trivia')

  await pageA.getByText(/Play Now/i).click()
  await pageB.getByText(/Play Now/i).click()

  // Play Now auto-joins with "surprise", which the server resolves to a random
  // category per player, so both switch to the same topic to be paired.
  for (const page of [pageA, pageB]) {
    await page.getByRole('button', { name: 'Change topic' }).click()
    await page.getByRole('dialog', { name: 'Choose topic' }).getByText('Science').click()
  }

  // Splash should appear within a few seconds
  await expect(pageA.getByText(/MATCH FOUND/i)).toBeVisible({ timeout: 5000 })
  await expect(pageB.getByText(/MATCH FOUND/i)).toBeVisible({ timeout: 5000 })

  // Both players see Question 1 — matchmaking + room hand-off + game start all worked
  await expect(pageA.getByText(/Question 1 of/i)).toBeVisible({ timeout: 10000 })
  await expect(pageB.getByText(/Question 1 of/i)).toBeVisible({ timeout: 10000 })

  await ctxA.close()
  await ctxB.close()
})

test('single user falls back to bot after 15s', async ({ page }) => {
  await loginAsTestUser(page, 'LonelyPlayer')
  await page.goto('/play/trivia')
  await page.getByText(/Play Now/i).click()

  // Bot fallback fires ~15s in
  await expect(page.getByText(/MATCH FOUND/i)).toBeVisible({ timeout: 20000 })
  await expect(page.getByText(/Question 1 of/i)).toBeVisible({ timeout: 10000 })
})
