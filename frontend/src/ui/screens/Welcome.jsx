import Logo from '../components/Logo.jsx'

export default function Welcome({ onGuest, onSignIn, onHowTo }) {
  return (
    <div className="min-h-screen px-6 py-10 flex flex-col justify-between">
      <div className="space-y-10">
        <Logo />
        <div className="max-w-xl space-y-5">
          <h1 className="section-title">Bring words to life together.</h1>
          <p className="subtle text-lg">
            A refined, fast-paced charades room where every hint matters. Smooth lobbies,
            elegant gameplay, and a leaderboard that keeps the energy high.
          </p>
          <div className="hero-card animate-floaty glow-chip">
            <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Live Word</div>
            <div className="font-display text-3xl mt-2">Umbrella</div>
            <div className="text-sm text-slate/70 mt-2">Describe without saying it.</div>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 max-w-md">
          <button className="btn-primary" onClick={onGuest}>Play as Guest</button>
          <button className="btn-ghost" onClick={onSignIn}>Sign In</button>
        </div>
      </div>
      <button className="text-sm text-slate/70 underline" onClick={onHowTo}>How to play</button>
    </div>
  )
}
