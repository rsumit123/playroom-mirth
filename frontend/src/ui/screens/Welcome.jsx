import Logo from '../components/Logo.jsx'
import Spinner from '../components/Spinner.jsx'

export default function Welcome({ onGuest, onSignIn, onHowTo, loadingGuest }) {
  return (
    <div className="min-h-screen page py-10 flex flex-col justify-between">
      <div className="page-inner space-y-10">
        <Logo />
        <div className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div className="space-y-6">
            <h1 className="section-title">Bring words to life together.</h1>
            <p className="subtle text-lg">
              A refined, fast-paced charades room where every hint matters. Smooth lobbies,
              elegant gameplay, and a leaderboard that keeps the energy high.
            </p>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="card p-4">
                <div className="text-xs uppercase tracking-[0.3em] text-slate/60">1</div>
                <div className="font-semibold">Describe</div>
                <div className="text-xs text-slate/60">Give clean, quick hints.</div>
              </div>
              <div className="card p-4">
                <div className="text-xs uppercase tracking-[0.3em] text-slate/60">2</div>
                <div className="font-semibold">Guess</div>
                <div className="text-xs text-slate/60">Race to the right word.</div>
              </div>
              <div className="card p-4">
                <div className="text-xs uppercase tracking-[0.3em] text-slate/60">3</div>
                <div className="font-semibold">Rotate</div>
                <div className="text-xs text-slate/60">Everyone gets a turn.</div>
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 max-w-md">
              <button className="btn-primary flex items-center justify-center gap-2" onClick={onGuest} disabled={loadingGuest}>
                {loadingGuest ? <Spinner size={18} /> : null}
                Play as Guest
              </button>
              <button className="btn-ghost" onClick={onSignIn}>Sign In</button>
            </div>
          </div>
          <div className="space-y-4">
            <div className="hero-card animate-floaty glow-chip">
              <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Live Word</div>
              <div className="font-display text-3xl mt-2">Umbrella</div>
              <div className="text-sm text-slate/70 mt-2">Describe without saying it.</div>
            </div>
            <div className="card p-5 space-y-2">
              <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Experience</div>
              <p className="text-sm text-slate/70">Mobile-first rooms, desktop-ready layouts, and a clean scoreboard view built for longer sessions.</p>
            </div>
          </div>
        </div>
      </div>
      <div className="page-inner">
        <button className="text-sm text-slate/70 underline" onClick={onHowTo}>How to play</button>
      </div>
    </div>
  )
}
