import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApp } from '../../state/AppContext.jsx'
import * as api from '../../lib/api.js'
import PlayerAvatar from '../components/PlayerAvatar.jsx'

export default function FriendsPage() {
  const navigate = useNavigate()
  const { auth } = useApp()
  const token = auth?.token

  const [friends, setFriends] = useState([])
  const [requests, setRequests] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [tab, setTab] = useState('friends') // 'friends' | 'requests' | 'search'
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(null)

  const fetchData = useCallback(async () => {
    if (!token) return
    try {
      const [friendsRes, requestsRes] = await Promise.all([
        api.getFriends(token),
        api.getFriendRequests(token),
      ])
      setFriends(friendsRes.friends || [])
      setRequests(requestsRes.requests || [])
    } catch {
      // errors handled by api.js
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    if (!token) {
      navigate('/home', { replace: true })
      return
    }
    fetchData()
  }, [token, fetchData])

  // Auto-refresh when switching tabs (friends/requests)
  useEffect(() => {
    if (tab === 'friends' || tab === 'requests') fetchData()
  }, [tab])

  async function handleSearch() {
    if (!searchQuery.trim() || !token) return
    setSearching(true)
    try {
      const res = await api.searchUsers(token, searchQuery.trim())
      setSearchResults(res.users || [])
    } catch {
      setSearchResults([])
    } finally {
      setSearching(false)
    }
  }

  async function handleSendRequest(userId) {
    if (!token) return
    setActionLoading(userId)
    try {
      const res = await api.sendFriendRequest(token, userId)
      // Update search results to show status
      setSearchResults(prev => prev.map(u =>
        u.id === userId ? { ...u, requestStatus: res.status } : u
      ))
      if (res.status === 'accepted') {
        await fetchData() // refresh friends list
      }
    } catch { /* */ } finally {
      setActionLoading(null)
    }
  }

  async function handleAccept(userId) {
    if (!token) return
    setActionLoading(userId)
    try {
      await api.acceptFriendRequest(token, userId)
      await fetchData()
    } catch { /* */ } finally {
      setActionLoading(null)
    }
  }

  async function handleReject(userId) {
    if (!token) return
    setActionLoading(userId)
    try {
      await api.rejectFriend(token, userId)
      await fetchData()
    } catch { /* */ } finally {
      setActionLoading(null)
    }
  }

  async function handleRemove(userId) {
    if (!token) return
    setActionLoading(userId)
    try {
      await api.rejectFriend(token, userId)
      await fetchData()
    } catch { /* */ } finally {
      setActionLoading(null)
    }
  }

  return (
    <div className="game-shell">
      <div className="flex-1 overflow-y-auto">
        <div className="page-medium py-6 space-y-5">

          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <button className="btn-ghost-sm touch-target mb-2" onClick={() => navigate('/home')}>&larr; Back</button>
              <h1 className="font-display text-2xl">Friends</h1>
            </div>
            <div className="flex items-center gap-2">
              {requests.length > 0 && tab !== 'requests' && (
                <button
                  className="badge bg-danger/10 text-danger text-xs font-semibold px-2.5 py-1 cursor-pointer"
                  onClick={() => setTab('requests')}
                >
                  {requests.length} pending
                </button>
              )}
              <button
                className="btn-ghost-sm touch-target w-9 h-9 flex items-center justify-center text-base"
                onClick={() => { setLoading(true); fetchData() }}
                title="Refresh"
              >
                &#8635;
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="segmented">
            <button
              className={tab === 'friends' ? 'segmented-option-active' : 'segmented-option'}
              onClick={() => setTab('friends')}
            >
              Friends ({friends.length})
            </button>
            <button
              className={tab === 'requests' ? 'segmented-option-active' : 'segmented-option'}
              onClick={() => setTab('requests')}
            >
              Requests {requests.length > 0 && `(${requests.length})`}
            </button>
            <button
              className={tab === 'search' ? 'segmented-option-active' : 'segmented-option'}
              onClick={() => setTab('search')}
            >
              Add Friend
            </button>
          </div>

          {/* Friends Tab */}
          {tab === 'friends' && (
            <div className="space-y-2">
              {loading ? (
                <div className="card p-8 text-center text-slate/40">Loading...</div>
              ) : friends.length === 0 ? (
                <div className="card p-8 text-center space-y-3">
                  <div className="text-3xl">&#128075;</div>
                  <div className="text-slate/50 text-sm">No friends yet</div>
                  <button
                    className="btn-primary px-6 py-2.5 text-sm touch-target mx-auto"
                    onClick={() => setTab('search')}
                  >
                    Find Friends
                  </button>
                </div>
              ) : (
                friends.map(f => (
                  <div key={f.id} className="card px-4 py-3 flex items-center gap-3">
                    <div className="relative">
                      <PlayerAvatar name={f.display_name || 'User'} size="md" />
                      {f.is_online && <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-correct border-2 border-white" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{f.display_name}</div>
                      <div className={`text-xs ${f.is_online ? 'text-correct' : 'text-slate/40'}`}>{f.is_online ? 'Online' : 'Offline'}</div>
                    </div>
                    <button
                      className="btn-ghost-sm touch-target text-danger/60 text-xs"
                      onClick={() => handleRemove(f.id)}
                      disabled={actionLoading === f.id}
                    >
                      Remove
                    </button>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Requests Tab */}
          {tab === 'requests' && (
            <div className="space-y-2">
              {requests.length === 0 ? (
                <div className="card p-8 text-center text-slate/40 text-sm">No pending requests</div>
              ) : (
                requests.map(r => (
                  <div key={r.id} className="card px-4 py-3 flex items-center gap-3">
                    <PlayerAvatar name={r.display_name || 'User'} size="md" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{r.display_name}</div>
                      <div className="text-xs text-slate/40">Wants to be friends</div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        className="bg-accent text-white rounded-lg px-3 py-1.5 text-xs font-semibold touch-target"
                        onClick={() => handleAccept(r.id)}
                        disabled={actionLoading === r.id}
                      >
                        Accept
                      </button>
                      <button
                        className="btn-ghost-sm touch-target text-xs text-slate/50"
                        onClick={() => handleReject(r.id)}
                        disabled={actionLoading === r.id}
                      >
                        Decline
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Search/Add Tab */}
          {tab === 'search' && (
            <div className="space-y-4">
              <div className="flex gap-2">
                <input
                  className="flex-1 rounded-xl border border-black/10 px-4 py-3 text-sm outline-none focus:border-accent touch-target"
                  placeholder="Search by name..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSearch()}
                />
                <button
                  className="btn-primary px-4 py-2.5 text-sm touch-target shrink-0"
                  onClick={handleSearch}
                  disabled={searching || !searchQuery.trim()}
                >
                  {searching ? '...' : 'Search'}
                </button>
              </div>

              <div className="space-y-2">
                {searchResults.length === 0 && searchQuery && !searching && (
                  <div className="card p-6 text-center text-slate/40 text-sm">No users found for "{searchQuery}"</div>
                )}
                {searchResults.map(u => {
                  const isFriend = friends.some(f => f.id === u.id)
                  const isPending = u.requestStatus === 'pending' || requests.some(r => r.id === u.id)
                  const isAccepted = u.requestStatus === 'accepted' || u.requestStatus === 'already_friends'

                  return (
                    <div key={u.id} className="card px-4 py-3 flex items-center gap-3">
                      <PlayerAvatar name={u.display_name || 'User'} size="md" />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm truncate">{u.display_name}</div>
                      </div>
                      {isFriend || isAccepted ? (
                        <span className="text-xs text-correct font-medium">Friends</span>
                      ) : isPending ? (
                        <span className="text-xs text-slate/50 font-medium">Pending</span>
                      ) : (
                        <button
                          className="bg-accent text-white rounded-lg px-3 py-1.5 text-xs font-semibold touch-target"
                          onClick={() => handleSendRequest(u.id)}
                          disabled={actionLoading === u.id}
                        >
                          {actionLoading === u.id ? '...' : 'Add Friend'}
                        </button>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  )
}
