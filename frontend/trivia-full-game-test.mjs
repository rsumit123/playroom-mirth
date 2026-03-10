import { io } from 'socket.io-client';

const API = 'https://charade-api.skdev.one';
const TOTAL_ROUNDS = 5;
const QUESTIONS_PER_ROUND = 10;

function waitFor(socket, event, timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error(`Timeout waiting for "${event}" after ${timeoutMs}ms`)),
      timeoutMs
    );
    socket.once(event, (payload) => { clearTimeout(timer); resolve(payload); });
  });
}

async function test() {
  console.log('=== TRIVIA FULL 5-ROUND GAME TEST (2 Players) ===\n');
  let pass = 0, fail = 0;
  const errors = [];

  function check(name, cond, detail = '') {
    if (cond) { pass++; console.log('  PASS:', name, detail ? '-- ' + detail : ''); }
    else      { fail++; console.log('  FAIL:', name, detail ? '-- ' + detail : ''); }
  }

  // ── 1. Create 2 guests ──────────────────────────────────────
  console.log('--- 1. Create guests ---');
  const alice = await (await fetch(API + '/guest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ display_name: 'Alice' })
  })).json();
  const bob = await (await fetch(API + '/guest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ display_name: 'Bob' })
  })).json();
  check('Alice guest created', !!alice.guest_token);
  check('Bob guest created', !!bob.guest_token);

  // ── 2. Create trivia room ───────────────────────────────────
  console.log('\n--- 2. Create room (5 rounds, easy, turn_seconds=0) ---');
  const roomRes = await (await fetch(API + '/rooms/guest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      guest_token: alice.guest_token,
      game_type: 'trivia',
      rounds_total: TOTAL_ROUNDS,
      difficulty: 1,
      turn_seconds: 0
    })
  })).json();
  const code = roomRes.room?.code;
  check('Room created', !!code, `code=${code}`);
  if (!code) { console.log('FATAL: Room creation failed:', JSON.stringify(roomRes)); process.exit(1); }

  // ── 3. Bob joins ────────────────────────────────────────────
  console.log('\n--- 3. Bob joins ---');
  await fetch(API + '/rooms/join', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ room_code: code, guest_token: bob.guest_token })
  });

  // ── 4. Connect sockets + register ──────────────────────────
  console.log('\n--- 4. Connect sockets + register ---');
  const hs = io(API, { transports: ['websocket'] });
  const gs = io(API, { transports: ['websocket'] });
  await Promise.all([
    new Promise(r => hs.on('connect', r)),
    new Promise(r => gs.on('connect', r))
  ]);
  check('Both sockets connected', hs.connected && gs.connected);

  hs.on('error', e => errors.push({ who: 'Alice', ...(typeof e === 'object' ? e : { message: e }) }));
  gs.on('error', e => errors.push({ who: 'Bob', ...(typeof e === 'object' ? e : { message: e }) }));

  hs.emit('room:register', { room_code: code, guest_token: alice.guest_token });
  await waitFor(hs, 'room:lobby_update');
  gs.emit('room:register', { room_code: code, guest_token: bob.guest_token });
  await waitFor(gs, 'room:lobby_update');
  check('Both registered in lobby', true);

  // ── 5. Start the game ───────────────────────────────────────
  console.log('\n--- 5. Start game ---');
  const hTurnP  = waitFor(hs, 'game:turn_start', 15000);
  const gTurnP  = waitFor(gs, 'game:turn_start', 15000);
  const hQ0P    = waitFor(hs, 'trivia:question', 15000);
  const gQ0P    = waitFor(gs, 'trivia:question', 15000);

  hs.emit('game:start', { room_code: code, guest_token: alice.guest_token });

  const [hTurn, gTurn] = await Promise.all([hTurnP, gTurnP]);
  check('Alice got turn_start', !!hTurn);
  check('Bob got turn_start', !!gTurn);
  check('game_type is trivia', hTurn?.game_type === 'trivia');
  check('round_index is 1', hTurn?.round_index === 1);

  // First question of round 1
  let [pendingHQ, pendingGQ] = await Promise.all([hQ0P, gQ0P]);

  // ── 6. Play all 5 rounds ────────────────────────────────────
  const allRoundQuestions = []; // track question texts per round
  const cumulativeScores = {};  // track scores accumulating across rounds

  for (let round = 1; round <= TOTAL_ROUNDS; round++) {
    console.log(`\n====== Round ${round} of ${TOTAL_ROUNDS} ======`);
    const roundQuestions = [];

    for (let qi = 0; qi < QUESTIONS_PER_ROUND; qi++) {
      // Get the current question (either pre-fetched or waited for)
      let hQ, gQ;
      if (pendingHQ && pendingGQ) {
        // First question of this round was pre-fetched
        hQ = pendingHQ;
        gQ = pendingGQ;
        pendingHQ = null;
        pendingGQ = null;
      } else {
        // Wait for the next question (sent after result pause)
        const hQP = waitFor(hs, 'trivia:question', 20000);
        const gQP = waitFor(gs, 'trivia:question', 20000);
        [hQ, gQ] = await Promise.all([hQP, gQP]);
      }

      roundQuestions.push(hQ?.question_text);

      // Validate first and last question of each round
      if (qi === 0) {
        check(`R${round} Q0: question_index=0`, hQ?.question_index === 0);
        check(`R${round} Q0: total_questions=${QUESTIONS_PER_ROUND}`, hQ?.total_questions === QUESTIONS_PER_ROUND);
        check(`R${round} Q0: has 4 options`, hQ?.options?.length === 4);
        check(`R${round} Q0: both players got same question`, hQ?.question_text === gQ?.question_text);
        check(`R${round} Q0: has question text`, typeof hQ?.question_text === 'string' && hQ.question_text.length > 0,
          hQ?.question_text?.slice(0, 60));
      }
      if (qi === 9) {
        check(`R${round} Q9: question_index=9`, hQ?.question_index === 9);
      }

      // Both players answer
      const hRP = waitFor(hs, 'trivia:question_result', 15000);
      const gRP = waitFor(gs, 'trivia:question_result', 15000);
      hs.emit('trivia:answer', { room_code: code, answer_index: 0 });
      gs.emit('trivia:answer', { room_code: code, answer_index: 0 });
      const [hResult, gResult] = await Promise.all([hRP, gRP]);

      if (qi === 0) {
        check(`R${round} Q0 result: correct_index in 0-3`, hResult?.correct_index >= 0 && hResult?.correct_index <= 3);
        check(`R${round} Q0 result: 2 player_results`, hResult?.player_results?.length === 2);
        check(`R${round} Q0 result: has scores object`, typeof hResult?.scores === 'object');
        check(`R${round} Q0 result: results match between players`, hResult?.correct_index === gResult?.correct_index);
      }

      if ((qi + 1) % 5 === 0) {
        console.log(`  Completed question ${qi + 1}/${QUESTIONS_PER_ROUND}`);
      }
    }

    allRoundQuestions.push(roundQuestions);
    check(`R${round}: played all ${QUESTIONS_PER_ROUND} questions`, roundQuestions.length === QUESTIONS_PER_ROUND);

    // Check uniqueness within the round
    const uniqueSet = new Set(roundQuestions);
    check(`R${round}: ${QUESTIONS_PER_ROUND} unique questions (no duplicates)`, uniqueSet.size === QUESTIONS_PER_ROUND,
      `unique=${uniqueSet.size} of ${roundQuestions.length}`);

    // ── After last question: expect round_end or game_end ──
    if (round < TOTAL_ROUNDS) {
      // Rounds 1-4: expect round_end
      console.log(`  Waiting for game:round_end...`);
      const hRoundEndP = waitFor(hs, 'game:round_end', 15000);
      const gRoundEndP = waitFor(gs, 'game:round_end', 15000);
      const [hRE, gRE] = await Promise.all([hRoundEndP, gRoundEndP]);

      check(`R${round}: Alice got round_end`, !!hRE);
      check(`R${round}: Bob got round_end`, !!gRE);
      check(`R${round}: round_end has scores (2 players)`,
        typeof hRE?.scores === 'object' && Object.keys(hRE.scores).length === 2);
      check(`R${round}: both players' round_end scores match`,
        JSON.stringify(hRE?.scores) === JSON.stringify(gRE?.scores));

      // Track cumulative scores
      const currentScores = hRE?.scores || {};
      if (round === 1) {
        // First round: just store the scores
        for (const [pid, s] of Object.entries(currentScores)) {
          cumulativeScores[pid] = s;
        }
      } else {
        // Subsequent rounds: scores should be >= previous (cumulative)
        let scoresAccumulate = true;
        for (const [pid, s] of Object.entries(currentScores)) {
          if (s < (cumulativeScores[pid] || 0)) {
            scoresAccumulate = false;
          }
          cumulativeScores[pid] = s;
        }
        check(`R${round}: scores >= previous round (accumulating)`, scoresAccumulate);
      }

      // Print scores
      for (const [pid, s] of Object.entries(currentScores)) {
        console.log(`    Player ${pid}: ${s} pts`);
      }

      // Trigger next round
      console.log(`  Emitting game:next_round for round ${round + 1}...`);
      const hNextTurnP = waitFor(hs, 'game:turn_start', 15000);
      const gNextTurnP = waitFor(gs, 'game:turn_start', 15000);
      const hNextQP = waitFor(hs, 'trivia:question', 15000);
      const gNextQP = waitFor(gs, 'trivia:question', 15000);

      hs.emit('game:next_round', { room_code: code, guest_token: alice.guest_token });

      const [hNextTurn, gNextTurn] = await Promise.all([hNextTurnP, gNextTurnP]);
      check(`R${round + 1}: Alice got turn_start`, !!hNextTurn);
      check(`R${round + 1}: Bob got turn_start`, !!gNextTurn);
      check(`R${round + 1}: round_index=${round + 1}`, hNextTurn?.round_index === round + 1);
      check(`R${round + 1}: game_type=trivia`, hNextTurn?.game_type === 'trivia');
      check(`R${round + 1}: describer_id=-1`, hNextTurn?.describer_id === -1);

      // Pre-fetch the first question of the next round (already set up above)
      [pendingHQ, pendingGQ] = await Promise.all([hNextQP, gNextQP]);

    } else {
      // Round 5 (final): expect game_end
      console.log(`  Waiting for game:game_end...`);
      const hGameEndP = waitFor(hs, 'game:game_end', 15000);
      const gGameEndP = waitFor(gs, 'game:game_end', 15000);
      const [hGE, gGE] = await Promise.all([hGameEndP, gGameEndP]);

      check('Game end: Alice received', !!hGE);
      check('Game end: Bob received', !!gGE);
      check('Game end: has scores (2 players)',
        typeof hGE?.scores === 'object' && Object.keys(hGE.scores).length === 2);
      check('Game end: both players see same scores',
        JSON.stringify(hGE?.scores) === JSON.stringify(gGE?.scores));

      // Verify final scores >= last round's scores (they should be cumulative)
      const finalScores = hGE?.scores || {};
      let finalAccumulates = true;
      for (const [pid, s] of Object.entries(finalScores)) {
        if (s < (cumulativeScores[pid] || 0)) {
          finalAccumulates = false;
        }
      }
      check('Game end: final scores >= round 4 scores (cumulative)', finalAccumulates);

      // Print final scores
      console.log('\n  --- Final Scores ---');
      for (const [pid, s] of Object.entries(finalScores)) {
        console.log(`    Player ${pid}: ${s} pts`);
      }
    }
  }

  // ── 7. Question variety check ───────────────────────────────
  console.log('\n--- 7. Question variety summary ---');
  // Already checked per-round uniqueness above; also check cross-round stats
  const allQuestions = allRoundQuestions.flat();
  const totalUnique = new Set(allQuestions).size;
  console.log(`  Total questions asked: ${allQuestions.length}`);
  console.log(`  Total unique questions: ${totalUnique}`);
  check('50 total questions played (5 rounds x 10)', allQuestions.length === 50);
  // Cross-round duplicates are allowed (question pool may not have 50 unique easy questions),
  // but within each round all 10 should be unique (already checked per round above).

  // ── Cleanup ─────────────────────────────────────────────────
  hs.disconnect();
  gs.disconnect();

  // ── Summary ─────────────────────────────────────────────────
  if (errors.length > 0) {
    console.log('\n  Socket errors encountered:');
    errors.forEach(e => console.log('    -', e.who, ':', e.message || JSON.stringify(e)));
  }

  console.log('\n' + '='.repeat(50));
  console.log(`  Total: ${pass + fail} | Passed: ${pass} | Failed: ${fail}`);
  console.log('='.repeat(50));
  process.exit(fail > 0 ? 1 : 0);
}

test().catch(e => { console.error('FATAL:', e); process.exit(1); });
