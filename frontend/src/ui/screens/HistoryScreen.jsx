const TABS = [
  { value: 'all', label: 'All' },
  { value: 'quickmatch', label: 'Quick Play' },
  { value: 'friends', label: 'Friends' },
]

const GAME_ICON = { trivia: '🧠', charades: '💬', scribble: '✏️' }
const GAME_LABEL = { trivia: 'Trivia', charades: 'Charades', scribble: 'Scribble' }

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

function StatsCard({ stats }) {
  if (!stats) {
    return <div className="card p-4 animate-pop"><div className="h-12 bg-black/5 rounded animate-pulse" /></div>
  }
  const winRate = stats.total_games > 0 ? Math.round((stats.total_wins / stats.total_games) * 100) : 0
  return (
    <div className="card p-4 space-y-3 animate-pop">
      <div className="grid grid-cols-3 gap-3 text-center">
        <div>
          <div className="text-xs text-slate/60">Games</div>
          <div className="font-display text-2xl">{stats.total_games}</div>
        </div>
        <div>
          <div className="text-xs text-slate/60">Wins</div>
          <div className="font-display text-2xl text-accent">{stats.total_wins}</div>
        </div>
        <div>
          <div className="text-xs text-slate/60">Win rate</div>
          <div className="font-display text-2xl">{winRate}%</div>
        </div>
      </div>
      {stats.by_game_type.length > 0 && (
        <div className="space-y-1.5 pt-1 border-t border-black/5">
          {stats.by_game_type.slice(0, 4).map((s, i) => (
            <div key={i} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <span className="text-base">{GAME_ICON[s.game_type] || '🎮'}</span>
                <span className="text-slate/80">{GAME_LABEL[s.game_type] || s.game_type}</span>
                <span className="text-xs text-slate/40 capitalize">· {s.origin}</span>
              </div>
              <div className="text-xs text-slate/60">
                <span className="text-accent font-semibold">{s.wins}W</span>
                <span> / </span>
                <span>{s.losses}L</span>
                <span className="ml-2 text-slate/40">({s.games_played})</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function HistoryRow({ row }) {
  return (
    <div className="card-flat p-3 flex items-center gap-3">
      <div className="text-2xl shrink-0">{GAME_ICON[row.game_type] || '🎮'}</div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm truncate">{GAME_LABEL[row.game_type] || row.game_type}</span>
          {row.origin === 'quickmatch' && (
            <span className="badge bg-accent/10 text-accent text-[10px]">Quick</span>
          )}
        </div>
        <div className="text-xs text-slate/50 flex items-center gap-2 mt-0.5">
          <span>{relativeTime(row.played_at)}</span>
          <span>·</span>
          <span>{row.player_count} player{row.player_count === 1 ? '' : 's'}</span>
        </div>
      </div>
      <div className="text-right shrink-0">
        <div className={`text-sm font-bold ${row.is_winner ? 'text-accent' : 'text-slate/50'}`}>
          {row.is_winner ? '🏆' : ''} {row.score}
        </div>
        <div className="text-[10px] text-slate/40 uppercase tracking-wider">
          {row.is_winner ? 'Win' : 'Loss'}
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
    <div className="game-shell py-6">
      <div className="page-medium space-y-5">
        <div className="relative text-center py-1">
          <button className="btn-ghost-sm touch-target absolute left-0 top-1/2 -translate-y-1/2" onClick={onBack}>&larr; Back</button>
          <h2 className="font-display text-2xl">Game History</h2>
          <p className="text-xs text-slate/50">Your scores, wins, and recent matches</p>
        </div>

        <StatsCard stats={stats} />

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

        {loading && rows.length === 0 ? (
          <div className="space-y-2">
            {[0, 1, 2].map(i => (
              <div key={i} className="card-flat p-3 h-14 bg-black/5 animate-pulse rounded-xl" />
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
                className="btn-ghost-sm w-full touch-target"
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
  )
}
