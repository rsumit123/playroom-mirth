import { useState } from 'react'
import Logo from './Logo.jsx'
import { toggleMute, isMuted } from '../../lib/sounds.js'

export default function TopBar({ userEmail, userDisplayName, userAvatarUrl, isAuthed, isGuest, guestDisplayName, onLogout, onHome, onHowTo }) {
  const displayLabel = userDisplayName || userEmail || 'Signed in'
  const [muted, setMuted] = useState(isMuted())

  return (
    <div className="sticky top-0 z-20 w-full border-b border-black/5 bg-white/70 backdrop-blur">
      <div className="page-medium py-3 flex items-center justify-between">
        <Logo compact onClick={onHome} />

        <div className="flex items-center gap-2 text-sm">
          <button
            className="btn-ghost-sm touch-target w-9 h-9 flex items-center justify-center text-base"
            onClick={() => setMuted(toggleMute())}
            title={muted ? 'Unmute sounds' : 'Mute sounds'}
          >
            {muted ? '\uD83D\uDD07' : '\uD83D\uDD0A'}
          </button>
          {onHowTo && (
            <button
              className="btn-ghost-sm touch-target hidden sm:inline-flex"
              onClick={onHowTo}
            >
              How to play
            </button>
          )}
          {onHowTo && (
            <button
              className="btn-ghost-sm touch-target sm:hidden w-9 h-9 flex items-center justify-center text-base"
              onClick={onHowTo}
              title="How to play"
            >
              &#128214;
            </button>
          )}

          {isAuthed ? (
            <>
              {userAvatarUrl && (
                <img
                  src={userAvatarUrl}
                  alt=""
                  className="w-7 h-7 rounded-full object-cover"
                  referrerPolicy="no-referrer"
                />
              )}
              <span className="text-slate/60 max-w-[140px] truncate text-xs sm:text-sm">{displayLabel}</span>
              <button className="btn-ghost-sm touch-target" onClick={onLogout}>Logout</button>
            </>
          ) : isGuest ? (
            <>
              <span className="badge bg-accent/10 text-accent text-xs">{guestDisplayName || 'Guest'}</span>
              <button className="btn-ghost-sm touch-target" onClick={onLogout}>Switch</button>
            </>
          ) : null}
        </div>
      </div>
    </div>
  )
}
