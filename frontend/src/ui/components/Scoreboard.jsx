import PlayerAvatar from './PlayerAvatar.jsx'

const RANK_STYLES = {
  0: { bg: 'bg-gold/10', border: 'border-gold/20', medal: '\u{1F947}' },
  1: { bg: 'bg-silver/10', border: 'border-silver/20', medal: '\u{1F948}' },
  2: { bg: 'bg-bronze/10', border: 'border-bronze/20', medal: '\u{1F949}' },
}

export default function Scoreboard({ scores = {}, playerNames = {}, highlight }) {
  const entries = Object.entries(scores)
    .map(([playerId, score]) => ({ playerId, score, name: playerNames[playerId] || `Player ${playerId}` }))
    .sort((a, b) => b.score - a.score)

  if (entries.length === 0) {
    return <div className="text-sm text-slate/50 text-center py-4">No scores yet</div>
  }

  return (
    <div className="space-y-2">
      {entries.map((row, idx) => {
        const rankStyle = RANK_STYLES[idx]
        const isHighlighted = String(highlight) === String(row.playerId)
        return (
          <div
            key={row.playerId}
            className={`flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all
              ${rankStyle ? `${rankStyle.bg} border ${rankStyle.border}` : 'border border-black/5'}
              ${isHighlighted ? 'ring-2 ring-accent/30 animate-pop' : ''}
            `}
          >
            <span className="text-lg w-7 text-center shrink-0">
              {rankStyle ? rankStyle.medal : `#${idx + 1}`}
            </span>
            <PlayerAvatar name={row.name} size="sm" />
            <div className="flex-1 min-w-0">
              <div className="font-medium text-sm truncate">{row.name}</div>
            </div>
            <div className="font-display text-lg font-semibold text-ink">{row.score}</div>
          </div>
        )
      })}
    </div>
  )
}
