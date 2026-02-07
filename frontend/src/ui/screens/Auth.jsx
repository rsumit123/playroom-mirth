import { useState } from 'react'
import Logo from '../components/Logo.jsx'

export default function Auth({ onBack, onDone }) {
  const [mode, setMode] = useState('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  return (
    <div className="min-h-screen px-6 py-10">
      <div className="flex items-center justify-between">
        <Logo />
        <button className="text-sm text-slate/70" onClick={onBack}>Back</button>
      </div>

      <div className="mt-10 max-w-lg card p-6">
        <div className="flex gap-3 mb-6">
          <button className={`px-4 py-2 rounded-full ${mode === 'signin' ? 'bg-ink text-white' : 'bg-mist text-slate'}`} onClick={() => setMode('signin')}>
            Sign In
          </button>
          <button className={`px-4 py-2 rounded-full ${mode === 'register' ? 'bg-ink text-white' : 'bg-mist text-slate'}`} onClick={() => setMode('register')}>
            Register
          </button>
        </div>
        <div className="space-y-4">
          <input className="w-full rounded-xl border border-black/10 px-4 py-3" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="w-full rounded-xl border border-black/10 px-4 py-3" placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button className="btn-primary mt-6 w-full" onClick={() => onDone(mode, email, password)}>
          {mode === 'signin' ? 'Sign In' : 'Create Account'}
        </button>
      </div>
    </div>
  )
}
