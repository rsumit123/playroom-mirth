import { test, expect } from '@playwright/test'
import { loginAsTestUser } from './helpers/auth.js'

test('two signed-in users matchmake and play a quickmatch game', async ({ browser }) => {
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

  // Both pick Science and start
  await pageA.getByText('Science').click()
  await pageA.getByText(/Start Searching/i).click()
  await pageB.getByText('Science').click()
  await pageB.getByText(/Start Searching/i).click()

  // Splash should appear within a few seconds
  await expect(pageA.getByText(/MATCH FOUND/i)).toBeVisible({ timeout: 5000 })
  await expect(pageB.getByText(/MATCH FOUND/i)).toBeVisible({ timeout: 5000 })

  // Game starts; first question shows
  await expect(pageA.getByText(/Question 1 of/i)).toBeVisible({ timeout: 10000 })

  // Click any answer on both
  await pageA.locator('button').filter({ hasText: /^(?!.*Leave).*$/ }).first().click()
  await pageB.locator('button').first().click()

  // Eventually game ends
  await expect(pageA.getByText(/You (Win|Lost)/i)).toBeVisible({ timeout: 180000 })

  await ctxA.close()
  await ctxB.close()
})

test('single user falls back to bot after 15s', async ({ page }) => {
  await loginAsTestUser(page, 'LonelyPlayer')
  await page.goto('/play/trivia')
  await page.getByText(/Play Now/i).click()
  await page.getByText('Science').click()
  await page.getByText(/Start Searching/i).click()

  // Bot fallback fires ~15s in
  await expect(page.getByText(/MATCH FOUND/i)).toBeVisible({ timeout: 20000 })
  await expect(page.getByText(/Question 1 of/i)).toBeVisible({ timeout: 10000 })
})
