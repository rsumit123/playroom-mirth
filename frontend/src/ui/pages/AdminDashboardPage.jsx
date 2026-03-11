import { useEffect, useState, useRef } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import * as api from '../../lib/api.js'

const GAME_LABELS = { charades: 'Charades', scribble: 'Scribble', trivia: 'Trivia' }
const CAT_ICONS = { science: '🔬', history: '📜', geography: '🌍', sports: '⚽', entertainment: '🎬', general: '💡' }

export default function AdminDashboardPage() {
  const { auth } = useApp()
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [lastRefresh, setLastRefresh] = useState(null)
  const intervalRef = useRef(null)

  async function loadStats() {
    if (!auth?.token) { setError('Sign in required'); return }
    setLoading(true)
    try {
      const res = await api.fetchAdminStats(auth.token)
      setStats(res)
      setError(null)
      setLastRefresh(new Date())
    } catch (e) {
      setError(e.message || 'Failed to load stats')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (auth?.token) loadStats()
    intervalRef.current = setInterval(() => {
      if (auth?.token) loadStats()
    }, 30000)
    return () => clearInterval(intervalRef.current)
  }, [auth?.token])

  const t = stats?.totals || {}
  const pool = stats?.question_pool || {}

  return (
    <div className="min-h-screen px-4 sm:px-6 py-8 space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl">Admin Dashboard</h1>
          <p className="text-xs text-slate/50">
            {lastRefresh ? `Last updated: ${lastRefresh.toLocaleTimeString()}` : 'Loading...'}
            {' · Auto-refreshes every 30s'}
          </p>
        </div>
        <button
          className="btn-ghost-sm touch-target flex items-center gap-1.5"
          onClick={loadStats}
          disabled={loading}
        >
          {loading ? '...' : 'Refresh'}
        </button>
      </div>

      {error && <div className="card px-4 py-3 text-sm text-danger bg-danger/5 border-danger/20">{error}</div>}

      {!auth?.token && (
        <div className="card p-8 text-center text-slate/50">Sign in with Google to access admin stats.</div>
      )}

      {stats && (
        <>
          {/* Stat cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <StatCard label="Active Rooms" value={t.active_room_count || 0} color="accent" />
            <StatCard label="Connected Players" value={t.connected_players || 0} color="correct" />
            <StatCard label="Live Games" value={t.in_memory_games || 0} color="gold" />
            <StatCard label="Total Questions" value={t.total_questions || 0} color="accent" />
          </div>

          {/* Active Rooms */}
          <div className="card p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">Active Rooms</h2>
              <span className="badge bg-accent/10 text-accent text-xs">{stats.active_rooms?.length || 0}</span>
            </div>
            {stats.active_rooms?.length === 0 && (
              <div className="text-sm text-slate/40 py-2">No active rooms right now.</div>
            )}
            {stats.active_rooms?.map((room) => (
              <div key={room.code} className="flex items-center justify-between rounded-xl border border-black/5 px-4 py-3">
                <div className="flex items-center gap-3 min-w-0">
                  <span className="font-display text-lg tracking-wider">{room.code}</span>
                  <span className="badge bg-accent/10 text-accent text-[10px]">
                    {GAME_LABELS[room.game_type] || room.game_type}
                  </span>
                  {room.game_type === 'trivia' && room.trivia_category && (
                    <span className="text-[10px] text-slate/40">{room.trivia_category}</span>
                  )}
                </div>
                <div className="flex items-center gap-4 text-xs text-slate/50 shrink-0">
                  <span className={room.status === 'active' ? 'text-correct font-medium' : 'text-accent'}>
                    {room.status === 'active' ? 'In Game' : 'Lobby'}
                  </span>
                  <span>{room.connected_players}/{room.max_players} players</span>
                  {room.created_at && (
                    <span>{new Date(room.created_at).toLocaleTimeString()}</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Question Pool */}
          <div className="card p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">Question Pool</h2>
              <span className="badge bg-accent/10 text-accent text-xs">{t.total_questions || 0} total</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {Object.entries(pool)
                .sort(([, a], [, b]) => b - a)
                .map(([cat, count]) => (
                  <div key={cat} className="rounded-xl border border-black/5 px-4 py-3 flex items-center gap-3">
                    <span className="text-xl">{CAT_ICONS[cat] || '📝'}</span>
                    <div>
                      <div className="text-sm font-medium capitalize">{cat}</div>
                      <div className="text-xs text-slate/50">{count} questions</div>
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Recent Games */}
          <div className="card p-5 space-y-3">
            <h2 className="font-semibold">Recent Games</h2>
            {stats.recent_games?.length === 0 && (
              <div className="text-sm text-slate/40 py-2">No games played yet.</div>
            )}
            {stats.recent_games?.map((g, i) => (
              <div key={i} className="flex items-center justify-between rounded-xl border border-black/5 px-4 py-2.5">
                <div className="flex items-center gap-3 min-w-0">
                  <span className="font-display text-sm tracking-wider">{g.room_code}</span>
                  <span className="badge bg-accent/10 text-accent text-[10px]">
                    {GAME_LABELS[g.game_type] || g.game_type}
                  </span>
                  {g.is_winner && <span title="Winner">🏆</span>}
                </div>
                <div className="flex items-center gap-4 text-xs text-slate/50 shrink-0">
                  <span>{g.player_count} players</span>
                  <span>{g.score} pts</span>
                  {g.played_at && <span>{new Date(g.played_at).toLocaleDateString()}</span>}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function StatCard({ label, value, color = 'accent' }) {
  return (
    <div className="card p-4 text-center">
      <div className={`font-display text-3xl text-${color}`}>{value}</div>
      <div className="text-xs text-slate/50 mt-1">{label}</div>
    </div>
  )
}
