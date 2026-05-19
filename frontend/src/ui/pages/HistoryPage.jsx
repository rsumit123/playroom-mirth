import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import HistoryScreen from '../screens/HistoryScreen.jsx'
import * as api from '../../lib/api.js'
import { useApp } from '../../state/AppContext.jsx'

const PAGE_SIZE = 20

export default function HistoryPage() {
  const navigate = useNavigate()
  const { auth } = useApp()
  const [tab, setTab] = useState('all')
  const [stats, setStats] = useState(null)
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(false)

  // Guests redirect home — history is signed-in only.
  useEffect(() => {
    if (!auth?.token) navigate('/home', { replace: true })
  }, [auth?.token])

  const loadStats = useCallback(async () => {
    if (!auth?.token) return
    try {
      const data = await api.getGameHistoryStats(auth.token, { origin: 'all' })
      setStats(data)
    } catch { /* leave stats null, UI shows skeleton */ }
  }, [auth?.token])

  const loadPage = useCallback(async (origin, offset) => {
    if (!auth?.token) return []
    const data = await api.getGameHistory(auth.token, { origin, limit: PAGE_SIZE, offset })
    return data
  }, [auth?.token])

  useEffect(() => { loadStats() }, [loadStats])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setRows([])
    setHasMore(false)
    loadPage(tab, 0).then(data => {
      if (cancelled) return
      setRows(data)
      setHasMore(data.length === PAGE_SIZE)
    }).finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [tab, loadPage])

  async function handleLoadMore() {
    setLoadingMore(true)
    try {
      const more = await loadPage(tab, rows.length)
      setRows(prev => [...prev, ...more])
      setHasMore(more.length === PAGE_SIZE)
    } finally {
      setLoadingMore(false)
    }
  }

  return (
    <HistoryScreen
      tab={tab}
      onTabChange={setTab}
      stats={stats}
      rows={rows}
      loading={loading}
      loadingMore={loadingMore}
      hasMore={hasMore}
      onLoadMore={handleLoadMore}
      onBack={() => navigate('/home')}
    />
  )
}
