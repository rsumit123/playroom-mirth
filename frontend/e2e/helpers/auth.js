export async function loginAsTestUser(page, displayName) {
  const api = process.env.PLAYWRIGHT_API_BASE || 'http://localhost:8005'
  const res = await page.request.post(`${api}/auth/test_token`, {
    data: { display_name: displayName },
  })
  if (!res.ok()) {
    throw new Error(`test_token failed: ${res.status()} ${await res.text()}`)
  }
  const { token, user } = await res.json()
  await page.addInitScript((authPayload) => {
    localStorage.setItem('charade_auth', JSON.stringify(authPayload))
  }, { token, user, guestToken: null, guestDisplayName: null })
}
