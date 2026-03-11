import { useEffect, useState, useRef } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import * as api from '../../lib/api.js'

const GAME_LABELS = { charades: 'Charades', scribble: 'Scribble', trivia: 'Trivia' }
const CAT_ICONS = { science: '🔬', history: '📜', geography: '🌍', sports: '⚽', entertainment: '🎬', general: '💡', mythology: '🛕', food: '🍛', politics: '🏛️' }
const CATEGORIES = ['science', 'history', 'geography', 'sports', 'entertainment', 'general', 'mythology', 'food', 'politics']
const DIFFICULTIES = [{ value: 1, label: 'Easy' }, { value: 2, label: 'Medium' }, { value: 3, label: 'Hard' }]
const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'trivia', label: 'Trivia' },
  { id: 'charades', label: 'Charades' },
  { id: 'scribble', label: 'Scribble' },
]
const ADMIN_PASSWORD = 'playroomadmin@018'

export default function AdminDashboardPage() {
  const { auth } = useApp()
  const [authed, setAuthed] = useState(() => sessionStorage.getItem('admin_authed') === '1')
  const [pwInput, setPwInput] = useState('')
  const [pwError, setPwError] = useState(false)
  const [showPw, setShowPw] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [lastRefresh, setLastRefresh] = useState(null)
  const [expandedRoom, setExpandedRoom] = useState(null)
  const [actionLoading, setActionLoading] = useState(null)
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
    if (!authed || !auth?.token) return
    loadStats()
    intervalRef.current = setInterval(() => {
      if (auth?.token) loadStats()
    }, 30000)
    return () => clearInterval(intervalRef.current)
  }, [auth?.token, authed])

  function handlePasswordSubmit(e) {
    e.preventDefault()
    if (pwInput === ADMIN_PASSWORD) {
      sessionStorage.setItem('admin_authed', '1')
      setAuthed(true)
      setPwError(false)
    } else {
      setPwError(true)
    }
  }

  if (!authed) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <form onSubmit={handlePasswordSubmit} className="card p-6 sm:p-8 w-full max-w-sm space-y-4">
          <h1 className="font-display text-xl text-center">Admin Access</h1>
          <p className="text-sm text-slate/50 text-center">Enter the admin password to continue.</p>
          <div className="relative">
            <input
              type={showPw ? 'text' : 'password'}
              className="w-full text-sm border border-black/10 rounded-lg px-4 py-3 pr-11"
              placeholder="Password"
              value={pwInput}
              onChange={(e) => { setPwInput(e.target.value); setPwError(false) }}
              autoFocus
            />
            <button
              type="button"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate/40 hover:text-slate/70 transition p-1"
              onClick={() => setShowPw(!showPw)}
              tabIndex={-1}
            >
              {showPw ? (
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              )}
            </button>
          </div>
          {pwError && <p className="text-xs text-danger text-center">Incorrect password.</p>}
          <button type="submit" className="w-full py-3 rounded-xl bg-accent text-white font-medium text-sm hover:bg-accent/90 transition">
            Enter
          </button>
        </form>
      </div>
    )
  }

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

  const staleCount = stats?.active_rooms?.filter(r => r.connected_players === 0).length || 0
  const t = stats?.totals || {}
  const pool = stats?.question_pool || {}

  return (
    <div className="min-h-screen px-4 sm:px-6 py-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="font-display text-2xl">Admin Dashboard</h1>
          <p className="text-xs text-slate/50">
            {lastRefresh ? `Updated ${lastRefresh.toLocaleTimeString()}` : 'Loading...'}
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

      {error && (
        <div className="card px-4 py-3 text-sm text-danger bg-danger/5 border-danger/20 mb-4">
          {error}
          <button className="ml-2 underline text-xs" onClick={() => setError(null)}>dismiss</button>
        </div>
      )}

      {!auth?.token && (
        <div className="card p-8 text-center text-slate/50">Sign in with Google to access admin stats.</div>
      )}

      {/* Tab bar */}
      {stats && (
        <>
          <div className="flex gap-1 mb-6 p-1 rounded-xl bg-black/[.03] sticky top-0 z-10">
            {TABS.map(tab => (
              <button
                key={tab.id}
                className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition ${activeTab === tab.id ? 'bg-white shadow-sm text-ink' : 'text-slate/50 hover:text-slate/70'}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-5">
              {/* Stat cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <StatCard label="Active Rooms" value={t.active_room_count || 0} color="accent" />
                <StatCard label="Connected" value={t.connected_players || 0} color="correct" />
                <StatCard label="Live Games" value={t.in_memory_games || 0} color="gold" />
                <StatCard label="Trivia Qs" value={t.total_questions || 0} color="accent" />
                <StatCard label="Charades" value={t.charades_words || 0} color="accent" />
                <StatCard label="Scribble" value={t.scribble_words || 0} color="accent" />
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
                      className="flex flex-col sm:flex-row sm:items-center justify-between px-4 py-3 gap-2 cursor-pointer hover:bg-black/[.02] transition"
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
                        <span className={`text-xs font-medium sm:hidden ${room.status === 'active' ? 'text-correct' : 'text-accent'}`}>
                          {room.status === 'active' ? 'In Game' : 'Lobby'}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate/50 shrink-0">
                        <span className={`hidden sm:inline ${room.status === 'active' ? 'text-correct font-medium' : 'text-accent'}`}>
                          {room.status === 'active' ? 'In Game' : 'Lobby'}
                        </span>
                        <span>{room.connected_players}/{room.max_players}</span>
                        {room.created_at && (
                          <span className="hidden sm:inline">{new Date(room.created_at).toLocaleTimeString()}</span>
                        )}
                        <button
                          className="text-[10px] px-2.5 py-1.5 rounded bg-danger/10 text-danger hover:bg-danger/20 transition touch-target"
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

              {/* Recent Games */}
              <div className="card p-5 space-y-3">
                <h2 className="font-semibold">Recent Games</h2>
                {stats.recent_games?.length === 0 && (
                  <div className="text-sm text-slate/40 py-2">No games played yet.</div>
                )}
                {stats.recent_games?.map((g, i) => (
                  <div key={i} className="flex flex-col sm:flex-row sm:items-center justify-between rounded-xl border border-black/5 px-4 py-2.5 gap-1 sm:gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="font-display text-sm tracking-wider">{g.room_code}</span>
                      <span className="badge bg-accent/10 text-accent text-[10px]">
                        {GAME_LABELS[g.game_type] || g.game_type}
                      </span>
                      {g.is_winner && <span title="Winner">🏆</span>}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate/50 shrink-0">
                      <span>{g.player_count}p</span>
                      <span>{g.score} pts</span>
                      {g.played_at && <span>{new Date(g.played_at).toLocaleDateString()}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Trivia Tab */}
          {activeTab === 'trivia' && (
            <TriviaTab auth={auth} stats={stats} pool={pool} t={t} setError={setError} onRefresh={loadStats} />
          )}

          {/* Charades Tab */}
          {activeTab === 'charades' && (
            <WordTab gameType="charades" auth={auth} wordCount={t.charades_words || 0} setError={setError} onRefresh={loadStats} />
          )}

          {/* Scribble Tab */}
          {activeTab === 'scribble' && (
            <WordTab gameType="scribble" auth={auth} wordCount={t.scribble_words || 0} setError={setError} onRefresh={loadStats} />
          )}
        </>
      )}
    </div>
  )
}

// ─── Trivia Tab ──────────────────────────────────────────────

function TriviaTab({ auth, stats, pool, t, setError, onRefresh }) {
  const [questions, setQuestions] = useState(null)
  const [qTotal, setQTotal] = useState(0)
  const [qSearch, setQSearch] = useState('')
  const [qCategory, setQCategory] = useState('')
  const [qDifficulty, setQDifficulty] = useState('')
  const [qOffset, setQOffset] = useState(0)
  const [qLoading, setQLoading] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newQ, setNewQ] = useState({ category: 'general', difficulty: 2, question: '', options: ['', '', '', ''], correct_index: 0 })

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
    loadQuestions()
  }, [qSearch, qCategory, qDifficulty, qOffset])

  async function handleDeleteQuestion(id) {
    if (!confirm(`Delete question ${id}?`)) return
    try {
      await api.deleteAdminQuestion(auth.token, id)
      await loadQuestions()
      await onRefresh()
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
      await onRefresh()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="space-y-5">
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
          <h2 className="font-semibold">Manage Questions</h2>
          <button
            className="text-xs px-3 py-1.5 rounded-lg bg-accent/10 text-accent hover:bg-accent/20 transition"
            onClick={() => setShowAddForm(!showAddForm)}
          >
            {showAddForm ? 'Cancel' : '+ Add Question'}
          </button>
        </div>

        {showAddForm && (
          <form onSubmit={handleAddQuestion} className="space-y-3 p-4 rounded-xl border border-accent/20 bg-accent/[.02]">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate/50 block mb-1">Category</label>
                <select
                  className="w-full text-sm border border-black/10 rounded-lg px-3 py-2.5 bg-white"
                  value={newQ.category}
                  onChange={(e) => setNewQ({ ...newQ, category: e.target.value })}
                >
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-slate/50 block mb-1">Difficulty</label>
                <select
                  className="w-full text-sm border border-black/10 rounded-lg px-3 py-2.5 bg-white"
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
                className="w-full text-sm border border-black/10 rounded-lg px-3 py-2.5"
                value={newQ.question}
                onChange={(e) => setNewQ({ ...newQ, question: e.target.value })}
                placeholder="Enter question text..."
              />
            </div>
            <div>
              <label className="text-xs text-slate/50 block mb-1">Options (select the correct answer)</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {newQ.options.map((opt, i) => (
                  <label
                    key={i}
                    className={`flex items-center gap-2.5 rounded-lg border px-3 py-2.5 cursor-pointer transition ${newQ.correct_index === i ? 'border-correct bg-correct/5' : 'border-black/10 hover:border-black/20'}`}
                  >
                    <input
                      type="radio"
                      name="correct"
                      checked={newQ.correct_index === i}
                      onChange={() => setNewQ({ ...newQ, correct_index: i })}
                      className="accent-correct w-4 h-4 shrink-0"
                    />
                    <input
                      className="flex-1 text-sm bg-transparent outline-none min-w-0"
                      value={opt}
                      onChange={(e) => {
                        const opts = [...newQ.options]
                        opts[i] = e.target.value
                        setNewQ({ ...newQ, options: opts })
                      }}
                      placeholder={`Option ${i + 1}`}
                    />
                    {newQ.correct_index === i && <span className="text-correct text-xs shrink-0">Correct</span>}
                  </label>
                ))}
              </div>
            </div>
            <button type="submit" className="btn-ghost-sm bg-accent/10 text-accent hover:bg-accent/20">
              Add Question
            </button>
          </form>
        )}

        {/* Filters */}
        <div className="space-y-2 sm:space-y-0 sm:flex sm:flex-wrap sm:gap-2">
          <input
            className="w-full sm:flex-1 sm:min-w-[180px] text-sm border border-black/10 rounded-lg px-3 py-2.5"
            placeholder="Search questions..."
            value={qSearch}
            onChange={(e) => { setQSearch(e.target.value); setQOffset(0) }}
          />
          <div className="flex gap-2">
            <select
              className="flex-1 sm:flex-none text-sm border border-black/10 rounded-lg px-3 py-2.5 bg-white"
              value={qCategory}
              onChange={(e) => { setQCategory(e.target.value); setQOffset(0) }}
            >
              <option value="">All Categories</option>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <select
              className="flex-1 sm:flex-none text-sm border border-black/10 rounded-lg px-3 py-2.5 bg-white"
              value={qDifficulty}
              onChange={(e) => { setQDifficulty(e.target.value); setQOffset(0) }}
            >
              <option value="">All Difficulties</option>
              {DIFFICULTIES.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
            </select>
          </div>
        </div>

        {/* Pagination */}
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
            <div key={q.id} className="rounded-xl border border-black/5 px-4 py-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-1.5 mb-1">
                    <span className="text-[10px] font-mono text-slate/40 break-all">{q.id}</span>
                    <span className="text-[10px] capitalize text-slate/50">{q.category}</span>
                    <span className="text-[10px] text-slate/40">
                      {q.difficulty === 1 ? 'Easy' : q.difficulty === 2 ? 'Medium' : 'Hard'}
                    </span>
                  </div>
                  <div className="text-sm leading-snug">{q.question}</div>
                  <div className="text-xs text-correct mt-1">
                    {q.options?.[q.correct_index]}
                  </div>
                </div>
                <button
                  className="text-[10px] px-2.5 py-1.5 rounded bg-danger/10 text-danger hover:bg-danger/20 transition shrink-0 touch-target"
                  onClick={() => handleDeleteQuestion(q.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
          {questions?.length === 0 && (
            <div className="text-sm text-slate/40 py-4 text-center">No questions found.</div>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Word Tab (reused for Charades & Scribble) ───────────────

function WordTab({ gameType, auth, wordCount, setError, onRefresh }) {
  const label = gameType.charAt(0).toUpperCase() + gameType.slice(1)
  const [words, setWords] = useState(null)
  const [search, setSearch] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(false)
  const [showAdd, setShowAdd] = useState(false)
  const [newWord, setNewWord] = useState({ text: '', difficulty: 1 })

  async function loadWords() {
    if (!auth?.token) return
    setLoading(true)
    try {
      const params = { limit: 50, offset, game_type: gameType }
      if (search) params.q = search
      if (difficulty) params.difficulty = difficulty
      const res = await api.fetchAdminWords(auth.token, params)
      setWords(res)
    } catch (e) {
      setError(e.message || 'Failed to load words')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadWords()
  }, [search, difficulty, offset])

  async function handleAdd(e) {
    e.preventDefault()
    if (!newWord.text.trim()) { setError('Word text required'); return }
    try {
      await api.createAdminWord(auth.token, { ...newWord, game_type: gameType })
      setNewWord({ text: '', difficulty: 1 })
      setShowAdd(false)
      await loadWords()
      await onRefresh()
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleToggle(word) {
    try {
      await api.updateAdminWord(auth.token, word.id, { active: !word.active })
      await loadWords()
      await onRefresh()
    } catch (e) {
      setError(e.message)
    }
  }

  async function handleDelete(id) {
    if (!confirm('Delete this word?')) return
    try {
      await api.deleteAdminWord(auth.token, id)
      await loadWords()
      await onRefresh()
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="space-y-5">
      {/* Summary */}
      <div className="card p-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold">{label} Words</h2>
            <p className="text-xs text-slate/50 mt-0.5">{wordCount} active words in pool</p>
          </div>
          <div className="font-display text-3xl text-accent">{wordCount}</div>
        </div>
      </div>

      {/* Word Management */}
      <div className="card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Manage Words</h2>
          <button
            className="text-xs px-3 py-1.5 rounded-lg bg-accent/10 text-accent hover:bg-accent/20 transition"
            onClick={() => setShowAdd(!showAdd)}
          >
            {showAdd ? 'Cancel' : '+ Add Word'}
          </button>
        </div>

        {showAdd && (
          <form onSubmit={handleAdd} className="space-y-3 p-4 rounded-xl border border-accent/20 bg-accent/[.02]">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate/50 block mb-1">Word</label>
                <input
                  className="w-full text-sm border border-black/10 rounded-lg px-3 py-2.5"
                  value={newWord.text}
                  onChange={(e) => setNewWord({ ...newWord, text: e.target.value })}
                  placeholder={`Enter ${gameType} word...`}
                  autoFocus
                />
              </div>
              <div>
                <label className="text-xs text-slate/50 block mb-1">Difficulty</label>
                <select
                  className="w-full text-sm border border-black/10 rounded-lg px-3 py-2.5 bg-white"
                  value={newWord.difficulty}
                  onChange={(e) => setNewWord({ ...newWord, difficulty: Number(e.target.value) })}
                >
                  {DIFFICULTIES.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
                </select>
              </div>
            </div>
            <button type="submit" className="btn-ghost-sm bg-accent/10 text-accent hover:bg-accent/20">
              Add Word
            </button>
          </form>
        )}

        {/* Filters */}
        <div className="space-y-2 sm:space-y-0 sm:flex sm:gap-2">
          <input
            className="w-full sm:flex-1 text-sm border border-black/10 rounded-lg px-3 py-2.5"
            placeholder="Search words..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setOffset(0) }}
          />
          <select
            className="w-full sm:w-auto text-sm border border-black/10 rounded-lg px-3 py-2.5 bg-white"
            value={difficulty}
            onChange={(e) => { setDifficulty(e.target.value); setOffset(0) }}
          >
            <option value="">All Difficulties</option>
            {DIFFICULTIES.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
          </select>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between text-xs text-slate/50">
          <span>{loading ? 'Loading...' : `${words?.length || 0} words`}</span>
          <div className="flex items-center gap-2">
            <button
              className="px-2 py-1 rounded bg-black/5 hover:bg-black/10 disabled:opacity-30"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - 50))}
            >
              Prev
            </button>
            <span>Page {Math.floor(offset / 50) + 1}</span>
            <button
              className="px-2 py-1 rounded bg-black/5 hover:bg-black/10 disabled:opacity-30"
              disabled={!words || words.length < 50}
              onClick={() => setOffset(offset + 50)}
            >
              Next
            </button>
          </div>
        </div>

        {/* Word list */}
        <div className="space-y-1.5 max-h-[500px] overflow-y-auto">
          {words?.map((w) => (
            <div key={w.id} className="rounded-xl border border-black/5 px-4 py-2.5">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0 flex-1 flex-wrap">
                  <span className="text-sm font-medium">{w.text}</span>
                  <span className="text-[10px] text-slate/40">
                    {w.difficulty === 1 ? 'Easy' : w.difficulty === 2 ? 'Medium' : 'Hard'}
                  </span>
                  {!w.active && <span className="text-[10px] text-danger">Disabled</span>}
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <button
                    className={`text-[10px] px-2 py-1 rounded transition touch-target ${w.active ? 'bg-slate/10 text-slate/60 hover:bg-slate/20' : 'bg-correct/10 text-correct hover:bg-correct/20'}`}
                    onClick={() => handleToggle(w)}
                  >
                    {w.active ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    className="text-[10px] px-2 py-1 rounded bg-danger/10 text-danger hover:bg-danger/20 transition touch-target"
                    onClick={() => handleDelete(w.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
          {words?.length === 0 && (
            <div className="text-sm text-slate/40 py-4 text-center">No words found.</div>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Shared Components ───────────────────────────────────────

function StatCard({ label, value, color = 'accent' }) {
  return (
    <div className="card p-4 text-center">
      <div className={`font-display text-3xl text-${color}`}>{value}</div>
      <div className="text-xs text-slate/50 mt-1">{label}</div>
    </div>
  )
}
