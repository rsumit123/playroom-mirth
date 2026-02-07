import { useState } from 'react'
import Logo from '../components/Logo.jsx'
import Spinner from '../components/Spinner.jsx'

export default function Welcome({ onGuest, onSignIn, onHowTo, loadingGuest }) {
  const [name, setName] = useState('')

  return (
    <div className="game-shell">
      <div className="flex-1 flex flex-col items-center justify-center page-narrow py-8 text-center">
        <div className="mb-8">
          <Logo />
        </div>

        <h1 className="font-display text-4xl sm:text-5xl mb-3">
          Describe. Guess. <span className="text-accent">Win.</span>
        </h1>
        <p className="text-slate/60 text-base mb-8 max-w-sm">
          The multiplayer word game where every hint counts. Play with friends in seconds.
        </p>

        <div className="flex items-center gap-3 mb-10 text-sm flex-wrap justify-center">
          <span className="badge bg-accent/10 text-accent">1. Describe</span>
          <span className="text-slate/30">&rarr;</span>
          <span className="badge bg-accent/10 text-accent">2. Guess</span>
          <span className="text-slate/30">&rarr;</span>
          <span className="badge bg-accent/10 text-accent">3. Score</span>
        </div>

        <div className="w-full space-y-3 max-w-xs">
          <input
            className="w-full rounded-xl border border-black/10 px-4 py-3 text-sm text-center touch-target outline-none focus:border-accent transition"
            placeholder="Enter your name"
            maxLength={30}
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && name.trim()) onGuest(name.trim())
            }}
          />
          <button
            className="btn-primary w-full text-lg py-4 touch-target flex items-center justify-center gap-2"
            onClick={() => onGuest(name.trim() || undefined)}
            disabled={loadingGuest}
          >
            {loadingGuest ? <Spinner size={18} /> : null}
            Play Now
          </button>
          <button className="btn-ghost w-full touch-target" onClick={onSignIn}>
            Sign In
          </button>
        </div>
      </div>

      <div className="page-narrow pb-6 text-center">
        <button className="text-sm text-accent font-medium underline underline-offset-4" onClick={onHowTo}>
          How to Play
        </button>
      </div>
    </div>
  )
}
