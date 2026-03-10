import { io } from 'socket.io-client';

const API = 'https://charade-api.skdev.one';

function waitFor(socket, event, timeoutMs = 30000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`Timeout waiting for ${event}`)), timeoutMs);
    socket.once(event, (p) => { clearTimeout(timer); resolve(p); });
  });
}

/** Like waitFor but resolves to null on timeout instead of rejecting. */
function waitForSafe(socket, event, timeoutMs = 30000) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      socket.off(event, handler);
      resolve(null);
    }, timeoutMs);
    function handler(p) {
      clearTimeout(timer);
      resolve(p);
    }
    socket.once(event, handler);
  });
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

/** Retry-aware fetch wrapper */
async function fetchRetry(url, opts, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, opts);
      return res;
    } catch (err) {
      if (i === retries - 1) throw err;
      console.log(`    (fetch retry ${i + 1}/${retries} for ${url})`);
      await sleep(1000 * (i + 1));
    }
  }
}

let pass = 0, fail = 0;
function check(name, cond, detail = '') {
  if (cond) { pass++; console.log('  PASS:', name, detail ? '-- ' + detail : ''); }
  else { fail++; console.log('  FAIL:', name, detail ? '-- ' + detail : ''); }
}

async function createGuest(name) {
  const res = await fetchRetry(API + '/guest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ display_name: name })
  });
  return res.json();
}

async function createRoom(guestToken, { rounds = 1, difficulty = 1 } = {}) {
  const res = await fetchRetry(API + '/rooms/guest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      guest_token: guestToken,
      game_type: 'trivia',
      rounds_total: rounds,
      difficulty,
      turn_seconds: 0
    })
  });
  return res.json();
}

async function joinRoom(roomCode, guestToken) {
  const res = await fetchRetry(API + '/rooms/join', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ room_code: roomCode, guest_token: guestToken })
  });
  return res.json();
}

function connectSocket() {
  const s = io(API, { transports: ['websocket'] });
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('Socket connect timeout')), 10000);
    s.on('connect', () => { clearTimeout(timer); resolve(s); });
    s.on('connect_error', (err) => { clearTimeout(timer); reject(err); });
  });
}

async function registerSocket(socket, roomCode, guestToken) {
  socket.emit('room:register', { room_code: roomCode, guest_token: guestToken });
  return waitFor(socket, 'room:lobby_update');
}

// Collect all sockets so we can clean up on fatal errors
const allSockets = [];

// ============================================================
// TEST 1: Timer timeout -- no one answers, verify question_result
// Then verify next question arrives after ~4s pause.
// ============================================================
async function test1_timerTimeout() {
  console.log('\n========================================');
  console.log('TEST 1: Timer Timeout (no answers)');
  console.log('========================================');

  const alice = await createGuest('Alice');
  const bob = await createGuest('Bob');
  console.log('  Created guests: Alice, Bob');

  const rd = await createRoom(alice.guest_token, { rounds: 1, difficulty: 1 });
  const code = rd.room?.code;
  if (!code) { console.log('  FATAL: Room creation failed:', JSON.stringify(rd)); return { code: null }; }
  console.log('  Room:', code, '(1 round, easy/difficulty=1)');

  await joinRoom(code, bob.guest_token);

  const as = await connectSocket();
  const bs = await connectSocket();
  allSockets.push(as, bs);

  await registerSocket(as, code, alice.guest_token);
  await registerSocket(bs, code, bob.guest_token);
  console.log('  Both players registered');

  // Set up listeners before starting
  const aTurnP = waitFor(as, 'game:turn_start');
  const bTurnP = waitFor(bs, 'game:turn_start');
  const aQ1P = waitFor(as, 'trivia:question');
  const bQ1P = waitFor(bs, 'trivia:question');

  as.emit('game:start', { room_code: code, guest_token: alice.guest_token });
  console.log('  Game started. Waiting for question...');

  await Promise.all([aTurnP, bTurnP]);
  const [aQ1, bQ1] = await Promise.all([aQ1P, bQ1P]);
  check('T1: Both received question #0', aQ1?.question_index === 0 && bQ1?.question_index === 0);
  check('T1: Easy timer is 20s', aQ1?.time_seconds === 20, `got ${aQ1?.time_seconds}`);

  // DO NOT answer. Wait for the timer to expire (~20s) + server processing.
  // Set up BOTH result and next-question listeners NOW before the timeout,
  // so we don't miss the next question that arrives ~4s after the result.
  console.log('  Waiting for timer expiry (~20s, not answering)...');
  const aResultP = waitFor(as, 'trivia:question_result', 35000);
  const bResultP = waitFor(bs, 'trivia:question_result', 35000);
  // Pre-register next-question listener (arrives ~4s after result)
  const aQ2P = waitForSafe(as, 'trivia:question', 35000);
  const bQ2P = waitForSafe(bs, 'trivia:question', 35000);

  const [aResult, bResult] = await Promise.all([aResultP, bResultP]);
  check('T1: Alice received question_result after timeout', !!aResult);
  check('T1: Bob received question_result after timeout', !!bResult);
  check('T1: Result has player_results', Array.isArray(aResult?.player_results) && aResult.player_results.length === 2);

  // Verify both have answer_index=-1 and points=0
  for (const pr of aResult?.player_results || []) {
    check(`T1: Player ${pr.player_id} answer_index=-1 (timed out)`, pr.answer_index === -1, `got ${pr.answer_index}`);
    check(`T1: Player ${pr.player_id} points=0`, pr.points === 0, `got ${pr.points}`);
    check(`T1: Player ${pr.player_id} correct=false`, pr.correct === false);
  }

  // Verify next question arrives after the ~4s pause
  console.log('  Waiting for next question after 4s pause (up to 15s)...');
  const [aQ2, bQ2] = await Promise.all([aQ2P, bQ2P]);
  check('T1: Next question arrived (question_index=1)', aQ2?.question_index === 1, aQ2 ? `got ${aQ2?.question_index}` : 'TIMED OUT (possible server-side task cancellation bug)');
  check('T1: Bob also got next question', bQ2?.question_index === 1, bQ2 ? `got ${bQ2?.question_index}` : 'TIMED OUT');

  // Clean up these sockets regardless
  as.disconnect();
  bs.disconnect();
  console.log('  Test 1 cleanup done');

  return { code, alice, bob };
}

// ============================================================
// TEST 2: Partial answers + timeout (Alice answers, Bob doesn't)
// Uses a FRESH room to avoid any state issues from Test 1.
// ============================================================
async function test2_partialTimeout() {
  console.log('\n========================================');
  console.log('TEST 2: Partial Answers + Timeout');
  console.log('========================================');

  const alice = await createGuest('Alice2');
  const bob = await createGuest('Bob2');
  console.log('  Created guests: Alice2, Bob2');

  const rd = await createRoom(alice.guest_token, { rounds: 1, difficulty: 1 });
  const code = rd.room?.code;
  if (!code) { console.log('  FATAL: Room creation failed:', JSON.stringify(rd)); return; }
  console.log('  Room:', code, '(1 round, easy/difficulty=1)');

  await joinRoom(code, bob.guest_token);

  const as = await connectSocket();
  const bs = await connectSocket();
  allSockets.push(as, bs);

  await registerSocket(as, code, alice.guest_token);
  await registerSocket(bs, code, bob.guest_token);
  console.log('  Both players registered');

  // Start the game
  const aTurnP = waitFor(as, 'game:turn_start');
  const bTurnP = waitFor(bs, 'game:turn_start');
  const aQP = waitFor(as, 'trivia:question');
  const bQP = waitFor(bs, 'trivia:question');

  as.emit('game:start', { room_code: code, guest_token: alice.guest_token });
  await Promise.all([aTurnP, bTurnP]);
  const [aQ, bQ] = await Promise.all([aQP, bQP]);
  console.log('  First question received. Alice will answer, Bob will not.');

  // Alice answers, Bob does NOT
  const aUpdateP = waitFor(as, 'trivia:answer_update');
  as.emit('trivia:answer', { room_code: code, answer_index: 2 });
  const aUpdate = await aUpdateP;
  check('T2: answer_update shows 1 of 2 answered', aUpdate?.answered_count === 1 && aUpdate?.total_players === 2,
    `answered_count=${aUpdate?.answered_count}, total_players=${aUpdate?.total_players}`);

  // Now wait for timeout since Bob won't answer.
  // Set up result listener
  console.log('  Waiting for timer expiry (~20s, Bob not answering)...');
  const aResult2P = waitFor(as, 'trivia:question_result', 35000);
  const bResult2P = waitFor(bs, 'trivia:question_result', 35000);

  const [aResult2, bResult2] = await Promise.all([aResult2P, bResult2P]);
  check('T2: Result received after partial timeout', !!aResult2);
  check('T2: Result has 2 player_results', aResult2?.player_results?.length === 2, `got ${aResult2?.player_results?.length}`);

  // Find Alice and Bob in results
  // Alice should have answer_index=2, Bob should have answer_index=-1
  let aliceResult = null, bobResult = null;
  for (const pr of aResult2?.player_results || []) {
    if (pr.answer_index === 2) aliceResult = pr;
    if (pr.answer_index === -1) bobResult = pr;
  }

  check('T2: Alice answered with index=2', aliceResult !== null, aliceResult ? `answer_index=${aliceResult.answer_index}` : 'not found');
  check('T2: Bob timed out with index=-1', bobResult !== null, bobResult ? `answer_index=${bobResult.answer_index}` : 'not found');
  check('T2: Bob got 0 points', bobResult?.points === 0, `got ${bobResult?.points}`);
  check('T2: Bob correct=false', bobResult?.correct === false);

  // Clean up
  as.disconnect();
  bs.disconnect();
  console.log('  Test 2 cleanup done');
}

// ============================================================
// TEST 3: Three players
// ============================================================
async function test3_threePlayers() {
  console.log('\n========================================');
  console.log('TEST 3: Three Players');
  console.log('========================================');

  const alice = await createGuest('Alice3');
  const bob = await createGuest('Bob3');
  const charlie = await createGuest('Charlie3');
  console.log('  Created guests: Alice3, Bob3, Charlie3');

  const rd = await createRoom(alice.guest_token, { rounds: 1, difficulty: 1 });
  const code = rd.room?.code;
  if (!code) { console.log('  FATAL: Room creation failed:', JSON.stringify(rd)); return; }
  console.log('  Room:', code);

  await joinRoom(code, bob.guest_token);
  await joinRoom(code, charlie.guest_token);

  const as = await connectSocket();
  const bs = await connectSocket();
  const cs = await connectSocket();
  allSockets.push(as, bs, cs);

  await registerSocket(as, code, alice.guest_token);
  await registerSocket(bs, code, bob.guest_token);
  await registerSocket(cs, code, charlie.guest_token);
  console.log('  All 3 players registered');

  // Start the game
  const aTurnP = waitFor(as, 'game:turn_start');
  const bTurnP = waitFor(bs, 'game:turn_start');
  const cTurnP = waitFor(cs, 'game:turn_start');
  const aQP = waitFor(as, 'trivia:question');
  const bQP = waitFor(bs, 'trivia:question');
  const cQP = waitFor(cs, 'trivia:question');

  as.emit('game:start', { room_code: code, guest_token: alice.guest_token });
  await Promise.all([aTurnP, bTurnP, cTurnP]);
  const [aQ, bQ, cQ] = await Promise.all([aQP, bQP, cQP]);

  check('T3: All 3 received question #0', aQ?.question_index === 0 && bQ?.question_index === 0 && cQ?.question_index === 0);
  check('T3: All 3 got same question text', aQ?.question_text === bQ?.question_text && bQ?.question_text === cQ?.question_text);
  check('T3: All 3 got same options', JSON.stringify(aQ?.options) === JSON.stringify(bQ?.options) && JSON.stringify(bQ?.options) === JSON.stringify(cQ?.options));

  // Have all 3 answer, one at a time, and check answer_update progression
  // Collect answer_updates from Alice's perspective
  const updates = [];
  as.on('trivia:answer_update', (data) => updates.push(data));

  // Also set up result listeners
  const aResP = waitFor(as, 'trivia:question_result', 15000);
  const bResP = waitFor(bs, 'trivia:question_result', 15000);
  const cResP = waitFor(cs, 'trivia:question_result', 15000);

  // Alice answers first
  as.emit('trivia:answer', { room_code: code, answer_index: 0 });
  await sleep(500);

  // Bob answers second
  bs.emit('trivia:answer', { room_code: code, answer_index: 1 });
  await sleep(500);

  // Charlie answers third (should trigger result since all 3 have answered)
  cs.emit('trivia:answer', { room_code: code, answer_index: 0 });

  const [aRes, bRes, cRes] = await Promise.all([aResP, bResP, cResP]);

  // Check answer_update progression
  as.off('trivia:answer_update');
  check('T3: Received at least 2 answer_updates', updates.length >= 2, `got ${updates.length} updates`);
  if (updates.length >= 1) {
    check('T3: First update: answered_count=1', updates[0]?.answered_count === 1, `got ${updates[0]?.answered_count}`);
    check('T3: First update: total_players=3', updates[0]?.total_players === 3, `got ${updates[0]?.total_players}`);
  }
  if (updates.length >= 2) {
    check('T3: Second update: answered_count=2', updates[1]?.answered_count === 2, `got ${updates[1]?.answered_count}`);
  }

  // Check question_result
  check('T3: Result has 3 player_results', aRes?.player_results?.length === 3, `got ${aRes?.player_results?.length}`);
  check('T3: Alice result matches Bob result (correct_index)', aRes?.correct_index === bRes?.correct_index);
  check('T3: Alice result matches Charlie result (correct_index)', aRes?.correct_index === cRes?.correct_index);

  // Verify scores has 3 entries
  check('T3: Scores has 3 players', typeof aRes?.scores === 'object' && Object.keys(aRes.scores).length === 3, `got ${Object.keys(aRes?.scores || {}).length}`);

  as.disconnect();
  bs.disconnect();
  cs.disconnect();
  console.log('  Test 3 cleanup done');
}

// ============================================================
// TEST 4: Different difficulties (medium and hard timer values)
// ============================================================
async function test4_difficulties() {
  console.log('\n========================================');
  console.log('TEST 4: Different Difficulties');
  console.log('========================================');

  // --- Medium (difficulty=2) ---
  console.log('\n  --- Medium (difficulty=2) ---');
  const aliceM = await createGuest('AliceMed');
  const bobM = await createGuest('BobMed');

  const rdM = await createRoom(aliceM.guest_token, { rounds: 1, difficulty: 2 });
  const codeM = rdM.room?.code;
  if (!codeM) { console.log('  FATAL: Medium room creation failed:', JSON.stringify(rdM)); return; }
  console.log('  Room:', codeM, '(medium)');

  await joinRoom(codeM, bobM.guest_token);

  const asM = await connectSocket();
  const bsM = await connectSocket();
  allSockets.push(asM, bsM);

  await registerSocket(asM, codeM, aliceM.guest_token);
  await registerSocket(bsM, codeM, bobM.guest_token);

  const mTurnP = waitFor(asM, 'game:turn_start');
  const mQP = waitFor(asM, 'trivia:question');
  asM.emit('game:start', { room_code: codeM, guest_token: aliceM.guest_token });
  await mTurnP;
  const mQ = await mQP;
  check('T4: Medium time_seconds is 15', mQ?.time_seconds === 15, `got ${mQ?.time_seconds}`);

  asM.disconnect();
  bsM.disconnect();

  // --- Hard (difficulty=3) ---
  console.log('\n  --- Hard (difficulty=3) ---');
  const aliceH = await createGuest('AliceHard');
  const bobH = await createGuest('BobHard');

  const rdH = await createRoom(aliceH.guest_token, { rounds: 1, difficulty: 3 });
  const codeH = rdH.room?.code;
  if (!codeH) { console.log('  FATAL: Hard room creation failed:', JSON.stringify(rdH)); return; }
  console.log('  Room:', codeH, '(hard)');

  await joinRoom(codeH, bobH.guest_token);

  const asH = await connectSocket();
  const bsH = await connectSocket();
  allSockets.push(asH, bsH);

  await registerSocket(asH, codeH, aliceH.guest_token);
  await registerSocket(bsH, codeH, bobH.guest_token);

  const hTurnP = waitFor(asH, 'game:turn_start');
  const hQP = waitFor(asH, 'trivia:question');
  asH.emit('game:start', { room_code: codeH, guest_token: aliceH.guest_token });
  await hTurnP;
  const hQ = await hQP;
  check('T4: Hard time_seconds is 10', hQ?.time_seconds === 10, `got ${hQ?.time_seconds}`);

  asH.disconnect();
  bsH.disconnect();
  console.log('  Test 4 cleanup done');
}

// ============================================================
// MAIN
// ============================================================
async function main() {
  console.log('=== TRIVIA EDGE-CASE TESTS ===');
  console.log(`API: ${API}`);
  console.log(`Started at: ${new Date().toISOString()}\n`);

  try {
    await test1_timerTimeout();
    await sleep(2000);
    await test2_partialTimeout();
    await sleep(2000);
    await test3_threePlayers();
    await sleep(2000);
    await test4_difficulties();
  } catch (err) {
    console.error('\nFATAL ERROR:', err.message);
    console.error(err.stack);
  } finally {
    // Cleanup any remaining sockets
    for (const s of allSockets) {
      if (s.connected) s.disconnect();
    }
  }

  console.log('\n========================================');
  console.log('SUMMARY');
  console.log('========================================');
  console.log(`  Total:  ${pass + fail}`);
  console.log(`  Passed: ${pass}`);
  console.log(`  Failed: ${fail}`);
  console.log('========================================');
  console.log(`Finished at: ${new Date().toISOString()}`);

  process.exit(fail > 0 ? 1 : 0);
}

main();
