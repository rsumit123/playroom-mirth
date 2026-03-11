/**
 * Auth / Session Expiry E2E Tests
 *
 * Tests:
 * 1. Backend returns 401 for invalid/expired JWT
 * 2. Frontend api.js throws with status 401 on expired token
 * 3. Browser redirects to welcome page when session expires on /home
 * 4. Browser redirects to welcome page when session expires on /play/:game
 * 5. Browser does NOT redirect /join/:code routes (those don't require auth)
 */

const API = process.env.API_BASE || 'http://localhost:8000';
const FRONTEND = process.env.FRONTEND_BASE || 'http://localhost:5173';
const USE_PLAYWRIGHT = process.env.USE_PLAYWRIGHT !== '0';
const TIMEOUT = 15000;

const results = [];

function log(msg) {
  const ts = new Date().toISOString().slice(11, 19);
  console.log(`[${ts}] ${msg}`);
}

function result(name, passed, detail = '') {
  results.push({ name, passed, detail });
  console.log(`  ${passed ? 'PASS' : 'FAIL'}: ${name}${detail ? ' — ' + detail : ''}`);
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ============================================================
// TEST 1: Backend 401 for invalid JWT
// ============================================================
async function testBackend401() {
  console.log('\n--- Test 1: Backend returns 401 for invalid JWT ---');

  // 1a: Completely fake token
  try {
    const res = await fetch(`${API}/rooms/active`, {
      headers: { Authorization: 'Bearer totally-fake-token-12345' },
    });
    result('Fake JWT → 401', res.status === 401, `Got: ${res.status}`);
  } catch (err) {
    result('Fake JWT → 401', false, err.message);
  }

  // 1b: Malformed JWT (3 parts but garbage)
  try {
    const res = await fetch(`${API}/rooms/active`, {
      headers: { Authorization: 'Bearer aaa.bbb.ccc' },
    });
    result('Malformed JWT → 401', res.status === 401, `Got: ${res.status}`);
  } catch (err) {
    result('Malformed JWT → 401', false, err.message);
  }

  // 1c: Expired-looking JWT (valid structure, wrong signature)
  // Create a JWT-like string with expired exp claim
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(JSON.stringify({ sub: '999', exp: Math.floor(Date.now() / 1000) - 3600 }));
  const fakeJwt = `${header}.${payload}.fakesignature`;
  try {
    const res = await fetch(`${API}/rooms/active`, {
      headers: { Authorization: `Bearer ${fakeJwt}` },
    });
    result('Expired JWT → 401', res.status === 401, `Got: ${res.status}`);
  } catch (err) {
    result('Expired JWT → 401', false, err.message);
  }

  // 1d: Valid guest token still works (not 401)
  try {
    const guestRes = await fetch(`${API}/guest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ display_name: 'AuthTestGuest' }),
    });
    const guest = await guestRes.json();
    const res = await fetch(`${API}/rooms/active?guest_token=${encodeURIComponent(guest.guest_token)}`);
    result('Valid guest token → 200', res.status === 200, `Got: ${res.status}`);
  } catch (err) {
    result('Valid guest token → 200', false, err.message);
  }
}

// ============================================================
// TEST 2: Frontend redirect on expired session (Playwright)
// ============================================================
async function testFrontendRedirect() {
  if (!USE_PLAYWRIGHT) {
    log('Skipping Playwright tests (USE_PLAYWRIGHT=0)');
    return;
  }

  let chromium;
  try {
    ({ chromium } = await import('playwright'));
  } catch {
    log('Playwright not available, skipping browser tests');
    return;
  }

  console.log('\n--- Test 2: Frontend redirect on expired session ---');

  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });

  try {
    // 2a: Sign in as guest, then simulate expired JWT session → redirect to /
    {
      console.log('\n  2a: Expired JWT user on /home → redirect to /');
      const ctx = await browser.newContext();
      const page = await ctx.newPage();

      // Sign in as guest first
      await page.goto(FRONTEND, { waitUntil: 'networkidle', timeout: TIMEOUT });
      if (!page.url().includes('/home')) {
        const input = page.locator('input[placeholder="Enter your name"]');
        await input.waitFor({ state: 'visible', timeout: TIMEOUT });
        await input.fill('SessionTestUser');
        await page.locator('button:has-text("Play as Guest")').click();
        await page.waitForSelector('text=Choose a Game', { timeout: TIMEOUT });
      }
      log('Signed in as guest, on /home');

      // Now corrupt localStorage to simulate an expired JWT user (remove guest, add fake JWT)
      await page.evaluate(() => {
        localStorage.setItem('charade_auth', JSON.stringify({
          token: 'expired.jwt.token',
          guestToken: null,
          guestDisplayName: null,
          user: { email: 'test@example.com', display_name: 'TestUser', avatar_url: null },
        }));
      });
      log('Corrupted localStorage with fake expired JWT');

      // Reload — this will trigger fetchActiveRooms with bad token → 401 → logout → redirect
      await page.goto(`${FRONTEND}/home`, { waitUntil: 'networkidle', timeout: TIMEOUT });
      await sleep(2000);

      const url = page.url();
      const onWelcome = url.endsWith('/') || url.endsWith(FRONTEND);
      result('Expired session on /home → redirected to /', onWelcome, `URL: ${url}`);

      // Verify welcome page content
      const hasGuestBtn = await page.locator('text=Play as Guest').isVisible({ timeout: 3000 }).catch(() => false);
      result('Welcome page shows sign-in options', hasGuestBtn);

      // Verify toast message shown
      const hasToast = await page.locator('text=Session expired').isVisible({ timeout: 3000 }).catch(() => false);
      result('Toast shows "Session expired" message', hasToast);

      await ctx.close();
    }

    // 2b: Expired session on /play/trivia → redirect to /
    {
      console.log('\n  2b: Expired JWT user on /play/trivia → redirect to /');
      const ctx = await browser.newContext();
      const page = await ctx.newPage();

      // Set corrupted auth directly
      await page.goto(FRONTEND, { waitUntil: 'networkidle', timeout: TIMEOUT });
      await page.evaluate(() => {
        localStorage.setItem('charade_auth', JSON.stringify({
          token: 'expired.jwt.token',
          guestToken: null,
          guestDisplayName: null,
          user: { email: 'test@example.com', display_name: 'TestUser', avatar_url: null },
        }));
      });

      await page.goto(`${FRONTEND}/play/trivia`, { waitUntil: 'networkidle', timeout: TIMEOUT });
      await sleep(2000);

      const url = page.url();
      const onWelcome = url.endsWith('/') || url.endsWith(FRONTEND);
      result('Expired session on /play/trivia → redirected to /', onWelcome, `URL: ${url}`);

      await ctx.close();
    }

    // 2c: Unauthenticated user on /home → redirect to /
    {
      console.log('\n  2c: No auth on /home → redirect to /');
      const ctx = await browser.newContext();
      const page = await ctx.newPage();

      // Go directly to /home with no auth
      await page.goto(`${FRONTEND}/home`, { waitUntil: 'networkidle', timeout: TIMEOUT });
      await sleep(1500);

      const url = page.url();
      const onWelcome = url.endsWith('/') || url.endsWith(FRONTEND);
      result('No auth on /home → redirected to /', onWelcome, `URL: ${url}`);

      await ctx.close();
    }

    // 2d: /join/:code should NOT redirect (anyone can join)
    {
      console.log('\n  2d: /join/:code does NOT redirect without auth');
      const ctx = await browser.newContext();
      const page = await ctx.newPage();

      await page.goto(`${FRONTEND}/join/ABCDEF`, { waitUntil: 'networkidle', timeout: TIMEOUT });
      await sleep(1500);

      const url = page.url();
      const stayedOnJoin = url.includes('/join/');
      result('/join/:code stays on join page without auth', stayedOnJoin, `URL: ${url}`);

      await ctx.close();
    }

    // 2e: Valid guest session stays on /home (no redirect)
    {
      console.log('\n  2e: Valid guest session stays on /home');
      const ctx = await browser.newContext();
      const page = await ctx.newPage();

      // Sign in normally as guest
      await page.goto(FRONTEND, { waitUntil: 'networkidle', timeout: TIMEOUT });
      if (!page.url().includes('/home')) {
        const input = page.locator('input[placeholder="Enter your name"]');
        await input.waitFor({ state: 'visible', timeout: TIMEOUT });
        await input.fill('ValidGuest');
        await page.locator('button:has-text("Play as Guest")').click();
        await page.waitForSelector('text=Choose a Game', { timeout: TIMEOUT });
      }

      const url = page.url();
      const onHome = url.includes('/home');
      result('Valid guest stays on /home', onHome, `URL: ${url}`);

      await ctx.close();
    }

  } finally {
    await browser.close();
  }
}

// ============================================================
// Main
// ============================================================
async function main() {
  console.log('='.repeat(60));
  console.log(' Auth / Session Expiry Tests');
  console.log(`  API: ${API}`);
  console.log(`  Frontend: ${FRONTEND}`);
  console.log('='.repeat(60));

  await testBackend401();
  await testFrontendRedirect();

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log(' RESULTS');
  console.log('='.repeat(60));
  const passed = results.filter(r => r.passed).length;
  const failed = results.filter(r => !r.passed).length;
  for (const r of results) {
    console.log(`  ${r.passed ? 'PASS' : 'FAIL'}: ${r.name}${r.detail ? ' — ' + r.detail : ''}`);
  }
  console.log('-'.repeat(60));
  console.log(` Total: ${results.length} | Passed: ${passed} | Failed: ${failed}`);
  console.log('='.repeat(60));
  if (failed > 0) process.exit(1);
}

main().catch(err => { console.error('Fatal:', err); process.exit(1); });
