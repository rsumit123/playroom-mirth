import { useState, useRef } from 'react'
import PlayerAvatar from './PlayerAvatar.jsx'

export default function InviteFriendsDrawer({ open, friends, onInvite, onClose }) {
  const [invitedIds, setInvitedIds] = useState(new Set())
  const [loadingId, setLoadingId] = useState(null)
  const prevOpenRef = useRef(false)

  // Reset only on closed → open transition (not on every re-render while open)
  if (open && !prevOpenRef.current) {
    setInvitedIds(new Set())
  }
  prevOpenRef.current = open

  if (!open) return null

  const online = (friends || []).filter(f => f.is_online)
  const offline = (friends || []).filter(f => !f.is_online)

  async function handleInvite(friendId) {
    setLoadingId(friendId)
    try {
      await onInvite(friendId)
      setInvitedIds(prev => new Set([...prev, friendId]))
    } catch { /* */ } finally {
      setLoadingId(null)
    }
  }

  function renderFriendRow(f, showOnlineDot) {
    return (
      <div key={f.id} className="card px-4 py-3 flex items-center gap-3">
        <div className="relative">
          <PlayerAvatar name={f.display_name || 'User'} size="sm" />
          {showOnlineDot && <div className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-correct border-2 border-white" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm truncate">{f.display_name}</div>
          {!f.is_online && <div className="text-xs text-slate/40">Offline</div>}
        </div>
        {invitedIds.has(f.id) ? (
          <span className="text-xs text-correct font-medium">Invited</span>
        ) : (
          <button
            className="bg-accent text-white rounded-lg px-3 py-1.5 text-xs font-semibold touch-target shrink-0"
            onClick={() => handleInvite(f.id)}
            disabled={loadingId === f.id}
          >
            {loadingId === f.id ? '...' : 'Invite'}
          </button>
        )}
      </div>
    )
  }

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/30" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur rounded-t-2xl shadow-2xl p-4 max-h-[70vh] overflow-y-auto safe-area-bottom animate-pop">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Invite Friends</h3>
          <button className="text-slate/40 text-xl touch-target" onClick={onClose}>&times;</button>
        </div>

        {(friends || []).length === 0 && (
          <div className="py-8 text-center text-slate/40 text-sm">
            <div className="text-2xl mb-2">&#128075;</div>
            Add friends from the Home screen to invite them here
          </div>
        )}

        {/* Online Friends */}
        {online.length > 0 && (
          <div className="mb-4">
            <div className="text-xs uppercase tracking-wider text-slate/50 mb-2">Online ({online.length})</div>
            <div className="space-y-2">
              {online.map(f => renderFriendRow(f, true))}
            </div>
          </div>
        )}

        {/* Offline Friends -- can still invite (they'll see it when they open the app) */}
        {offline.length > 0 && (
          <div>
            <div className="text-xs uppercase tracking-wider text-slate/50 mb-2">Offline ({offline.length})</div>
            <div className="space-y-2">
              {offline.map(f => renderFriendRow(f, false))}
            </div>
          </div>
        )}
      </div>
    </>
  )
}
