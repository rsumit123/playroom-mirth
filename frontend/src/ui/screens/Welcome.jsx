import { useState, useEffect, useRef } from 'react'
import Logo from '../components/Logo.jsx'
import Spinner from '../components/Spinner.jsx'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID

export default function Welcome({ onGuest, onGoogleLogin, onHowTo, loadingGuest, loadingGoogle }) {
  const [name, setName] = useState('')
  const googleBtnRef = useRef(null)

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return

    function tryRenderButton() {
      if (!window.google?.accounts?.id) return false
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: (response) => {
          if (response.credential) {
            onGoogleLogin?.(response.credential)
          }
        },
      })
      if (googleBtnRef.current) {
        window.google.accounts.id.renderButton(googleBtnRef.current, {
          type: 'standard',
          theme: 'outline',
          size: 'large',
          width: 320,
          text: 'continue_with',
        })
      }
      return true
    }

    // SDK may not be loaded yet (async defer script) — poll until available
    if (tryRenderButton()) return
    const interval = setInterval(() => {
      if (tryRenderButton()) clearInterval(interval)
    }, 200)
    return () => clearInterval(interval)
  }, [onGoogleLogin])

  return (
    <div className="game-shell">
      <div className="flex-1 flex flex-col items-center justify-center page-narrow py-8 text-center">
        <div className="mb-8">
          <Logo />
        </div>

        <h1 className="font-display text-4xl sm:text-5xl mb-3">
          Play. Laugh. <span className="text-accent">Win.</span>
        </h1>
        <p className="text-slate/60 text-base mb-8 max-w-sm">
          Multiplayer party games — play with friends in seconds.
        </p>

        <div className="flex items-center gap-3 mb-10 text-sm flex-wrap justify-center">
          <span className="badge bg-accent/10 text-accent">Charades</span>
          <span className="text-slate/30">&middot;</span>
          <span className="badge bg-accent/10 text-accent">Scribble</span>
          <span className="text-slate/30">&middot;</span>
          <span className="badge bg-accent/10 text-accent">Trivia</span>
        </div>

        <div className="w-full space-y-4 max-w-xs">
          {/* Google Sign-In button */}
          <div className="flex justify-center">
            <div ref={googleBtnRef} data-testid="google-signin-btn" />
          </div>
          {loadingGoogle && (
            <div className="flex justify-center">
              <Spinner size={20} />
            </div>
          )}

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-black/10" />
            <span className="text-xs text-slate/40 uppercase tracking-wider">or</span>
            <div className="flex-1 h-px bg-black/10" />
          </div>

          {/* Guest play */}
          <input
            className="w-full rounded-xl border border-black/10 px-4 py-3 text-sm text-center touch-target outline-none focus:border-accent transition"
            placeholder="Enter your name"
            maxLength={30}
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && name.trim()) onGuest(name.trim())
            }}
          />
          <button
            className="btn-ghost w-full py-3 touch-target flex items-center justify-center gap-2 border border-black/10 rounded-xl disabled:opacity-40"
            onClick={() => onGuest(name.trim())}
            disabled={loadingGuest || !name.trim()}
          >
            {loadingGuest ? <Spinner size={18} /> : null}
            Play as Guest
          </button>
          <p className="text-[11px] text-slate/40 leading-tight">
            Guest progress is not saved across devices. Sign in with Google for a persistent account.
          </p>
        </div>
      </div>

      <div className="page-narrow pb-6 text-center">
        <button className="text-sm text-accent font-medium underline underline-offset-4" onClick={onHowTo}>
          How to Play
        </button>
      </div>
    </div>
  )
}
