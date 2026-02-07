import { useState } from 'react'
import Logo from '../components/Logo.jsx'
import Spinner from '../components/Spinner.jsx'

export default function Auth({ onBack, onDone, loading }) {
  const [mode, setMode] = useState('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const isLoading = Boolean(loading)

  return (
    <div className="min-h-screen page py-10">
      <div className="page-inner flex items-center justify-between">
        <Logo />
        <button className="text-sm text-slate/70" onClick={onBack}>Back</button>
      </div>

      <div className="page-inner mt-10 grid gap-8 lg:grid-cols-[1fr_1fr]">
        <div className="card p-6">
          <div className="flex gap-3 mb-6">
            <button className={`px-4 py-2 rounded-full ${mode === 'signin' ? 'bg-ink text-white' : 'bg-mist text-slate'}`} onClick={() => setMode('signin')}>
              Sign In
            </button>
            <button className={`px-4 py-2 rounded-full ${mode === 'register' ? 'bg-ink text-white' : 'bg-mist text-slate'}`} onClick={() => setMode('register')}>
              Register
            </button>
          </div>
          <div className="space-y-4">
            <input
              className="w-full rounded-xl border border-black/10 px-4 py-3"
              placeholder="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <div className="space-y-1">
              <input
                className="w-full rounded-xl border border-black/10 px-4 py-3"
                placeholder="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <div className="text-xs text-slate/60">Use at least 6 characters.</div>
            </div>
          </div>
          <button className="btn-primary mt-6 w-full flex items-center justify-center gap-2" onClick={() => onDone(mode, email, password)} disabled={isLoading}>
            {isLoading ? <Spinner size={18} /> : null}
            {mode === 'signin' ? 'Sign In' : 'Create Account'}
          </button>
        </div>
        <div className="card p-6 space-y-4">
          <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Account Benefits</div>
          <h2 className="font-display text-2xl">Track your wins across rooms.</h2>
          <p className="text-sm text-slate/70">
            Signed in players can rejoin mid-round, keep score history, and host multiple rooms with capped concurrency.
          </p>
          <div className="card p-4 bg-white/60 border border-black/5">
            <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Guest mode</div>
            <p className="text-sm text-slate/70">Guests can play one full match before signing in.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
