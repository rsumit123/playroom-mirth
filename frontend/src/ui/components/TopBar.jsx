import { useState, useRef, useEffect } from 'react'
import Logo from './Logo.jsx'
import { toggleMute, isMuted } from '../../lib/sounds.js'

export default function TopBar({ userEmail, userDisplayName, userAvatarUrl, isAuthed, isGuest, guestDisplayName, onLogout, onHome, onHowTo, onHistory, notificationCount = 0, onNotifications }) {
  const displayLabel = userDisplayName || userEmail || 'Signed in'
  const [muted, setMuted] = useState(isMuted())
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  // Close menu on outside click
  useEffect(() => {
    if (!menuOpen) return
    function handleClick(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false)
    }
    document.addEventListener('pointerdown', handleClick)
    return () => document.removeEventListener('pointerdown', handleClick)
  }, [menuOpen])

  return (
    <div className="sticky top-0 z-20 w-full border-b border-black/5 bg-white/70 backdrop-blur">
      <div className="page-medium py-3 flex items-center justify-between">
        <Logo compact onClick={onHome} />

        <div className="flex items-center gap-2 text-sm">
          {/* Desktop: show all controls inline */}
          <button
            className="btn-ghost-sm touch-target w-9 h-9 items-center justify-center text-base hidden sm:flex"
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

          {/* Notification bell -- visible on both mobile and desktop */}
          {isAuthed && onNotifications && (
            <button
              className="btn-ghost-sm touch-target w-9 h-9 flex items-center justify-center text-base relative"
              onClick={onNotifications}
              title="Notifications"
            >
              &#128276;
              {notificationCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] rounded-full bg-danger text-white text-[10px] font-bold flex items-center justify-center px-1">
                  {notificationCount > 9 ? '9+' : notificationCount}
                </span>
              )}
            </button>
          )}

          {/* User avatar / profile menu */}
          {isAuthed ? (
            <div className="relative" ref={menuRef}>
              <button
                className="flex items-center gap-1.5 touch-target rounded-lg px-1.5 py-1 hover:bg-black/5 transition"
                onClick={() => setMenuOpen(!menuOpen)}
              >
                {userAvatarUrl ? (
                  <img src={userAvatarUrl} alt="" className="w-7 h-7 rounded-full object-cover" referrerPolicy="no-referrer" />
                ) : (
                  <div className="w-7 h-7 rounded-full bg-accent/10 flex items-center justify-center text-xs font-bold text-accent">
                    {(displayLabel || '?')[0].toUpperCase()}
                  </div>
                )}
                <span className="text-slate/60 max-w-[100px] truncate text-xs hidden sm:inline">{displayLabel}</span>
                <svg className="w-3 h-3 text-slate/40" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 5l3 3 3-3"/></svg>
              </button>

              {menuOpen && (
                <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-xl shadow-lg border border-black/10 py-1 z-50 animate-pop">
                  <div className="px-3 py-2 border-b border-black/5">
                    <div className="font-medium text-sm truncate">{displayLabel}</div>
                    {userEmail && <div className="text-xs text-slate/40 truncate">{userEmail}</div>}
                  </div>
                  <button
                    className="w-full px-3 py-2.5 text-left text-sm hover:bg-black/5 flex items-center gap-2 sm:hidden"
                    onClick={() => { setMuted(toggleMute()); setMenuOpen(false) }}
                  >
                    <span className="text-base">{muted ? '\uD83D\uDD07' : '\uD83D\uDD0A'}</span>
                    {muted ? 'Unmute sounds' : 'Mute sounds'}
                  </button>
                  {onHowTo && (
                    <button
                      className="w-full px-3 py-2.5 text-left text-sm hover:bg-black/5 flex items-center gap-2 sm:hidden"
                      onClick={() => { onHowTo(); setMenuOpen(false) }}
                    >
                      <span className="text-base">&#128214;</span>
                      How to play
                    </button>
                  )}
                  {onHistory && (
                    <button
                      className="w-full px-3 py-2.5 text-left text-sm hover:bg-black/5 flex items-center gap-2"
                      onClick={() => { onHistory(); setMenuOpen(false) }}
                    >
                      <span className="text-base">&#128202;</span>
                      Game history
                    </button>
                  )}
                  <button
                    className="w-full px-3 py-2.5 text-left text-sm hover:bg-black/5 flex items-center gap-2 text-danger/70"
                    onClick={() => { onLogout(); setMenuOpen(false) }}
                  >
                    <span className="text-base">&#128682;</span>
                    Logout
                  </button>
                </div>
              )}
            </div>
          ) : isGuest ? (
            <div className="relative" ref={menuRef}>
              <button
                className="flex items-center gap-1.5 touch-target rounded-lg px-1.5 py-1 hover:bg-black/5 transition"
                onClick={() => setMenuOpen(!menuOpen)}
              >
                <span className="badge bg-accent/10 text-accent text-xs">{guestDisplayName || 'Guest'}</span>
                <svg className="w-3 h-3 text-slate/40" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 5l3 3 3-3"/></svg>
              </button>

              {menuOpen && (
                <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-xl shadow-lg border border-black/10 py-1 z-50 animate-pop">
                  <button
                    className="w-full px-3 py-2.5 text-left text-sm hover:bg-black/5 flex items-center gap-2 sm:hidden"
                    onClick={() => { setMuted(toggleMute()); setMenuOpen(false) }}
                  >
                    <span className="text-base">{muted ? '\uD83D\uDD07' : '\uD83D\uDD0A'}</span>
                    {muted ? 'Unmute sounds' : 'Mute sounds'}
                  </button>
                  {onHowTo && (
                    <button
                      className="w-full px-3 py-2.5 text-left text-sm hover:bg-black/5 flex items-center gap-2 sm:hidden"
                      onClick={() => { onHowTo(); setMenuOpen(false) }}
                    >
                      <span className="text-base">&#128214;</span>
                      How to play
                    </button>
                  )}
                  <button
                    className="w-full px-3 py-2.5 text-left text-sm hover:bg-black/5 flex items-center gap-2"
                    onClick={() => { onLogout(); setMenuOpen(false) }}
                  >
                    <span className="text-base">&#128260;</span>
                    Sign in with Google
                  </button>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
