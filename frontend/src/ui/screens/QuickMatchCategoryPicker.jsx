import { useEffect, useRef, useState } from 'react'
import TriviaCategorySelector, { CATEGORIES } from '../components/TriviaCategorySelector.jsx'

const RANDOM_VALUE = 'surprise'

// Roulette tuning: total ~2400ms, starting fast and decelerating to a clear "rest"
// before the search starts. The intervals grow geometrically so each step feels
// slower than the last — like a slot machine winding down.
const ROULETTE_INTERVALS_MS = [
  60, 60, 70, 80, 90, 100, 115, 130, 150, 175, 200, 230, 270, 320, 380, 460,
]

function pickRandomCategory() {
  return CATEGORIES[Math.floor(Math.random() * CATEGORIES.length)].value
}

export default function QuickMatchCategoryPicker({ onStart, onBack }) {
  const [selected, setSelected] = useState(RANDOM_VALUE)
  const [pending, setPending] = useState(false)
  const [rolling, setRolling] = useState(false)
  // Which category tile is currently highlighted in the roulette animation.
  const [rollCursor, setRollCursor] = useState(null)
  // The final landed category (locked in before we call onStart).
  const [rollResult, setRollResult] = useState(null)
  const timersRef = useRef([])

  // Tidy any in-flight roulette timers on unmount.
  useEffect(() => () => {
    for (const id of timersRef.current) clearTimeout(id)
    timersRef.current = []
  }, [])

  function startRoulette() {
    const finalChoice = pickRandomCategory()
    const finalIdx = CATEGORIES.findIndex(c => c.value === finalChoice)
    setRolling(true)
    setRollResult(null)

    // Walk through tiles, decelerating. The last hop lands exactly on finalIdx.
    let elapsed = 0
    const totalSteps = ROULETTE_INTERVALS_MS.length
    // Pre-compute the cursor index at each step so the final step lands on finalChoice.
    const startCursor = (finalIdx - (totalSteps - 1) + CATEGORIES.length * 10) % CATEGORIES.length
    for (let step = 0; step < totalSteps; step++) {
      elapsed += ROULETTE_INTERVALS_MS[step]
      const cursorIdx = (startCursor + step) % CATEGORIES.length
      const id = setTimeout(() => setRollCursor(cursorIdx), elapsed)
      timersRef.current.push(id)
    }
    // After the last hop, lock in result + give a brief "rest" pause before starting search.
    const restPauseMs = 700
    const settleId = setTimeout(() => {
      setRollResult(finalChoice)
    }, elapsed)
    timersRef.current.push(settleId)
    const goId = setTimeout(() => onStart(finalChoice), elapsed + restPauseMs)
    timersRef.current.push(goId)
  }

  function handleStart() {
    if (pending) return
    setPending(true)
    if (selected === RANDOM_VALUE) {
      startRoulette()
    } else {
      onStart(selected)
    }
  }

  // While rolling, force the selector to highlight the cursor (and the final
  // landed category once we've settled).
  const visualHighlight = rolling
    ? (rollResult ?? (rollCursor != null ? CATEGORIES[rollCursor].value : null))
    : (selected === RANDOM_VALUE ? null : selected)

  return (
    <div className="min-h-screen flex flex-col bg-bg">
      <div className="px-4 py-3 flex items-center gap-2 safe-area-top border-b border-black/5">
        <button className="touch-target text-slate/60" onClick={onBack} disabled={rolling}>←</button>
        <h1 className="font-display text-lg">
          {rolling ? (rollResult ? 'Locked in!' : 'Picking a topic...') : 'Pick a topic'}
        </h1>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 pb-32">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-2">
          <button
            data-category={RANDOM_VALUE}
            disabled={rolling}
            className={`rounded-xl border-2 px-3 py-3 text-center transition-all ${
              !rolling && selected === RANDOM_VALUE
                ? 'border-accent bg-accent/10 ring-1 ring-accent shadow-sm'
                : 'border-black/5 bg-white/60 hover:border-accent/30'
            } ${rolling ? 'opacity-50' : ''}`}
            onClick={() => setSelected(RANDOM_VALUE)}
          >
            <div className={`text-2xl mb-1 ${rolling && !rollResult ? 'animate-bounce' : ''}`}>🎲</div>
            <div className={`text-xs font-semibold ${!rolling && selected === RANDOM_VALUE ? 'text-accent' : 'text-ink'}`}>Random</div>
          </button>
        </div>
        <TriviaCategorySelector
          value={visualHighlight}
          onChange={(v) => { if (!rolling) setSelected(v) }}
          readOnly={rolling}
        />
        {rolling && rollResult && (
          <div className="mt-4 text-center text-sm text-accent font-semibold animate-pop">
            {CATEGORIES.find(c => c.value === rollResult)?.label} — starting...
          </div>
        )}
      </div>

      <div className="fixed bottom-0 left-0 right-0 px-4 py-3 safe-area-bottom bg-bg/95 backdrop-blur border-t border-black/5">
        <button
          className="btn-primary w-full touch-target"
          onClick={handleStart}
          disabled={pending}
        >
          {rolling ? (rollResult ? 'Starting...' : 'Picking...') : 'Start Searching →'}
        </button>
      </div>
    </div>
  )
}
