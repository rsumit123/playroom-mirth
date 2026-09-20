const TABS = [
  { value: 'all', label: 'All' },
  { value: 'quickmatch', label: 'Quick Play' },
  { value: 'friends', label: 'Friends' },
]

const GAME_ICON = { trivia: '🧠', charades: '💬', scribble: '✏️' }
const GAME_LABEL = { trivia: 'Trivia', charades: 'Charades', scribble: 'Scribble', poker: 'Poker' }

function relativeTime(iso) {
  const then = new Date(iso).getTime()
  const diff = Math.max(0, Date.now() - then)
  const s = Math.floor(diff / 1000)
  if (s < 60) return 'just now'
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  const d = Math.floor(h / 24)
  if (d < 30) return `${d}d ago`
  const mo = Math.floor(d / 30)
  if (mo < 12) return `${mo}mo ago`
  return `${Math.floor(mo / 12)}y ago`
}

// Stats are filtered by the current tab, so we want one tile per game_type
// (already filtered to the chosen origin). When tab === 'all', collapse rows
// that share a game_type so we don't show "Trivia friends" and "Trivia
// quickmatch" as two separate tiles — sum them.
function collapseByGameType(byGameType) {
  const map = new Map()
  for (const s of byGameType) {
    const cur = map.get(s.game_type)
    if (!cur) {
      map.set(s.game_type, { game_type: s.game_type, games_played: s.games_played, wins: s.wins, losses: s.losses })
    } else {
      cur.games_played += s.games_played
      cur.wins += s.wins
      cur.losses += s.losses
    }
  }
  return [...map.values()].sort((a, b) => b.games_played - a.games_played)
}

function StatsTotals({ stats }) {
  if (!stats) {
    return (
      <div className="card p-5 animate-pop">
        <div className="grid grid-cols-3 gap-4">
          {[0, 1, 2].map(i => (
            <div key={i} className="text-center">
              <div className="h-3 bg-black/5 rounded mb-2 animate-pulse" />
              <div className="h-7 bg-black/5 rounded animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    )
  }
  const winRate = stats.total_games > 0 ? Math.round((stats.total_wins / stats.total_games) * 100) : 0
  return (
    <div className="card p-5 animate-pop">
      <div className="grid grid-cols-3 gap-3 text-center">
        <div>
          <div className="text-[11px] uppercase tracking-wider text-slate/50">Games</div>
          <div className="font-display text-3xl mt-1">{stats.total_games}</div>
        </div>
        <div>
          <div className="text-[11px] uppercase tracking-wider text-slate/50">Wins</div>
          <div className="font-display text-3xl text-accent mt-1">{stats.total_wins}</div>
        </div>
        <div>
          <div className="text-[11px] uppercase tracking-wider text-slate/50">Win rate</div>
          <div className="font-display text-3xl mt-1">{winRate}%</div>
        </div>
      </div>
    </div>
  )
}

function GameTypeTiles({ stats }) {
  if (!stats || stats.by_game_type.length === 0) return null
  const tiles = collapseByGameType(stats.by_game_type)
  return (
    <div className="grid grid-cols-2 gap-3">
      {tiles.map((t) => {
        const rate = t.games_played > 0 ? Math.round((t.wins / t.games_played) * 100) : 0
        return (
          <div key={t.game_type} className="card-flat p-4 space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{GAME_ICON[t.game_type] || '🎮'}</span>
              <span className="font-semibold text-sm">{GAME_LABEL[t.game_type] || t.game_type}</span>
            </div>
            <div className="text-xs text-slate/60">{t.games_played} played</div>
            <div className="text-sm font-medium pt-1">
              <span className="text-accent">{t.wins}W</span>
              <span className="text-slate/40 mx-1">·</span>
              <span className="text-slate/70">{t.losses}L</span>
              <span className="text-xs text-slate/40 ml-1.5">({rate}%)</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function HistoryRow({ row }) {
  return (
    <div className="card-flat p-3.5 flex items-center gap-3">
      <div className="text-2xl shrink-0 w-8 text-center">{GAME_ICON[row.game_type] || '🎮'}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="font-medium text-sm">{GAME_LABEL[row.game_type] || row.game_type}</span>
          {row.origin === 'quickmatch' && (
            <span className="badge bg-accent/10 text-accent text-[10px] px-1.5 py-0.5">Quick</span>
          )}
        </div>
        <div className="text-[11px] text-slate/50 mt-0.5">
          {relativeTime(row.played_at)} · {row.player_count} player{row.player_count === 1 ? '' : 's'}
        </div>
      </div>
      <div className="text-right shrink-0">
        {row.is_winner ? (
          <div className="text-base">🏆</div>
        ) : (
          <div className="text-[10px] uppercase tracking-wider text-slate/40">Loss</div>
        )}
        <div className={`text-sm font-bold mt-0.5 ${row.is_winner ? 'text-accent' : 'text-slate/60'}`}>
          {row.score}
        </div>
      </div>
    </div>
  )
}

export default function HistoryScreen({
  tab,
  onTabChange,
  stats,
  rows,
  loading,
  loadingMore,
  hasMore,
  onLoadMore,
  onBack,
}) {
  return (
    <div className="game-shell pb-6">
      <div className="page-medium space-y-5 pt-3">
        {/* Mobile-friendly header — back chip on its own line, then title block */}
        <div className="space-y-3">
          <button className="btn-ghost-sm touch-target inline-flex items-center gap-1" onClick={onBack}>
            &larr; Back
          </button>
          <div>
            <h1 className="font-display text-2xl">Game History</h1>
            <p className="text-xs text-slate/50 mt-0.5">Your scores, wins, and matches</p>
          </div>
        </div>

        {/* Tabs first — they filter both the stats card AND the row list */}
        <div className="segmented">
          {TABS.map(t => (
            <button
              key={t.value}
              className={tab === t.value ? 'segmented-option-active' : 'segmented-option'}
              onClick={() => onTabChange(t.value)}
            >
              {t.label}
            </button>
          ))}
        </div>

        <StatsTotals stats={stats} />
        <GameTypeTiles stats={stats} />

        <div className="pt-1">
          <div className="text-xs uppercase tracking-wider text-slate/40 px-1 pb-2">Matches</div>
          {loading && rows.length === 0 ? (
            <div className="space-y-2">
              {[0, 1, 2, 3].map(i => (
                <div key={i} className="card-flat h-16 bg-black/5 animate-pulse rounded-xl" />
              ))}
            </div>
          ) : rows.length === 0 ? (
            <div className="card p-8 text-center text-slate/60 animate-pop">
              <div className="text-4xl mb-2">🎮</div>
              <p className="font-medium">No games yet in this tab.</p>
              <p className="text-xs text-slate/50 mt-1">Play a match and your results will show up here.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {rows.map(r => <HistoryRow key={r.id} row={r} />)}
              {hasMore && (
                <button
                  className="btn-ghost-sm w-full touch-target mt-1"
                  onClick={onLoadMore}
                  disabled={loadingMore}
                >
                  {loadingMore ? 'Loading...' : 'Load more'}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
