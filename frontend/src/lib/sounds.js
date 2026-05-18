// Web Audio API sound synthesis — zero audio files, zero dependencies
let ctx = null
let muted = false

try {
  muted = localStorage.getItem('charade_sounds_muted') === 'true'
} catch { /* ignore */ }

/** Call from a user gesture (click/tap) to unlock AudioContext on mobile */
export function initAudio() {
  if (ctx) return
  try {
    ctx = new (window.AudioContext || window.webkitAudioContext)()
    if (ctx.state === 'suspended') ctx.resume()
  } catch { /* browser doesn't support Web Audio */ }
}

/** Play a named sound effect. No-ops if muted or AudioContext not ready. */
export function playSound(name) {
  if (muted || !ctx) return
  if (ctx.state === 'suspended') ctx.resume()
  const fn = SOUNDS[name]
  if (fn) {
    try { fn(ctx) } catch { /* swallow audio errors */ }
  }
}

export function toggleMute() {
  muted = !muted
  try { localStorage.setItem('charade_sounds_muted', String(muted)) } catch { /* ignore */ }
  return muted
}

export function isMuted() {
  return muted
}

// --- Sound definitions ---

function playTurnStart(ctx) {
  const now = ctx.currentTime
  const notes = [523.25, 659.25] // C5, E5
  notes.forEach((freq, i) => {
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.value = freq
    const t = now + i * 0.08
    gain.gain.setValueAtTime(0.25, t)
    gain.gain.exponentialRampToValueAtTime(0.01, t + 0.15)
    osc.connect(gain).connect(ctx.destination)
    osc.start(t)
    osc.stop(t + 0.15)
  })
}

function playCorrectGuess(ctx) {
  const now = ctx.currentTime
  const notes = [523.25, 659.25, 783.99] // C5, E5, G5
  notes.forEach((freq, i) => {
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'triangle'
    osc.frequency.value = freq
    const t = now + i * 0.06
    gain.gain.setValueAtTime(0.3, t)
    gain.gain.exponentialRampToValueAtTime(0.01, t + 0.18)
    osc.connect(gain).connect(ctx.destination)
    osc.start(t)
    osc.stop(t + 0.18)
  })
}

function playTick(ctx) {
  const now = ctx.currentTime
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  osc.type = 'square'
  osc.frequency.value = 800
  gain.gain.setValueAtTime(0.12, now)
  gain.gain.exponentialRampToValueAtTime(0.01, now + 0.05)
  osc.connect(gain).connect(ctx.destination)
  osc.start(now)
  osc.stop(now + 0.05)
}

function playTimesUp(ctx) {
  const now = ctx.currentTime
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  osc.type = 'sawtooth'
  osc.frequency.setValueAtTime(440, now) // A4
  osc.frequency.exponentialRampToValueAtTime(220, now + 0.4) // A3
  gain.gain.setValueAtTime(0.2, now)
  gain.gain.exponentialRampToValueAtTime(0.01, now + 0.4)
  osc.connect(gain).connect(ctx.destination)
  osc.start(now)
  osc.stop(now + 0.4)
}

function playRoundEnd(ctx) {
  const now = ctx.currentTime
  const notes = [523.25, 659.25, 783.99, 1046.5] // C5, E5, G5, C6
  notes.forEach((freq, i) => {
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'triangle'
    osc.frequency.value = freq
    const t = now + i * 0.08
    gain.gain.setValueAtTime(0.25, t)
    gain.gain.exponentialRampToValueAtTime(0.01, t + 0.2)
    osc.connect(gain).connect(ctx.destination)
    osc.start(t)
    osc.stop(t + 0.2)
  })
}

function playGameEnd(ctx) {
  const now = ctx.currentTime
  const notes = [261.63, 329.63, 392.0, 523.25, 659.25, 783.99] // C4, E4, G4, C5, E5, G5
  notes.forEach((freq, i) => {
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.value = freq
    const t = now + i * 0.1
    const dur = i === notes.length - 1 ? 0.5 : 0.2 // sustain final note
    gain.gain.setValueAtTime(0.25, t)
    gain.gain.exponentialRampToValueAtTime(0.01, t + dur)
    osc.connect(gain).connect(ctx.destination)
    osc.start(t)
    osc.stop(t + dur)
  })
}

function playPlayerJoin(ctx) {
  const now = ctx.currentTime
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  osc.type = 'sine'
  osc.frequency.value = 880
  gain.gain.setValueAtTime(0.15, now)
  gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1)
  osc.connect(gain).connect(ctx.destination)
  osc.start(now)
  osc.stop(now + 0.1)
}

function playMatchFound(ctx) {
  // Soft two-tone ding at reduced gain
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  osc.frequency.setValueAtTime(660, ctx.currentTime)
  osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15)
  gain.gain.setValueAtTime(0.08, ctx.currentTime)
  gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3)
  osc.connect(gain).connect(ctx.destination)
  osc.start()
  osc.stop(ctx.currentTime + 0.35)
}

const SOUNDS = {
  'turn-start': playTurnStart,
  'correct-guess': playCorrectGuess,
  'tick': playTick,
  'times-up': playTimesUp,
  'round-end': playRoundEnd,
  'game-end': playGameEnd,
  'player-join': playPlayerJoin,
  'match-found': playMatchFound,
}
