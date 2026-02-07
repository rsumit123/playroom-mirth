import Logo from './Logo.jsx'

export default function TopBar({ userEmail, isAuthed, onLogin, onLogout, onProfile, onHome, onHowTo }) {
  return (
    <div className="w-full border-b border-black/5 bg-white/70 backdrop-blur">
      <div className="page-inner py-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center justify-between gap-3">
          <Logo compact onClick={onHome} />
          {onHowTo && (
            <button className="text-xs uppercase tracking-[0.3em] text-slate/60 sm:hidden" onClick={onHowTo}>
              How to play
            </button>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2 text-sm sm:justify-end">
          {onHowTo && (
            <button className="hidden sm:inline-flex text-xs uppercase tracking-[0.3em] text-slate/60" onClick={onHowTo}>
              How to play
            </button>
          )}
          {isAuthed ? (
            <>
              <span className="text-slate/60 max-w-[140px] truncate">{userEmail || 'Signed in'}</span>
              <button className="btn-ghost-sm" onClick={onProfile}>Profile</button>
              <button className="btn-ghost-sm" onClick={onLogout}>Logout</button>
            </>
          ) : (
            <button className="btn-ghost-sm" onClick={onLogin}>Login</button>
          )}
        </div>
      </div>
    </div>
  )
}
