import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import LeaderboardScreen from '../screens/LeaderboardScreen.jsx'
import * as api from '../../lib/api.js'
import { useApp } from '../../state/AppContext.jsx'

export default function LeaderboardPage() {
  const navigate = useNavigate()
  const { auth } = useApp()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!auth?.token) {
      navigate('/home', { replace: true })
      return
    }
    let cancelled = false
    setLoading(true)
    api.getLeaderboard(auth.token, { origin: 'quickmatch', limit: 10 })
      .then(res => { if (!cancelled) setData(res) })
      .catch(() => { /* leave data null, UI shows empty state */ })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [auth?.token])

  return (
    <LeaderboardScreen
      data={data}
      loading={loading}
      onBack={() => navigate('/home')}
      currentUserId={auth?.user?.id}
    />
  )
}
