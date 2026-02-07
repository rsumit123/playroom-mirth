import Logo from './Logo.jsx'

export default function TopBar({ userEmail, isAuthed, onLogin, onLogout, onProfile }) {
  return (
    <div className="w-full px-6 py-4 flex items-center justify-between border-b border-black/5 bg-white/70 backdrop-blur">
      <Logo />
      <div className="flex items-center gap-3 text-sm">
        {isAuthed ? (
          <>
            <span className="text-slate/60 max-w-[120px] truncate">{userEmail || 'Signed in'}</span>
            <button className="btn-ghost" onClick={onProfile}>Profile</button>
            <button className="btn-ghost" onClick={onLogout}>Logout</button>
          </>
        ) : (
          <button className="btn-ghost" onClick={onLogin}>Login</button>
        )}
      </div>
    </div>
  )
}
