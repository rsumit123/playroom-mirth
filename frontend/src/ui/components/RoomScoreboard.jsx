import { useState } from 'react'

export default function RoomScoreboard({ scoreboard, selfName }) {
  const [expanded, setExpanded] = useState(false)
  const [tab, setTab] = useState('totals') // 'totals' | 'games'

  if (!scoreboard || !scoreboard.games?.length) return null

  const { games, totals } = scoreboard

  return (
    <div className="card overflow-hidden">
      {/* Header — always visible, acts as toggle */}
      <button
        className="w-full flex items-center justify-between p-4 text-left"
        onClick={() => setExpanded((e) => !e)}
      >
        <div className="flex items-center gap-2">
          <h2 className="font-semibold">Scoreboard</h2>
          <span className="badge bg-accent/10 text-accent text-[10px]">
            {games.length} {games.length === 1 ? 'game' : 'games'}
          </span>
        </div>
        <svg
          className={`w-4 h-4 text-slate/40 transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Collapsed summary — show leader */}
      {!expanded && totals.length > 0 && (
        <div className="px-4 pb-3 -mt-1">
          <span className="text-xs text-slate/50">
            Leader: <span className="text-accent font-medium">{totals[0].display_name}</span>
            {' '}&middot; {totals[0].total_score} pts &middot; {totals[0].wins}W
          </span>
        </div>
      )}

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-black/5">
          {/* Tab switcher */}
          <div className="flex border-b border-black/5">
            <button
              className={`flex-1 py-2 text-xs font-medium transition ${tab === 'totals' ? 'text-accent border-b-2 border-accent' : 'text-slate/50'}`}
              onClick={() => setTab('totals')}
            >
              Overall
            </button>
            <button
              className={`flex-1 py-2 text-xs font-medium transition ${tab === 'games' ? 'text-accent border-b-2 border-accent' : 'text-slate/50'}`}
              onClick={() => setTab('games')}
            >
              Game History
            </button>
          </div>

          <div className="p-4 max-h-64 overflow-y-auto">
            {tab === 'totals' ? (
              <TotalsView totals={totals} selfName={selfName} />
            ) : (
              <GamesView games={games} selfName={selfName} />
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function TotalsView({ totals, selfName }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-[10px] uppercase tracking-wider text-slate/40">
          <th className="text-left pb-2 font-medium">#</th>
          <th className="text-left pb-2 font-medium">Player</th>
          <th className="text-right pb-2 font-medium">Score</th>
          <th className="text-right pb-2 font-medium">W</th>
          <th className="text-right pb-2 font-medium">GP</th>
        </tr>
      </thead>
      <tbody>
        {totals.map((t, i) => {
          const isSelf = selfName && t.display_name === selfName
          return (
            <tr key={t.display_name} className={isSelf ? 'text-accent font-medium' : ''}>
              <td className="py-1.5 pr-2">
                {i === 0 ? <span title="Leader">&#127942;</span> : i + 1}
              </td>
              <td className="py-1.5 truncate max-w-[120px]">
                {t.display_name}
                {isSelf && <span className="text-[10px] ml-1 opacity-60">(You)</span>}
              </td>
              <td className="py-1.5 text-right tabular-nums">{t.total_score}</td>
              <td className="py-1.5 text-right tabular-nums">{t.wins}</td>
              <td className="py-1.5 text-right tabular-nums text-slate/50">{t.games_played}</td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}

function GamesView({ games, selfName }) {
  return (
    <div className="space-y-3">
      {games.map((g) => (
        <div key={g.game_number} className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate/60">Game {g.game_number}</span>
            <span className="text-[10px] text-slate/30 capitalize">{g.game_type}</span>
          </div>
          {g.players.map((p, i) => {
            const isSelf = selfName && p.display_name === selfName
            return (
              <div
                key={i}
                className={`flex items-center justify-between rounded-lg px-2.5 py-1.5 text-sm ${
                  p.is_winner ? 'bg-accent/8' : ''
                } ${isSelf ? 'font-medium' : ''}`}
              >
                <span className="truncate max-w-[140px]">
                  {p.is_winner && <span className="mr-1">&#127942;</span>}
                  {p.display_name}
                  {isSelf && <span className="text-[10px] text-accent ml-1">(You)</span>}
                </span>
                <span className="tabular-nums text-slate/70">{p.score}</span>
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}
/* scoreboard */
