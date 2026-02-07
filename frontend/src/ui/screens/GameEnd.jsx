import Scoreboard from '../components/Scoreboard.jsx'

export default function GameEnd({ scores, onHome }) {
  return (
    <div className="min-h-screen px-6 py-10 flex items-center">
      <div className="card p-8 w-full max-w-2xl mx-auto space-y-6">
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Game Complete</div>
          <div className="font-display text-3xl">Final Leaderboard</div>
        </div>
        <Scoreboard scores={scores} />
        <div className="grid gap-3 sm:grid-cols-2">
          <button className="btn-primary" onClick={onHome}>Back to Home</button>
          <button className="btn-ghost">Play Again</button>
        </div>
      </div>
    </div>
  )
}
