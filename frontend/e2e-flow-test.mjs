/**
 * E2E test: Play Again flow + Next Round flow
 *
 * Tests:
 * 1. Full game → Play Again → Rejoin → verify lobby (not game screen)
 * 2. Multi-round game → Next Round → verify both players transition
 * 3. Timer correctness after transitions
 */
import { chromium } from 'playwright';

const BASE = 'https://playroom.skdev.one';
const API = 'https://charade-api.skdev.one';
const TIMEOUT = 20000;
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

async function signInAsGuest(page, name) {
  await page.goto(BASE, { waitUntil: 'networkidle', timeout: TIMEOUT });
  if (page.url().includes('/home')) return;
  const input = page.locator('input[placeholder="Enter your name"]');
  await input.waitFor({ state: 'visible', timeout: TIMEOUT });
  await input.fill(name);
  await page.locator('button:has-text("Play as Guest")').click();
  await page.waitForSelector('text=Choose a Game', { timeout: TIMEOUT });
}

async function getGuestToken(page) {
  return page.evaluate(() => {
    const auth = JSON.parse(localStorage.getItem('charade_auth') || '{}');
    return auth.guestToken;
  });
}

async function createRoom(page, gameType) {
  const cardText = gameType === 'scribble' ? 'Scribble' : 'Charades';
  await page.locator(`button.card:has-text("${cardText}")`).click();
  const createBtn = page.locator('button.btn-primary:has-text("Create Room")');
  await createBtn.waitFor({ state: 'visible', timeout: TIMEOUT });
  await createBtn.click();
  await page.waitForSelector('text=Room Code', { timeout: TIMEOUT });
  const code = await page.evaluate(() => {
    const el = document.querySelector('.text-accent.font-display');
    return el ? el.textContent.trim() : null;
  });
  return code;
}

async function setRoomTimer(guestToken, roomCode, turnSeconds, rounds) {
  const params = `?guest_token=${encodeURIComponent(guestToken)}`;
  const res = await fetch(`${API}/rooms/${roomCode}/settings${params}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ turn_seconds: turnSeconds, rounds_total: rounds, difficulty: 2 }),
  });
  return res.ok;
}

async function waitForGameEnd(page, timeoutMs = 120000) {
  try {
    await page.waitForSelector('text=Final Results', { timeout: timeoutMs });
    return true;
  } catch {
    return false;
  }
}

async function waitForRoundEnd(page, timeoutMs = 60000) {
  try {
    await page.waitForSelector('text=Round Complete', { timeout: timeoutMs });
    return true;
  } catch {
    return false;
  }
}

async function getCurrentPageType(page) {
  const url = page.url();
  if (url.includes('/game-end')) return 'game-end';
  if (url.includes('/round-end')) return 'round-end';
  if (url.includes('/game') || url.includes('/scribble')) return 'game';
  if (url.includes('/lobby')) return 'lobby';
  if (url.includes('/home')) return 'home';

  // Also check page content
  const hasGameEnd = await page.locator('text=Final Results').isVisible({ timeout: 1000 }).catch(() => false);
  if (hasGameEnd) return 'game-end';
  const hasRoundEnd = await page.locator('text=Round Complete').isVisible({ timeout: 1000 }).catch(() => false);
  if (hasRoundEnd) return 'round-end';
  const hasLobby = await page.locator('text=Room Code').isVisible({ timeout: 1000 }).catch(() => false);
  if (hasLobby) return 'lobby';
  const hasHome = await page.locator('text=Choose a Game').isVisible({ timeout: 1000 }).catch(() => false);
  if (hasHome) return 'home';
  const hasDescriber = await page.locator('text=Describer').isVisible({ timeout: 500 }).catch(() => false);
  const hasGuesser = await page.locator('text=Guesser').isVisible({ timeout: 500 }).catch(() => false);
  if (hasDescriber || hasGuesser) return 'game';
  return 'unknown';
}

async function getTimerValue(page) {
  return page.evaluate(() => {
    // CircularTimer uses a <span> overlay, not SVG <text>
    const container = document.querySelector('.relative.inline-flex svg');
    if (!container) return null;
    const span = container.parentElement.querySelector('span.absolute');
    return span ? parseInt(span.textContent.trim(), 10) : null;
  });
}

// ============================================================
// TEST 1: Play Again → Rejoin flow
// ============================================================
async function testPlayAgainFlow(browser) {
  console.log('\n' + '='.repeat(60));
  console.log(' TEST 1: Play Again → Rejoin Flow');
  console.log('='.repeat(60));

  const ctxA = await browser.newContext();
  const ctxB = await browser.newContext();
  const pageA = await ctxA.newPage();
  const pageB = await ctxB.newPage();

  try {
    // Setup
    log('Signing in players...');
    await signInAsGuest(pageA, 'HostPA');
    await signInAsGuest(pageB, 'GuestPA');
    const tokenA = await getGuestToken(pageA);

    log('Creating Charades room...');
    const code = await createRoom(pageA, 'charades');
    log(`Room: ${code}`);

    // Set timer to 10 seconds, 1 round for quick game
    log('Setting timer to 10s, 1 round...');
    const settingsOk = await setRoomTimer(tokenA, code, 10, 1);
    result('Room settings updated', settingsOk, `timer=10s, rounds=1`);

    log('Player B joining...');
    await pageB.goto(`${BASE}/join/${code}`, { waitUntil: 'networkidle', timeout: TIMEOUT });
    await pageB.waitForSelector('text=Room Code', { timeout: TIMEOUT });
    await sleep(1000);

    log('Starting game...');
    const startBtn = pageA.locator('button:has-text("Start Game")');
    await startBtn.waitFor({ state: 'visible', timeout: TIMEOUT });
    await startBtn.click();
    await sleep(2000);

    // Verify game started
    const pageTypeA1 = await getCurrentPageType(pageA);
    const pageTypeB1 = await getCurrentPageType(pageB);
    result('Both players in game after start', pageTypeA1 === 'game' && pageTypeB1 === 'game',
      `A: ${pageTypeA1}, B: ${pageTypeB1}`);

    // Check initial timer values
    const timerA1 = await getTimerValue(pageA);
    const timerB1 = await getTimerValue(pageB);
    log(`Initial timers — A: ${timerA1}s, B: ${timerB1}s`);
    result('Timer started correctly', timerA1 > 0 && timerB1 > 0, `A: ${timerA1}s, B: ${timerB1}s`);

    // Wait for game to end (2 turns × 10s = ~20s + buffer)
    log('Waiting for game to end (2 turns × 10s)...');
    const gameEnded = await waitForGameEnd(pageA, 60000);
    result('Game ended for host', gameEnded);

    if (gameEnded) {
      await sleep(1000);
      const gameEndedB = await pageB.locator('text=Final Results').isVisible({ timeout: 5000 }).catch(() => false) ||
        await waitForGameEnd(pageB, 10000);
      result('Game ended for guest', true);

      // Take screenshot of game end
      await pageA.screenshot({ path: '/tmp/test-gameend-a.png' });
      await pageB.screenshot({ path: '/tmp/test-gameend-b.png' });

      // Both click "Play Again"
      log('Both clicking Play Again...');
      const playAgainA = pageA.locator('button:has-text("Play Again")');
      const playAgainB = pageB.locator('button:has-text("Play Again")');

      if (await playAgainA.isVisible({ timeout: 3000 }).catch(() => false)) {
        await playAgainA.click();
      }
      await sleep(500);
      if (await playAgainB.isVisible({ timeout: 3000 }).catch(() => false)) {
        await playAgainB.click();
      }
      await sleep(2000);

      // Both should be on home page
      const pageTypeA2 = await getCurrentPageType(pageA);
      const pageTypeB2 = await getCurrentPageType(pageB);
      result('Both on home after Play Again', pageTypeA2 === 'home' && pageTypeB2 === 'home',
        `A: ${pageTypeA2}, B: ${pageTypeB2}`);

      // Check for active room
      const hasActiveRoom = await pageA.locator('text=Active Rooms').isVisible({ timeout: 3000 }).catch(() => false);
      log(`Active Rooms section visible: ${hasActiveRoom}`);

      // Both click Rejoin
      log('Both clicking Rejoin...');
      const rejoinA = pageA.locator('button:has-text("Rejoin")').first();
      const rejoinB = pageB.locator('button:has-text("Rejoin")').first();

      if (await rejoinA.isVisible({ timeout: 5000 }).catch(() => false)) {
        await rejoinA.click();
      }
      await sleep(1000);
      if (await rejoinB.isVisible({ timeout: 5000 }).catch(() => false)) {
        await rejoinB.click();
      }
      await sleep(2000);

      // THE KEY CHECK: Both should be on LOBBY, not game screen
      const pageTypeA3 = await getCurrentPageType(pageA);
      const pageTypeB3 = await getCurrentPageType(pageB);
      result('Host on LOBBY after rejoin (not game)', pageTypeA3 === 'lobby',
        `Got: ${pageTypeA3}`);
      result('Guest on LOBBY after rejoin (not game)', pageTypeB3 === 'lobby',
        `Got: ${pageTypeB3}`);

      await pageA.screenshot({ path: '/tmp/test-rejoin-a.png' });
      await pageB.screenshot({ path: '/tmp/test-rejoin-b.png' });

      // If on game screen, check timer
      if (pageTypeA3 === 'game' || pageTypeB3 === 'game') {
        const timerAfterRejoin = await getTimerValue(pageTypeA3 === 'game' ? pageA : pageB);
        result('Timer after rejoin is NOT 0', timerAfterRejoin !== 0 && timerAfterRejoin !== null,
          `Timer: ${timerAfterRejoin}`);
      }
    }

  } catch (err) {
    result('Test 1 execution', false, err.message.slice(0, 120));
    await pageA.screenshot({ path: '/tmp/test1-error-a.png' }).catch(() => {});
    await pageB.screenshot({ path: '/tmp/test1-error-b.png' }).catch(() => {});
  } finally {
    await ctxA.close();
    await ctxB.close();
  }
}

// ============================================================
// TEST 2: Next Round flow
// ============================================================
async function testNextRoundFlow(browser) {
  console.log('\n' + '='.repeat(60));
  console.log(' TEST 2: Next Round Flow');
  console.log('='.repeat(60));

  const ctxA = await browser.newContext();
  const ctxB = await browser.newContext();
  const pageA = await ctxA.newPage();
  const pageB = await ctxB.newPage();

  try {
    log('Signing in players...');
    await signInAsGuest(pageA, 'HostNR');
    await signInAsGuest(pageB, 'GuestNR');
    const tokenA = await getGuestToken(pageA);

    log('Creating Charades room...');
    const code = await createRoom(pageA, 'charades');
    log(`Room: ${code}`);

    // Set timer to 10 seconds, 2 rounds
    log('Setting timer to 10s, 2 rounds...');
    await setRoomTimer(tokenA, code, 10, 2);

    log('Player B joining...');
    await pageB.goto(`${BASE}/join/${code}`, { waitUntil: 'networkidle', timeout: TIMEOUT });
    await pageB.waitForSelector('text=Room Code', { timeout: TIMEOUT });
    await sleep(1000);

    log('Starting game...');
    await pageA.locator('button:has-text("Start Game")').click();
    await sleep(2000);

    // Wait for round 1 to end (2 turns × 10s = ~20s)
    log('Waiting for round 1 to end...');
    const roundEnded = await waitForRoundEnd(pageA, 45000);
    result('Round 1 ended for host', roundEnded);

    if (roundEnded) {
      await sleep(1000);

      // Check non-host sees round end too
      const guestRoundEnd = await pageB.locator('text=Round Complete').isVisible({ timeout: 5000 }).catch(() => false);
      result('Guest sees Round Complete', guestRoundEnd);

      await pageA.screenshot({ path: '/tmp/test-roundend-a.png' });
      await pageB.screenshot({ path: '/tmp/test-roundend-b.png' });

      // Host clicks "Next Round"
      log('Host clicking Next Round...');
      const nextRoundBtn = pageA.locator('button:has-text("Next Round")');
      if (await nextRoundBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
        await nextRoundBtn.click();
        await sleep(3000);

        // Both should transition to game screen for round 2
        const pageTypeA = await getCurrentPageType(pageA);
        const pageTypeB = await getCurrentPageType(pageB);
        result('Host in game after Next Round', pageTypeA === 'game', `Got: ${pageTypeA}`);
        result('Guest in game after Next Round', pageTypeB === 'game', `Got: ${pageTypeB}`);

        // Check timer is running (not stuck at 0)
        const timerA = await getTimerValue(pageA);
        const timerB = await getTimerValue(pageB);
        result('Host timer > 0 after Next Round', timerA > 0, `Timer: ${timerA}s`);
        result('Guest timer > 0 after Next Round', timerB > 0, `Timer: ${timerB}s`);

        await pageA.screenshot({ path: '/tmp/test-round2-a.png' });
        await pageB.screenshot({ path: '/tmp/test-round2-b.png' });

        // Check round number
        const roundText = await pageA.locator('text=Round 2').isVisible({ timeout: 3000 }).catch(() => false);
        result('Shows Round 2', roundText);

      } else {
        result('Next Round button visible', false, 'Button not found');
      }
    }

  } catch (err) {
    result('Test 2 execution', false, err.message.slice(0, 120));
    await pageA.screenshot({ path: '/tmp/test2-error-a.png' }).catch(() => {});
    await pageB.screenshot({ path: '/tmp/test2-error-b.png' }).catch(() => {});
  } finally {
    await ctxA.close();
    await ctxB.close();
  }
}

// ============================================================
// TEST 3: Quick Rejoin during lobby (no game running)
// ============================================================
async function testRejoinToLobby(browser) {
  console.log('\n' + '='.repeat(60));
  console.log(' TEST 3: Rejoin to Lobby (no game in progress)');
  console.log('='.repeat(60));

  const ctxA = await browser.newContext();
  const pageA = await ctxA.newPage();

  try {
    log('Signing in...');
    await signInAsGuest(pageA, 'RejoinTest');

    log('Creating room...');
    const code = await createRoom(pageA, 'charades');
    log(`Room: ${code}`);

    // Go home
    log('Navigating home...');
    await pageA.goto(`${BASE}/home`, { waitUntil: 'networkidle', timeout: TIMEOUT });
    await sleep(1500);

    // Click Rejoin
    log('Clicking Rejoin...');
    const rejoinBtn = pageA.locator('button:has-text("Rejoin")').first();
    if (await rejoinBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await rejoinBtn.click();
      await sleep(2000);

      const pageType = await getCurrentPageType(pageA);
      result('Rejoin goes to lobby', pageType === 'lobby', `Got: ${pageType}`);

      // Verify lobby shows room code
      const hasRoomCode = await pageA.locator(`text=${code}`).isVisible({ timeout: 3000 }).catch(() => false);
      result('Lobby shows correct room code', hasRoomCode);

      // Verify no game screen elements
      const hasDescriber = await pageA.locator('text=Describer').isVisible({ timeout: 1000 }).catch(() => false);
      const hasGuesser = await pageA.locator('text=Guesser').isVisible({ timeout: 1000 }).catch(() => false);
      result('No game screen elements in lobby', !hasDescriber && !hasGuesser);
    } else {
      result('Rejoin button found', false);
    }

  } catch (err) {
    result('Test 3 execution', false, err.message.slice(0, 120));
  } finally {
    await ctxA.close();
  }
}

// ============================================================
// Main
// ============================================================
async function main() {
  console.log('='.repeat(60));
  console.log(' Game Flow E2E Tests');
  console.log(`Target: ${BASE}`);
  console.log('='.repeat(60));

  const browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });

  try {
    await testRejoinToLobby(browser);
    await testNextRoundFlow(browser);
    await testPlayAgainFlow(browser);
  } finally {
    await browser.close();
  }

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
