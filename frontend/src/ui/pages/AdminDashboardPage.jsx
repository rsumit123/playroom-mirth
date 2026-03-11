import { useEffect, useState, useRef } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import * as api from '../../lib/api.js'

const GAME_LABELS = { charades: 'Charades', scribble: 'Scribble', trivia: 'Trivia' }
const CAT_ICONS = { science: '🔬', history: '📜', geography: '🌍', sports: '⚽', entertainment: '🎬', general: '💡' }
const CATEGORIES = ['science', 'history', 'geography', 'sports', 'entertainment', 'general']
const DIFFICULTIES = [{ value: 1, label: 'Easy' }, { value: 2, label: 'Medium' }, { value: 3, label: 'Hard' }]

export default function AdminDashboardPage() {
  const { auth } = useApp()
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [lastRefresh, setLastRefresh] = useState(null)
  const [expandedRoom, setExpandedRoom] = useState(null)
  const [actionLoading, setActionLoading] = useState(null)
  const intervalRef = useRef(null)

  // Question management state
  const [questions, setQuestions] = useState(null)
  const [qTotal, setQTotal] = useState(0)
  const [qSearch, setQSearch] = useState('')
  const [qCategory, setQCategory] = useState('')
  const [qDifficulty, setQDifficulty] = useState('')
  const [qOffset, setQOffset] = useState(0)
  const [qLoading, setQLoading] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newQ, setNewQ] = useState({ category: 'general', difficulty: 2, question: '', options: ['', '', '', ''], correct_index: 0 })

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

  async function loadQuestions() {
    if (!auth?.token) return
    setQLoading(true)
    try {
      const params = { limit: 50, offset: qOffset }
      if (qSearch) params.q = qSearch
      if (qCategory) params.category = qCategory
      if (qDifficulty) params.difficulty = qDifficulty
      const res = await api.fetchAdminQuestions(auth.token, params)
      setQuestions(res.questions)
      setQTotal(res.total)
    } catch (e) {
      setError(e.message || 'Failed to load questions')
    } finally {
      setQLoading(false)
    }
  }

  useEffect(() => {
    if (auth?.token) loadStats()
    intervalRef.current = setInterval(() => {
      if (auth?.token) loadStats()
    }, 30000)
    return () => clearInterval(intervalRef.current)
  }, [auth?.token])

  useEffect(() => {
    if (auth?.token) loadQuestions()
  }, [auth?.token, qSearch, qCategory, qDifficulty, qOffset])

  async function handleCloseRoom(code) {
    if (!confirm(`Close room ${code}?`)) return
    setActionLoading(code)
    try {
      await api.adminCloseRoom(auth.token, code)
      await loadStats()
    } catch (e) {
      setError(e.message)
    } finally {
      setActionLoading(null)
    }
  }

  async function handleCleanup() {
    const stale = stats?.active_rooms?.filter(r => r.connected_players === 0).length || 0
    if (!confirm(`Close ${stale} stale rooms with 0 connected players?`)) return
    setActionLoading('cleanup')
    try {
      const res = await api.adminCleanupRooms(auth.token)
      alert(`Closed ${res.closed_count} stale rooms`)
      await loadStats()
    } catch (e) {
      setError(e.message)
    } finally {
      setActionLoading(null)
    }
  }

  async function handleDeleteQuestion(id) {
    if (!confirm(`Delete question ${id}?`)) return
    try {
      await api.deleteAdminQuestion(auth.token, id)
      await loadQuestions()
      await loadStats() // refresh totals
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleAddQuestion(e) {
    e.preventDefault()
    if (newQ.options.some(o => !o.trim())) { setError('All 4 options required'); return }
    if (!newQ.question.trim()) { setError('Question text required'); return }
    try {
      await api.createAdminQuestion(auth.token, newQ)
      setNewQ({ category: 'general', difficulty: 2, question: '', options: ['', '', '', ''], correct_index: 0 })
      setShowAddForm(false)
      await loadQuestions()
      await loadStats()
    } catch (e) {
      setError(e.message)
    }
  }

  const staleCount = stats?.active_rooms?.filter(r => r.connected_players === 0).length || 0
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
              <div className="flex items-center gap-2">
                {staleCount > 0 && (
                  <button
                    className="text-xs px-3 py-1.5 rounded-lg bg-danger/10 text-danger hover:bg-danger/20 transition"
                    onClick={handleCleanup}
                    disabled={actionLoading === 'cleanup'}
                  >
                    {actionLoading === 'cleanup' ? '...' : `Cleanup ${staleCount} Stale`}
                  </button>
                )}
                <span className="badge bg-accent/10 text-accent text-xs">{stats.active_rooms?.length || 0}</span>
              </div>
            </div>
            {stats.active_rooms?.length === 0 && (
              <div className="text-sm text-slate/40 py-2">No active rooms right now.</div>
            )}
            {stats.active_rooms?.map((room) => (
              <div key={room.code} className="rounded-xl border border-black/5 overflow-hidden">
                <div
                  className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-black/[.02] transition"
                  onClick={() => setExpandedRoom(expandedRoom === room.code ? null : room.code)}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="font-display text-lg tracking-wider">{room.code}</span>
                    <span className="badge bg-accent/10 text-accent text-[10px]">
                      {GAME_LABELS[room.game_type] || room.game_type}
                    </span>
                    {room.game_type === 'trivia' && room.trivia_category && (
                      <span className="text-[10px] text-slate/40">{room.trivia_category}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate/50 shrink-0">
                    <span className={room.status === 'active' ? 'text-correct font-medium' : 'text-accent'}>
                      {room.status === 'active' ? 'In Game' : 'Lobby'}
                    </span>
                    <span>{room.connected_players}/{room.max_players}</span>
                    {room.created_at && (
                      <span>{new Date(room.created_at).toLocaleTimeString()}</span>
                    )}
                    <button
                      className="text-[10px] px-2 py-1 rounded bg-danger/10 text-danger hover:bg-danger/20 transition"
                      onClick={(e) => { e.stopPropagation(); handleCloseRoom(room.code) }}
                      disabled={actionLoading === room.code}
                    >
                      {actionLoading === room.code ? '...' : 'Close'}
                    </button>
                  </div>
                </div>
                {expandedRoom === room.code && room.players && (
                  <div className="px-4 pb-3 pt-1 border-t border-black/5">
                    <div className="flex flex-wrap gap-2">
                      {room.players.map((p) => (
                        <span key={p.id} className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full bg-black/[.03]">
                          <span className={`w-1.5 h-1.5 rounded-full ${p.connected ? 'bg-correct' : 'bg-slate/30'}`} />
                          {p.name}
                        </span>
                      ))}
                      {(!room.players || room.players.length === 0) && (
                        <span className="text-xs text-slate/40">No players</span>
                      )}
                    </div>
                  </div>
                )}
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

          {/* Question Management */}
          <div className="card p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">Questions</h2>
              <button
                className="text-xs px-3 py-1.5 rounded-lg bg-accent/10 text-accent hover:bg-accent/20 transition"
                onClick={() => setShowAddForm(!showAddForm)}
              >
                {showAddForm ? 'Cancel' : '+ Add Question'}
              </button>
            </div>

            {/* Add question form */}
            {showAddForm && (
              <form onSubmit={handleAddQuestion} className="space-y-3 p-4 rounded-xl border border-accent/20 bg-accent/[.02]">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-slate/50 block mb-1">Category</label>
                    <select
                      className="w-full text-sm border border-black/10 rounded-lg px-3 py-2 bg-white"
                      value={newQ.category}
                      onChange={(e) => setNewQ({ ...newQ, category: e.target.value })}
                    >
                      {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-slate/50 block mb-1">Difficulty</label>
                    <select
                      className="w-full text-sm border border-black/10 rounded-lg px-3 py-2 bg-white"
                      value={newQ.difficulty}
                      onChange={(e) => setNewQ({ ...newQ, difficulty: Number(e.target.value) })}
                    >
                      {DIFFICULTIES.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-slate/50 block mb-1">Question</label>
                  <input
                    className="w-full text-sm border border-black/10 rounded-lg px-3 py-2"
                    value={newQ.question}
                    onChange={(e) => setNewQ({ ...newQ, question: e.target.value })}
                    placeholder="Enter question text..."
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {newQ.options.map((opt, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="correct"
                        checked={newQ.correct_index === i}
                        onChange={() => setNewQ({ ...newQ, correct_index: i })}
                        className="accent-correct"
                      />
                      <input
                        className="flex-1 text-sm border border-black/10 rounded-lg px-3 py-2"
                        value={opt}
                        onChange={(e) => {
                          const opts = [...newQ.options]
                          opts[i] = e.target.value
                          setNewQ({ ...newQ, options: opts })
                        }}
                        placeholder={`Option ${i + 1}`}
                      />
                    </div>
                  ))}
                </div>
                <p className="text-[10px] text-slate/40">Select the radio button next to the correct answer.</p>
                <button type="submit" className="btn-ghost-sm bg-accent/10 text-accent hover:bg-accent/20">
                  Add Question
                </button>
              </form>
            )}

            {/* Filters */}
            <div className="flex flex-wrap gap-2">
              <input
                className="flex-1 min-w-[180px] text-sm border border-black/10 rounded-lg px-3 py-2"
                placeholder="Search questions..."
                value={qSearch}
                onChange={(e) => { setQSearch(e.target.value); setQOffset(0) }}
              />
              <select
                className="text-sm border border-black/10 rounded-lg px-3 py-2 bg-white"
                value={qCategory}
                onChange={(e) => { setQCategory(e.target.value); setQOffset(0) }}
              >
                <option value="">All Categories</option>
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <select
                className="text-sm border border-black/10 rounded-lg px-3 py-2 bg-white"
                value={qDifficulty}
                onChange={(e) => { setQDifficulty(e.target.value); setQOffset(0) }}
              >
                <option value="">All Difficulties</option>
                {DIFFICULTIES.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
              </select>
            </div>

            {/* Results info */}
            <div className="flex items-center justify-between text-xs text-slate/50">
              <span>{qLoading ? 'Loading...' : `${qTotal} questions`}</span>
              <div className="flex items-center gap-2">
                <button
                  className="px-2 py-1 rounded bg-black/5 hover:bg-black/10 disabled:opacity-30"
                  disabled={qOffset === 0}
                  onClick={() => setQOffset(Math.max(0, qOffset - 50))}
                >
                  Prev
                </button>
                <span>{qOffset + 1}-{Math.min(qOffset + 50, qTotal)}</span>
                <button
                  className="px-2 py-1 rounded bg-black/5 hover:bg-black/10 disabled:opacity-30"
                  disabled={qOffset + 50 >= qTotal}
                  onClick={() => setQOffset(qOffset + 50)}
                >
                  Next
                </button>
              </div>
            </div>

            {/* Question list */}
            <div className="space-y-1.5 max-h-[500px] overflow-y-auto">
              {questions?.map((q) => (
                <div key={q.id} className="flex items-start justify-between rounded-xl border border-black/5 px-4 py-2.5 gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-[10px] font-mono text-slate/40">{q.id}</span>
                      <span className="text-[10px] capitalize text-slate/50">{q.category}</span>
                      <span className="text-[10px] text-slate/40">
                        {q.difficulty === 1 ? 'Easy' : q.difficulty === 2 ? 'Medium' : 'Hard'}
                      </span>
                    </div>
                    <div className="text-sm leading-snug">{q.question}</div>
                    <div className="text-[10px] text-correct mt-0.5">
                      {q.options?.[q.correct_index]}
                    </div>
                  </div>
                  <button
                    className="text-[10px] px-2 py-1 rounded bg-danger/10 text-danger hover:bg-danger/20 transition shrink-0 mt-1"
                    onClick={() => handleDeleteQuestion(q.id)}
                  >
                    Delete
                  </button>
                </div>
              ))}
              {questions?.length === 0 && (
                <div className="text-sm text-slate/40 py-4 text-center">No questions found.</div>
              )}
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
