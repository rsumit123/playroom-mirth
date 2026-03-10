import { io } from 'socket.io-client';

const API = 'https://charade-api.skdev.one';

function waitFor(socket, event, timeoutMs = 10000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`Timeout waiting for ${event}`)), timeoutMs);
    socket.once(event, (p) => { clearTimeout(timer); resolve(p); });
  });
}

async function test() {
  console.log('=== TRIVIA GAME FULL E2E TEST ===\n');
  let pass = 0, fail = 0;
  function check(name, cond, detail = '') {
    if (cond) { pass++; console.log('  PASS:', name, detail ? '— ' + detail : ''); }
    else { fail++; console.log('  FAIL:', name, detail ? '— ' + detail : ''); }
  }

  // ── Setup ──
  const h = await (await fetch(API + '/guest', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ display_name: 'Alice' }) })).json();
  const g = await (await fetch(API + '/guest', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ display_name: 'Bob' }) })).json();
  console.log('Guests: Alice + Bob');

  const rd = await (await fetch(API + '/rooms/guest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ guest_token: h.guest_token, game_type: 'trivia', rounds_total: 1, difficulty: 1, turn_seconds: 0 })
  })).json();
  const code = rd.room?.code;
  console.log('Room:', code, '(trivia, 1 round, easy)');
  if (!code) { console.log('FATAL: Room creation failed:', JSON.stringify(rd)); process.exit(1); }

  await fetch(API + '/rooms/join', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ room_code: code, guest_token: g.guest_token })
  });

  const hs = io(API, { transports: ['websocket'] });
  const gs = io(API, { transports: ['websocket'] });
  await Promise.all([new Promise(r => hs.on('connect', r)), new Promise(r => gs.on('connect', r))]);

  const errors = [];
  hs.on('error', e => errors.push({ who: 'Alice', ...e }));
  gs.on('error', e => errors.push({ who: 'Bob', ...e }));

  hs.emit('room:register', { room_code: code, guest_token: h.guest_token });
  await waitFor(hs, 'room:lobby_update');
  gs.emit('room:register', { room_code: code, guest_token: g.guest_token });
  await waitFor(gs, 'room:lobby_update');
  console.log('Both registered\n');

  // ── Test 1: Game start ──
  console.log('--- Test 1: Game Start ---');
  // Set up ALL listeners before starting
  const hTurnP = waitFor(hs, 'game:turn_start');
  const gTurnP = waitFor(gs, 'game:turn_start');
  const hQ1P = waitFor(hs, 'trivia:question');
  const gQ1P = waitFor(gs, 'trivia:question');

  hs.emit('game:start', { room_code: code, guest_token: h.guest_token });

  const [hTurn, gTurn] = await Promise.all([hTurnP, gTurnP]);
  check('Host received turn_start', !!hTurn);
  check('Guest received turn_start', !!gTurn);
  check('game_type is trivia', hTurn?.game_type === 'trivia');
  check('describer_id is -1', hTurn?.describer_id === -1);
  check('round_index is 1', hTurn?.round_index === 1);

  const [hQ1, gQ1] = await Promise.all([hQ1P, gQ1P]);
  check('Host received question #0', hQ1?.question_index === 0);
  check('Guest received question #0', gQ1?.question_index === 0);
  check('Question has text', typeof hQ1?.question_text === 'string' && hQ1.question_text.length > 0, hQ1?.question_text);
  check('Question has 4 options', hQ1?.options?.length === 4);
  check('Question has time_seconds > 0', hQ1?.time_seconds > 0, String(hQ1?.time_seconds));
  check('total_questions is 10', hQ1?.total_questions === 10);
  check('Questions match', hQ1?.question_text === gQ1?.question_text);

  // ── Test 2: Answer submission + updates ──
  console.log('\n--- Test 2: Answer Submission ---');
  const hUpdateP = waitFor(hs, 'trivia:answer_update');
  hs.emit('trivia:answer', { room_code: code, answer_index: 0 });
  const hUpdate = await hUpdateP;
  check('Answer update: 1 of 2', hUpdate?.answered_count === 1 && hUpdate?.total_players === 2);

  // Double-answer prevention
  const doubleRes = await new Promise(resolve => {
    hs.emit('trivia:answer', { room_code: code, answer_index: 1 }, resolve);
  });
  check('Double answer rejected', doubleRes?.error === 'ALREADY_ANSWERED' || doubleRes?.ok === false);

  // Bob answers → triggers result
  const hResultP = waitFor(hs, 'trivia:question_result');
  const gResultP = waitFor(gs, 'trivia:question_result');
  gs.emit('trivia:answer', { room_code: code, answer_index: 0 });
  const [hResult, gResult] = await Promise.all([hResultP, gResultP]);
  check('Result has correct_index 0-3', hResult?.correct_index >= 0 && hResult?.correct_index <= 3);
  check('Result has 2 player_results', hResult?.player_results?.length === 2);
  check('Result has scores', typeof hResult?.scores === 'object' && Object.keys(hResult.scores).length === 2);
  check('Results match', hResult?.correct_index === gResult?.correct_index);

  for (const pr of hResult?.player_results || []) {
    check(`Player ${pr.player_id} valid result`, typeof pr.correct === 'boolean' && typeof pr.points === 'number');
    if (pr.correct) {
      check(`Correct: 100+ pts`, pr.points >= 100, String(pr.points));
    }
  }

  // ── Test 3: Full round — play through remaining 9 questions ──
  console.log('\n--- Test 3: Full Round (questions 1-9) ---');
  let questionsPlayed = 1;

  for (let qi = 1; qi < 10; qi++) {
    // Set up listeners BEFORE the 4s pause ends
    const hNextQP = waitFor(hs, 'trivia:question', 15000);
    const gNextQP = waitFor(gs, 'trivia:question', 15000);
    const [hNextQ, gNextQ] = await Promise.all([hNextQP, gNextQP]);
    questionsPlayed++;

    if (qi === 1 || qi === 5 || qi === 9) {
      check(`Q${qi}: index=${hNextQ?.question_index}`, hNextQ?.question_index === qi);
      check(`Q${qi}: both match`, hNextQ?.question_text === gNextQ?.question_text);
    }

    // Both answer
    const hResP = waitFor(hs, 'trivia:question_result', 15000);
    const gResP = waitFor(gs, 'trivia:question_result', 15000);
    hs.emit('trivia:answer', { room_code: code, answer_index: 0 });
    gs.emit('trivia:answer', { room_code: code, answer_index: 0 });
    await Promise.all([hResP, gResP]);
  }
  check('All 10 questions played', questionsPlayed === 10, String(questionsPlayed));

  // ── Test 4: Game end (1 round) ──
  console.log('\n--- Test 4: Game End ---');
  const hGameEndP = waitFor(hs, 'game:game_end', 15000);
  const gGameEndP = waitFor(gs, 'game:game_end', 15000);
  const [hGameEnd, gGameEnd] = await Promise.all([hGameEndP, gGameEndP]);
  check('Host received game_end', !!hGameEnd);
  check('Guest received game_end', !!gGameEnd);
  check('Game end has scores', typeof hGameEnd?.scores === 'object' && Object.keys(hGameEnd.scores).length === 2);
  check('Scores match', JSON.stringify(hGameEnd?.scores) === JSON.stringify(gGameEnd?.scores));

  hs.disconnect();
  gs.disconnect();

  // ── Test 5: Multi-round game ──
  console.log('\n--- Test 5: Multi-Round (2 rounds) ---');
  const rd2 = await (await fetch(API + '/rooms/guest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ guest_token: h.guest_token, game_type: 'trivia', rounds_total: 2, difficulty: 1, turn_seconds: 0 })
  })).json();
  const code2 = rd2.room?.code;
  if (!code2) { console.log('FATAL: Room 2 failed'); process.exit(1); }
  console.log('Room2:', code2);

  await fetch(API + '/rooms/join', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ room_code: code2, guest_token: g.guest_token })
  });

  const hs2 = io(API, { transports: ['websocket'] });
  const gs2 = io(API, { transports: ['websocket'] });
  await Promise.all([new Promise(r => hs2.on('connect', r)), new Promise(r => gs2.on('connect', r))]);
  hs2.on('error', e => errors.push({ who: 'Alice2', ...e }));
  gs2.on('error', e => errors.push({ who: 'Bob2', ...e }));

  hs2.emit('room:register', { room_code: code2, guest_token: h.guest_token });
  await waitFor(hs2, 'room:lobby_update');
  gs2.emit('room:register', { room_code: code2, guest_token: g.guest_token });
  await waitFor(gs2, 'room:lobby_update');

  // Start — set up question listener before start
  let hQ2P = waitFor(hs2, 'trivia:question', 15000);
  hs2.emit('game:start', { room_code: code2, guest_token: h.guest_token });

  // Play round 1 (10 questions)
  for (let qi = 0; qi < 10; qi++) {
    if (qi > 0) hQ2P = waitFor(hs2, 'trivia:question', 15000);
    await hQ2P;
    const resP = waitFor(hs2, 'trivia:question_result', 15000);
    hs2.emit('trivia:answer', { room_code: code2, answer_index: 0 });
    gs2.emit('trivia:answer', { room_code: code2, answer_index: 0 });
    await resP;
  }

  const roundEnd = await waitFor(hs2, 'game:round_end', 15000);
  check('Round 1 end received', !!roundEnd);
  check('Round end has scores', typeof roundEnd?.scores === 'object');

  // Host triggers next round — must emit game:turn_start (navigation trigger) + trivia:question
  const hR2TurnP = waitFor(hs2, 'game:turn_start', 15000);
  const gR2TurnP = waitFor(gs2, 'game:turn_start', 15000);
  const hR2QP = waitFor(hs2, 'trivia:question', 15000);
  const gR2QP = waitFor(gs2, 'trivia:question', 15000);
  hs2.emit('game:next_round', { room_code: code2, guest_token: h.guest_token });
  const [hR2Turn, gR2Turn] = await Promise.all([hR2TurnP, gR2TurnP]);
  check('Next round: host got turn_start', !!hR2Turn);
  check('Next round: guest got turn_start', !!gR2Turn);
  check('Next round: game_type=trivia', hR2Turn?.game_type === 'trivia');
  check('Next round: describer_id=-1', hR2Turn?.describer_id === -1);
  const [r2q, gR2Q] = await Promise.all([hR2QP, gR2QP]);
  check('Round 2: question_index=0', r2q?.question_index === 0);
  check('Round 2: guest got question too', gR2Q?.question_index === 0);

  // Play round 2 (10 questions)
  for (let qi = 0; qi < 10; qi++) {
    if (qi > 0) await waitFor(hs2, 'trivia:question', 15000);
    const resP = waitFor(hs2, 'trivia:question_result', 15000);
    hs2.emit('trivia:answer', { room_code: code2, answer_index: 0 });
    gs2.emit('trivia:answer', { room_code: code2, answer_index: 0 });
    await resP;
  }

  const gameEnd2 = await waitFor(hs2, 'game:game_end', 15000);
  check('Game end after 2 rounds', !!gameEnd2);
  check('Final scores present', typeof gameEnd2?.scores === 'object' && Object.keys(gameEnd2.scores).length === 2);

  hs2.disconnect();
  gs2.disconnect();

  // ── Summary ──
  if (errors.length > 0) {
    console.log('\n  Socket errors:');
    errors.forEach(e => console.log('    -', e.who, ':', e.message || JSON.stringify(e)));
  }

  console.log('\n  Total:', pass + fail, '| Passed:', pass, '| Failed:', fail);
  console.log('=== DONE ===');
  process.exit(fail > 0 ? 1 : 0);
}
test().catch(e => { console.error('FATAL:', e); process.exit(1); });
