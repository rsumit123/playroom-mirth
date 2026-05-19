/**
 * Live "you vs opponent" chip shown above the trivia card in 1v1 quickmatch
 * games. Designed to be flat + compact: ~44px tall on mobile, doesn't compete
 * with the question card for attention. Score on each side updates live from
 * scores prop; the player currently in the lead gets the accent treatment.
 */

function Initial({ name, isYou }) {
  const letter = (name || '?').trim().slice(0, 1).toUpperCase() || '?'
  return (
    <div className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
      isYou ? 'bg-accent text-white' : 'bg-slate/15 text-slate/70'
    }`}>
      {letter}
    </div>
  )
}

export default function VsOpponentChip({ scores, playerNames, selfPlayerId, playerOrder }) {
  // Build the two-player breakdown. We only render for exactly 2 players —
  // for friend games with 3+, scoreboard takes over.
  const ids = (playerOrder && playerOrder.length === 2) ? playerOrder : Object.keys(scores || {})
  if (!ids || ids.length !== 2) return null

  const youId = String(selfPlayerId)
  const meId = ids.find(id => String(id) === youId) ?? ids[0]
  const oppId = ids.find(id => String(id) !== String(meId)) ?? ids[1]
  const meScore = scores?.[meId] ?? 0
  const oppScore = scores?.[oppId] ?? 0
  const oppName = playerNames?.[oppId] || 'Opponent'

  const meLeads = meScore > oppScore
  const oppLeads = oppScore > meScore

  return (
    <div className="bg-white/70 backdrop-blur border-b border-black/5 px-4 py-2 shrink-0">
      <div className="max-w-lg mx-auto flex items-center justify-between gap-3">
        {/* You — left */}
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <Initial name="You" isYou />
          <div className="min-w-0">
            <div className="text-[10px] uppercase tracking-wider text-slate/40 leading-none">You</div>
            <div className={`font-display text-base leading-tight ${meLeads ? 'text-accent' : 'text-ink'}`}>
              {meScore}
            </div>
          </div>
        </div>

        {/* vs separator */}
        <div className="text-[10px] uppercase tracking-widest text-slate/40 shrink-0">vs</div>

        {/* Opponent — right (mirrored layout so scores meet in the middle) */}
        <div className="flex items-center gap-2 min-w-0 flex-1 justify-end">
          <div className="min-w-0 text-right">
            <div className="text-[10px] uppercase tracking-wider text-slate/40 leading-none truncate">{oppName}</div>
            <div className={`font-display text-base leading-tight ${oppLeads ? 'text-accent' : 'text-ink'}`}>
              {oppScore}
            </div>
          </div>
          <Initial name={oppName} isYou={false} />
        </div>
      </div>
    </div>
  )
}
