import Scoreboard from '../components/Scoreboard.jsx'

export default function GameEnd({ scores, playerNames, onHome }) {
  return (
    <div className="min-h-screen page py-10">
      <div className="page-inner grid gap-6 lg:grid-cols-[2fr_1fr] items-start">
        <div className="card p-8 space-y-6">
          <div>
            <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Game Complete</div>
            <div className="font-display text-3xl">Final Leaderboard</div>
          </div>
          <Scoreboard scores={scores} playerNames={playerNames} />
        </div>
        <div className="space-y-6">
          <div className="card p-6 space-y-3">
            <div className="text-xs uppercase tracking-[0.3em] text-slate/60">What’s Next</div>
            <p className="text-sm text-slate/70">Start a new room or replay with a different difficulty to keep it fresh.</p>
            <div className="text-xs text-slate/60">Guests can play one full match before signing in.</div>
          </div>
          <div className="grid gap-3">
            <button className="btn-primary" onClick={onHome}>Back to Home</button>
            <button className="btn-ghost">Play Again</button>
          </div>
        </div>
      </div>
    </div>
  )
}
