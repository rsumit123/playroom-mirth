export default function Scoreboard({ scores = {} }) {
  const entries = Object.entries(scores)
    .map(([playerId, score]) => ({ playerId, score }))
    .sort((a, b) => b.score - a.score)

  if (entries.length === 0) {
    return <div className="text-sm text-slate/60">No scores yet.</div>
  }

  return (
    <div className="space-y-2">
      {entries.map((row, idx) => (
        <div key={row.playerId} className="flex items-center justify-between rounded-xl border border-black/5 px-3 py-2">
          <div className="text-sm font-semibold">#{idx + 1} Player {row.playerId}</div>
          <div className="text-sm text-slate/70">{row.score} pts</div>
        </div>
      ))}
    </div>
  )
}
