import { useEffect, useState } from 'react'
import TriviaCategorySelector, { CATEGORIES } from '../components/TriviaCategorySelector.jsx'

const RANDOM_VALUE = 'surprise'

function categoryLabel(value) {
  if (!value || value === RANDOM_VALUE) return 'Random'
  return CATEGORIES.find(c => c.value === value)?.label || value
}

function categoryEmoji(value) {
  if (!value || value === RANDOM_VALUE) return '🎲'
  return CATEGORIES.find(c => c.value === value)?.icon || '🎯'
}

export default function QuickMatchSearch({ waitSeconds = 15, category, onCancel, onChangeCategory }) {
  const [remaining, setRemaining] = useState(waitSeconds)
  const [sheetOpen, setSheetOpen] = useState(false)

  useEffect(() => {
    setRemaining(waitSeconds)
  }, [waitSeconds, category])

  // Decrement once per second, clamping at 0 and self-stopping. The old version
  // used a stale-closure `if (remaining <= 0) return` outside the interval, so
  // the callback decremented forever and the user saw a negative number when
  // the server's bot fallback didn't arrive in time.
  useEffect(() => {
    const id = setInterval(() => {
      setRemaining(r => {
        if (r <= 0) {
          clearInterval(id)
          return 0
        }
        return r - 1
      })
    }, 1000)
    return () => clearInterval(id)
  }, [category])

  function pickCategory(value) {
    setSheetOpen(false)
    if (value === category) return
    onChangeCategory?.(value)
  }

  return (
    <div className="min-h-[100dvh] flex flex-col bg-bg safe-area-top safe-area-bottom">
      <div className="flex justify-end px-4 py-3">
        <button className="touch-target text-slate/60" onClick={onCancel} aria-label="Cancel">✕</button>
      </div>
      <div className="flex-1 flex flex-col items-center justify-center text-center px-6">
        <div className="relative w-48 h-48 flex items-center justify-center mb-6">
          <div className="absolute inset-0 rounded-full bg-accent/10 animate-ping" />
          <div className="absolute inset-4 rounded-full bg-accent/15" />
          <span className="relative z-10 text-5xl font-display text-accent">{remaining}</span>
        </div>
        <p className="text-xl font-display text-ink">Finding a player...</p>

        {/* Topic chip — tap to change. Lives on the search screen so the picker
            screen is no longer in the critical path. */}
        <button
          type="button"
          className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-black/10 bg-white/70 hover:bg-white text-sm text-slate/70 touch-target"
          onClick={() => setSheetOpen(true)}
          aria-label="Change topic"
        >
          <span className="text-base">{categoryEmoji(category)}</span>
          <span className="font-medium">{categoryLabel(category)}</span>
          <span className="text-base opacity-70" aria-hidden="true">⚙️</span>
        </button>
      </div>

      {sheetOpen && (
        <div className="fixed inset-0 z-40 flex items-end sm:items-center justify-center bg-black/40 animate-pop"
             onClick={() => setSheetOpen(false)}>
          <div
            className="w-full sm:max-w-md bg-white rounded-t-2xl sm:rounded-2xl p-4 safe-area-bottom max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-label="Choose topic"
          >
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-display text-lg">Choose topic</h2>
              <button className="touch-target text-slate/60" onClick={() => setSheetOpen(false)} aria-label="Close">✕</button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-2">
              <button
                type="button"
                className={`rounded-xl border-2 px-3 py-3 text-center transition-all ${
                  category === RANDOM_VALUE
                    ? 'border-accent bg-accent/10 ring-1 ring-accent shadow-sm'
                    : 'border-black/5 bg-white/60 hover:border-accent/30'
                }`}
                onClick={() => pickCategory(RANDOM_VALUE)}
              >
                <div className="text-2xl mb-1">🎲</div>
                <div className={`text-xs font-semibold ${category === RANDOM_VALUE ? 'text-accent' : 'text-ink'}`}>Random</div>
              </button>
            </div>
            <TriviaCategorySelector
              value={category === RANDOM_VALUE ? null : category}
              onChange={pickCategory}
            />
          </div>
        </div>
      )}
    </div>
  )
}
