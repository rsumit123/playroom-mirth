import PlayerAvatar from './PlayerAvatar.jsx'

export default function NotificationDrawer({ open, notifications, onAcceptFriend, onRejectFriend, onJoinRoom, onClose }) {
  if (!open) return null

  const { friend_requests_list = [], game_invites = [] } = notifications || {}
  const empty = friend_requests_list.length === 0 && game_invites.length === 0

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/30" onClick={onClose} />
      <div className="fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur rounded-t-2xl shadow-2xl p-4 max-h-[70vh] overflow-y-auto safe-area-bottom animate-pop">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Notifications</h3>
          <button className="text-slate/40 text-xl touch-target" onClick={onClose}>&times;</button>
        </div>

        {empty && (
          <div className="py-8 text-center text-slate/40 text-sm">No notifications</div>
        )}

        {/* Game Invites */}
        {game_invites.length > 0 && (
          <div className="mb-4">
            <div className="text-xs uppercase tracking-wider text-slate/50 mb-2">Game Invites</div>
            <div className="space-y-2">
              {game_invites.map(inv => (
                <div key={inv.id} className="card px-4 py-3 flex items-center gap-3">
                  <PlayerAvatar name={inv.from_user?.display_name || 'User'} size="sm" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm">
                      <span className="font-medium">{inv.from_user?.display_name}</span>
                      <span className="text-slate/50"> invited you to play</span>
                    </div>
                    <div className="text-xs text-slate/40">Room {inv.room_code}</div>
                  </div>
                  <button
                    className="bg-accent text-white rounded-lg px-3 py-1.5 text-xs font-semibold touch-target shrink-0"
                    onClick={() => onJoinRoom(inv.room_code)}
                  >
                    Join
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Friend Requests */}
        {friend_requests_list.length > 0 && (
          <div>
            <div className="text-xs uppercase tracking-wider text-slate/50 mb-2">Friend Requests</div>
            <div className="space-y-2">
              {friend_requests_list.map(req => (
                <div key={req.id} className="card px-4 py-3 flex items-center gap-3">
                  <PlayerAvatar name={req.display_name || 'User'} size="sm" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">{req.display_name}</div>
                    <div className="text-xs text-slate/40">Wants to be friends</div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      className="bg-accent text-white rounded-lg px-2.5 py-1.5 text-xs font-semibold touch-target"
                      onClick={() => onAcceptFriend(req.id)}
                    >
                      Accept
                    </button>
                    <button
                      className="btn-ghost-sm touch-target text-xs text-slate/50"
                      onClick={() => onRejectFriend(req.id)}
                    >
                      Decline
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  )
}
