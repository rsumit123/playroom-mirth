import { useEffect, useState } from 'react'
import { useApp } from '../../state/AppContext.jsx'
import * as api from '../../lib/api.js'

export default function AdminWordsPage() {
  const { auth } = useApp()
  const [token, setToken] = useState(auth?.token || '')
  const [words, setWords] = useState([])
  const [error, setError] = useState(null)
  const [form, setForm] = useState({ text: '', difficulty: 1 })
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(0)

  async function loadWords(nextPage = page) {
    try {
      const res = await api.fetchAdminWords(token, { q: query || undefined, limit: 20, offset: nextPage * 20 })
      setWords(res)
      setError(null)
      setPage(nextPage)
    } catch (e) {
      setError('Failed to load words. Check token.')
    }
  }

  async function addWord() {
    try {
      const res = await api.createAdminWord(token, form)
      setWords((w) => [res, ...w])
      setForm({ text: '', difficulty: 1 })
    } catch (e) {
      setError('Failed to add word.')
    }
  }

  async function toggleActive(word) {
    try {
      const res = await api.updateAdminWord(token, word.id, { active: !word.active })
      setWords((w) => w.map((item) => (item.id === word.id ? res : item)))
    } catch (e) {
      setError('Failed to update word.')
    }
  }

  useEffect(() => {
    if (token) loadWords(0)
  }, [])

  return (
    <div className="min-h-screen px-6 py-10 space-y-6">
      <div className="card p-6 space-y-4">
        <div className="font-display text-2xl">Admin Word Manager</div>
        <div className="text-sm text-slate/60">This page is hidden from normal navigation.</div>
        <input
          className="rounded-xl border border-black/10 px-4 py-3"
          placeholder="JWT token"
          value={token}
          onChange={(e) => setToken(e.target.value)}
        />
        <div className="flex gap-3">
          <input
            className="flex-1 rounded-xl border border-black/10 px-4 py-3"
            placeholder="Search words"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn-ghost" onClick={() => loadWords(0)}>Search</button>
        </div>
        <button className="btn-ghost w-full" onClick={() => loadWords(0)}>Load Words</button>
        {error && <div className="text-sm text-red-600">{error}</div>}
      </div>

      <div className="card p-6 space-y-4">
        <div className="font-semibold">Add Word</div>
        <input
          className="rounded-xl border border-black/10 px-4 py-3"
          placeholder="Word text"
          value={form.text}
          onChange={(e) => setForm((f) => ({ ...f, text: e.target.value }))}
        />
        <input
          className="rounded-xl border border-black/10 px-4 py-3"
          placeholder="Difficulty (1-3)"
          value={form.difficulty}
          onChange={(e) => setForm((f) => ({ ...f, difficulty: Number(e.target.value) }))}
        />
        <button className="btn-primary w-full" onClick={addWord}>Add Word</button>
      </div>

      <div className="card p-6 space-y-3">
        <div className="font-semibold">Words</div>
        {words.length === 0 && <div className="text-sm text-slate/60">No words loaded.</div>}
        {words.slice(0, 50).map((w) => (
          <div key={w.id} className="flex items-center justify-between rounded-xl border border-black/5 px-4 py-2">
            <div className="text-sm">{w.text} <span className="text-xs text-slate/50">(d{w.difficulty})</span></div>
            <button className="btn-ghost" onClick={() => toggleActive(w)}>{w.active ? 'Disable' : 'Enable'}</button>
          </div>
        ))}
        <div className="flex items-center justify-between pt-2">
          <button className="btn-ghost" onClick={() => loadWords(Math.max(page - 1, 0))}>Prev</button>
          <div className="text-xs text-slate/60">Page {page + 1}</div>
          <button className="btn-ghost" onClick={() => loadWords(page + 1)}>Next</button>
        </div>
      </div>
    </div>
  )
}
