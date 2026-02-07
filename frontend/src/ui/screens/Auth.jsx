import { useState } from 'react'
import Logo from '../components/Logo.jsx'
import Spinner from '../components/Spinner.jsx'

export default function Auth({ onBack, onDone, loading }) {
  const [mode, setMode] = useState('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const isLoading = Boolean(loading)

  return (
    <div className="game-shell">
      <div className="page-narrow py-4 flex items-center justify-between">
        <button className="btn-ghost-sm touch-target" onClick={onBack}>&larr; Back</button>
      </div>

      <div className="flex-1 flex items-center justify-center page-narrow pb-10">
        <div className="card p-6 w-full max-w-sm animate-pop">
          <div className="flex justify-center mb-6">
            <Logo compact />
          </div>

          <div className="segmented mb-6">
            <button
              className={mode === 'signin' ? 'segmented-option-active' : 'segmented-option'}
              onClick={() => setMode('signin')}
            >
              Sign In
            </button>
            <button
              className={mode === 'register' ? 'segmented-option-active' : 'segmented-option'}
              onClick={() => setMode('register')}
            >
              Register
            </button>
          </div>

          <div className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate/70">Email</label>
              <input
                className="w-full rounded-xl border border-black/10 px-4 py-3 text-sm touch-target outline-none focus:border-accent transition"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate/70">Password</label>
              <input
                className="w-full rounded-xl border border-black/10 px-4 py-3 text-sm touch-target outline-none focus:border-accent transition"
                type="password"
                placeholder="6+ characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') onDone(mode, email, password)
                }}
              />
              {mode === 'register' && (
                <p className="text-xs text-slate/50 mt-1">Use at least 6 characters</p>
              )}
            </div>
          </div>

          <button
            className="btn-primary mt-6 w-full py-3 touch-target flex items-center justify-center gap-2"
            onClick={() => onDone(mode, email, password)}
            disabled={isLoading}
          >
            {isLoading ? <Spinner size={18} /> : null}
            {mode === 'signin' ? 'Sign In' : 'Create Account'}
          </button>
        </div>
      </div>
    </div>
  )
}
