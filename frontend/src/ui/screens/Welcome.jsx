import { useState, useEffect, useRef } from 'react'
import { Capacitor } from '@capacitor/core'
import Logo from '../components/Logo.jsx'
import Spinner from '../components/Spinner.jsx'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID
const isNative = Capacitor.isNativePlatform()

export default function Welcome({ onGuest, onGoogleLogin, onHowTo, loadingGuest, loadingGoogle }) {
  const [name, setName] = useState('')
  const [nativeGoogleReady, setNativeGoogleReady] = useState(false)
  const googleBtnRef = useRef(null)

  // Native Google Sign-In (Capacitor)
  useEffect(() => {
    if (!isNative || !GOOGLE_CLIENT_ID) return
    import('@codetrix-studio/capacitor-google-auth').then(({ GoogleAuth }) => {
      GoogleAuth.initialize({
        clientId: GOOGLE_CLIENT_ID,
        scopes: ['profile', 'email'],
        grantOfflineAccess: false,
      })
      setNativeGoogleReady(true)
    })
  }, [])

  // Web Google Sign-In (GIS script)
  useEffect(() => {
    if (isNative || !GOOGLE_CLIENT_ID) return

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

    if (tryRenderButton()) return
    const interval = setInterval(() => {
      if (tryRenderButton()) clearInterval(interval)
    }, 200)
    return () => clearInterval(interval)
  }, [onGoogleLogin])

  const handleNativeGoogleSignIn = async () => {
    try {
      const { GoogleAuth } = await import('@codetrix-studio/capacitor-google-auth')
      const user = await GoogleAuth.signIn()
      if (user?.authentication?.idToken) {
        onGoogleLogin?.(user.authentication.idToken)
      }
    } catch (err) {
      console.error('Google Sign-In error:', err)
    }
  }

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
          {isNative ? (
            nativeGoogleReady && (
              <button
                className="w-full flex items-center justify-center gap-3 rounded-xl border border-black/10 bg-white px-4 py-3 text-sm font-medium text-slate shadow-sm hover:bg-gray-50 transition touch-target disabled:opacity-40"
                onClick={handleNativeGoogleSignIn}
                disabled={loadingGoogle}
              >
                {loadingGoogle ? <Spinner size={18} /> : (
                  <svg width="18" height="18" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>
                )}
                Continue with Google
              </button>
            )
          ) : (
            <div className="flex justify-center">
              <div ref={googleBtnRef} data-testid="google-signin-btn" />
            </div>
          )}
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
