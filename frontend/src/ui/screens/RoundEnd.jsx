import Scoreboard from '../components/Scoreboard.jsx'

export default function RoundEnd({ scores, onContinue }) {
  return (
    <div className="min-h-screen px-6 py-10 flex items-center">
      <div className="card p-8 w-full max-w-2xl mx-auto space-y-6">
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Round Complete</div>
          <div className="font-display text-3xl">Leaderboard</div>
        </div>
        <Scoreboard scores={scores} />
        <button className="btn-primary w-full" onClick={onContinue}>Start Next Round</button>
      </div>
    </div>
  )
}
