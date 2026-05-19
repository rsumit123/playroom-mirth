/**
 * All-time Quick Play leaderboard.
 *
 * Mobile UX:
 * - One row per player, 56px tall, big rank chip on the left.
 * - Top 3 get gold/silver/bronze rank pills. Rank 4+ stays neutral.
 * - The caller's own row (if in top) is highlighted with the accent ring.
 * - If the caller is outside the top, a sticky "you" pin sits at the bottom
 *   so they always know where they stand.
 * - Avatar is the Google profile pic when available, else a colored initial
 *   bubble. Falls back gracefully on referrer-policy-blocked image loads.
 */

const RANK_TIER = {
  1: { bg: 'bg-gradient-to-br from-yellow-300 to-yellow-500', text: 'text-white' },
  2: { bg: 'bg-gradient-to-br from-slate/30 to-slate/40', text: 'text-white' },
  3: { bg: 'bg-gradient-to-br from-amber-400 to-amber-600', text: 'text-white' },
}

function Avatar({ name, avatarUrl, size = 'md' }) {
  const dim = size === 'sm' ? 'h-8 w-8 text-xs' : 'h-10 w-10 text-sm'
  if (avatarUrl) {
    return <img src={avatarUrl} alt="" className={`${dim} rounded-full object-cover`} referrerPolicy="no-referrer" />
  }
  const letter = (name || '?').trim().slice(0, 1).toUpperCase() || '?'
  return <div className={`${dim} rounded-full bg-accent/15 flex items-center justify-center font-bold text-accent`}>{letter}</div>
}

function RankPill({ rank }) {
  const tier = RANK_TIER[rank]
  if (tier) {
    return (
      <div className={`h-9 w-9 rounded-xl ${tier.bg} ${tier.text} flex items-center justify-center font-display text-base shadow-sm shrink-0`}>
        {rank}
      </div>
    )
  }
  return (
    <div className="h-9 w-9 rounded-xl bg-black/5 text-slate/60 flex items-center justify-center font-display text-base shrink-0">
      {rank}
    </div>
  )
}

function Row({ entry, isYou }) {
  const winRate = entry.games_played > 0 ? Math.round((entry.wins / entry.games_played) * 100) : 0
  return (
    <div className={`flex items-center gap-3 p-3 rounded-xl border ${
      isYou ? 'border-accent/40 bg-accent/5 ring-1 ring-accent/20' : 'border-black/5 bg-white'
    }`}>
      <RankPill rank={entry.rank} />
      <Avatar name={entry.display_name} avatarUrl={entry.avatar_url} />
      <div className="flex-1 min-w-0">
        <div className="font-medium text-sm truncate">
          {entry.display_name}
          {isYou && <span className="ml-1.5 text-[10px] uppercase tracking-wider text-accent">You</span>}
        </div>
        <div className="text-[11px] text-slate/50">
          {entry.games_played} game{entry.games_played === 1 ? '' : 's'} · {winRate}% win rate
        </div>
      </div>
      <div className="text-right shrink-0">
        <div className="font-display text-lg text-accent">{entry.wins}</div>
        <div className="text-[10px] uppercase tracking-wider text-slate/40">wins</div>
      </div>
    </div>
  )
}

export default function LeaderboardScreen({ data, loading, onBack, currentUserId }) {
  return (
    <div className="game-shell pb-6 safe-area-top">
      <div className="page-medium space-y-5 pt-3">
        <div className="space-y-3">
          <button className="btn-ghost-sm touch-target inline-flex items-center gap-1" onClick={onBack}>
            &larr; Back
          </button>
          <div>
            <h1 className="font-display text-2xl">Leaderboard</h1>
            <p className="text-xs text-slate/50 mt-0.5">All-time Quick Play winners</p>
          </div>
        </div>

        {/* Streak pill — only if it makes sense to flex */}
        {data?.current_streak >= 2 && (
          <div className="card-flat p-3 flex items-center gap-3 animate-pop">
            <div className="text-2xl">🔥</div>
            <div className="flex-1">
              <div className="font-medium text-sm">{data.current_streak}-win streak</div>
              <div className="text-[11px] text-slate/50">Keep it going!</div>
            </div>
          </div>
        )}

        {loading ? (
          <div className="space-y-2">
            {[0, 1, 2, 3, 4].map(i => (
              <div key={i} className="h-16 rounded-xl bg-black/5 animate-pulse" />
            ))}
          </div>
        ) : !data || data.top.length === 0 ? (
          <div className="card p-8 text-center text-slate/60 animate-pop">
            <div className="text-4xl mb-2">🏆</div>
            <p className="font-medium">No one has played yet.</p>
            <p className="text-xs text-slate/50 mt-1">Be the first to land on the leaderboard.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {data.top.map(entry => (
              <Row key={entry.user_id} entry={entry} isYou={entry.user_id === currentUserId} />
            ))}
          </div>
        )}

        {/* Sticky "you" pin — only when the caller is outside the top slice */}
        {data?.you && (
          <div className="pt-2">
            <div className="text-[10px] uppercase tracking-wider text-slate/40 px-1 pb-2">Your rank</div>
            <Row entry={data.you} isYou />
          </div>
        )}
      </div>
    </div>
  )
}
