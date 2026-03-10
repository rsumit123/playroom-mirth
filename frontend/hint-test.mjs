import { io } from 'socket.io-client';

const API = 'https://charade-api.skdev.one';

async function test() {
  console.log('=== HINT FEATURE E2E TEST ===\n');
  let pass = 0, fail = 0;
  function check(name, cond, detail = '') {
    if (cond) { pass++; console.log('  PASS:', name, detail ? '— ' + detail : ''); }
    else { fail++; console.log('  FAIL:', name, detail ? '— ' + detail : ''); }
  }

  // Create guests
  const h = await (await fetch(API + '/guest', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ display_name: 'Alice' }) })).json();
  const g = await (await fetch(API + '/guest', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ display_name: 'Bob' }) })).json();
  console.log('Guests created');

  // Create room via POST /rooms/guest with guest_token in body
  const roomRes = await fetch(API + '/rooms/guest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ guest_token: h.guest_token, game_type: 'charades', rounds_total: 1, difficulty: 2, turn_seconds: 30 })
  });
  const rd = await roomRes.json();
  const code = rd.room?.code;
  console.log('Room:', code);
  if (!code) { console.log('FAIL: Room creation failed:', JSON.stringify(rd)); process.exit(1); }

  // Guest Bob joins the room via REST
  const joinRes = await fetch(API + '/rooms/join', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ room_code: code, guest_token: g.guest_token })
  });
  const joinData = await joinRes.json();
  console.log('Bob joined room:', joinRes.ok ? 'OK' : JSON.stringify(joinData));

  // Connect sockets
  const hs = io(API, { transports: ['websocket'] });
  const gs = io(API, { transports: ['websocket'] });
  await Promise.all([new Promise(r => hs.on('connect', r)), new Promise(r => gs.on('connect', r))]);
  console.log('Sockets connected');

  // Collect events (set up BEFORE register so we catch everything)
  let hTurn = null, gTurn = null, describerWord = null, hintEvt = null;
  let hLobby = null, gLobby = null;
  hs.on('game:turn_start', p => { hTurn = p; });
  gs.on('game:turn_start', p => { gTurn = p; });
  hs.on('game:new_word', p => { describerWord = p.word; });
  gs.on('game:new_word', p => { if (describerWord === null) describerWord = p.word; });
  hs.on('game:hint', p => { hintEvt = p; });
  gs.on('game:hint', p => { if (hintEvt === null) hintEvt = p; });
  hs.on('error', e => console.log('Host error:', JSON.stringify(e)));
  gs.on('error', e => console.log('Guest error:', JSON.stringify(e)));

  // Register and wait for lobby confirmations
  const hLobbyP = new Promise(r => hs.once('room:lobby_update', p => { hLobby = p; r(); }));
  hs.emit('room:register', { room_code: code, guest_token: h.guest_token });
  await hLobbyP;
  console.log('Host registered');

  const gLobbyP = new Promise(r => gs.once('room:lobby_update', p => { gLobby = p; r(); }));
  gs.emit('room:register', { room_code: code, guest_token: g.guest_token });
  await gLobbyP;
  console.log('Guest registered');

  // Start game (include guest_token for auth)
  console.log('Starting game...');
  hs.emit('game:start', { room_code: code, guest_token: h.guest_token });
  await new Promise(r => setTimeout(r, 3000));

  console.log('');
  // Test 1: Both players received turn_start
  check('Host received turn_start', !!hTurn);
  check('Guest received turn_start', !!gTurn);

  // Test 2: Both turn_start payloads include hint
  check('Host turn_start has hint', !!hTurn?.hint, hTurn?.hint || 'null');
  check('Guest turn_start has hint', !!gTurn?.hint, gTurn?.hint || 'null');

  // Test 3: Hints match between host and guest
  check('Hints match between players', hTurn?.hint === gTurn?.hint);

  // Test 4: Hint format correct
  const hint = hTurn?.hint || gTurn?.hint;
  if (hint) {
    const parts = hint.split('  ');
    let formatOk = true;
    for (const part of parts) {
      const chars = part.split(' ');
      if (!/^[A-Z]$/.test(chars[0])) formatOk = false;
      for (let i = 1; i < chars.length; i++) if (chars[i] !== '_') formatOk = false;
    }
    check('Hint format valid (A _ _ pattern)', formatOk, hint);
  } else {
    check('Hint format valid', false, 'no hint to validate');
  }

  // Test 5: If describer got word, verify hint matches
  if (describerWord && hint) {
    const expected = describerWord.split(' ').filter(Boolean).map(w =>
      [w[0].toUpperCase(), ...'_'.repeat(w.length - 1).split('')].join(' ')
    ).join('  ');
    check('Hint matches actual word', hint === expected, `word="${describerWord}" -> "${expected}"`);
  }

  // Test 6: game_type in turn
  check('Turn has game_type', !!(hTurn?.game_type || gTurn?.game_type), hTurn?.game_type || gTurn?.game_type);

  hs.disconnect();
  gs.disconnect();
  console.log('\n  Total:', pass + fail, '| Passed:', pass, '| Failed:', fail);
  console.log('=== DONE ===');
  process.exit(fail > 0 ? 1 : 0);
}
test().catch(e => { console.error(e); process.exit(1); });
