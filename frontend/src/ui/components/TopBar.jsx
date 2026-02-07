import Logo from './Logo.jsx'

export default function TopBar({ userEmail, isAuthed, onLogin, onLogout, onHome, onHowTo }) {
  return (
    <div className="sticky top-0 z-20 w-full border-b border-black/5 bg-white/70 backdrop-blur">
      <div className="page-medium py-3 flex items-center justify-between">
        <Logo compact onClick={onHome} />

        <div className="flex items-center gap-2 text-sm">
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
              ?
            </button>
          )}

          {isAuthed ? (
            <>
              <span className="text-slate/60 max-w-[120px] truncate hidden sm:inline">{userEmail || 'Signed in'}</span>
              <button className="btn-ghost-sm touch-target" onClick={onLogout}>Logout</button>
            </>
          ) : (
            <button className="btn-ghost-sm touch-target" onClick={onLogin}>Login</button>
          )}
        </div>
      </div>
    </div>
  )
}
