import Scoreboard from '../components/Scoreboard.jsx'

export default function RoundEnd({ scores, playerNames, onContinue }) {
  return (
    <div className="min-h-screen page py-10">
      <div className="page-inner grid gap-6 lg:grid-cols-[2fr_1fr] items-start">
        <div className="card p-8 space-y-6">
          <div>
            <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Round Complete</div>
            <div className="font-display text-3xl">Leaderboard</div>
          </div>
          <Scoreboard scores={scores} playerNames={playerNames} />
        </div>
        <div className="space-y-6">
          <div className="card p-6 space-y-3">
            <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Next Up</div>
            <p className="text-sm text-slate/70">The next round keeps the same join order with a fresh word list.</p>
            <div className="text-xs text-slate/60">Tip: Remind the describer to avoid the exact word.</div>
          </div>
          <button className="btn-primary w-full" onClick={onContinue}>Start Next Round</button>
        </div>
      </div>
    </div>
  )
}
