import { useState } from 'react'
import TriviaCategorySelector from '../components/TriviaCategorySelector.jsx'

export default function QuickMatchCategoryPicker({ onStart, onBack }) {
  const [selected, setSelected] = useState('surprise')
  const [pending, setPending] = useState(false)

  function handleStart() {
    if (pending) return
    setPending(true)
    onStart(selected)
  }

  return (
    <div className="min-h-screen flex flex-col bg-bg">
      <div className="px-4 py-3 flex items-center gap-2 safe-area-top border-b border-black/5">
        <button className="touch-target text-slate/60" onClick={onBack}>←</button>
        <h1 className="font-display text-lg">Pick a topic</h1>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 pb-32">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-2">
          <button
            data-category="surprise"
            className={`rounded-xl border-2 px-3 py-3 text-center transition-all ${
              selected === 'surprise'
                ? 'border-accent bg-accent/10 ring-1 ring-accent shadow-sm'
                : 'border-black/5 bg-white/60 hover:border-accent/30'
            }`}
            onClick={() => setSelected('surprise')}
          >
            <div className="text-2xl mb-1">🎲</div>
            <div className={`text-xs font-semibold ${selected === 'surprise' ? 'text-accent' : 'text-ink'}`}>Surprise me</div>
          </button>
        </div>
        <TriviaCategorySelector value={selected === 'surprise' ? null : selected} onChange={setSelected} />
      </div>

      <div className="fixed bottom-0 left-0 right-0 px-4 py-3 safe-area-bottom bg-bg/95 backdrop-blur border-t border-black/5">
        <button
          className="btn-primary w-full touch-target"
          onClick={handleStart}
          disabled={pending}
        >
          Start Searching →
        </button>
      </div>
    </div>
  )
}
