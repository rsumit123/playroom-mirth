import { useEffect, useState } from 'react'

export default function QuickMatchSearch({ waitSeconds = 15, category, onCancel }) {
  const [remaining, setRemaining] = useState(waitSeconds)

  useEffect(() => {
    if (remaining <= 0) return
    const id = setInterval(() => setRemaining(r => r - 1), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="min-h-screen flex flex-col bg-bg safe-area-top">
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
        <p className="text-sm text-slate/60 mt-1 capitalize">{category} category</p>
      </div>
    </div>
  )
}
