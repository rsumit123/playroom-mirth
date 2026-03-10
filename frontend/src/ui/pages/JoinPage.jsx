import { useEffect, useRef, useCallback, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useApp } from '../../state/AppContext.jsx'
import Welcome from '../screens/Welcome.jsx'
import Spinner from '../components/Spinner.jsx'
import { initAudio } from '../../lib/sounds.js'

export default function JoinPage() {
  const { roomCode } = useParams()
  const navigate = useNavigate()
  const { auth, joinRoom, bindLobbyEvents, ensureGuest, loginWithGoogle, ui } = useApp()
  const [joining, setJoining] = useState(false)
  const [error, setError] = useState(null)
  const joinAttempted = useRef(false)

  const normalizedCode = roomCode?.toUpperCase()

  async function doJoin() {
    setJoining(true)
    setError(null)
    try {
      await joinRoom(normalizedCode)
      bindLobbyEvents(normalizedCode)
      navigate('/lobby', { replace: true })
    } catch (err) {
      setError(err?.message || 'Could not join room')
      setJoining(false)
    }
  }

  // Auto-join if already authenticated
  useEffect(() => {
    if (joinAttempted.current) return
    if (!(auth.token || auth.guestToken)) return
    joinAttempted.current = true
    doJoin()
  }, [auth.token, auth.guestToken])

  const handleGoogleLogin = useCallback(async (idToken) => {
    initAudio()
    try {
      await loginWithGoogle(idToken)
      // Don't call doJoin here — auth state update is async (setAuth batched).
      // The useEffect watching [auth.token, auth.guestToken] will fire on
      // re-render with the fresh joinRoom closure that has the new token.
    } catch {
      // errors surfaced via toast in AppContext
    }
  }, [loginWithGoogle])

  async function handleGuest(displayName) {
    initAudio()
    try {
      await ensureGuest(displayName)
      // Same as above — let the useEffect handle the join after re-render
      // so joinRoom() reads the updated auth.guestToken.
    } catch {
      // errors surfaced via toast in AppContext
    }
  }

  // Authenticated and joining / already attempted
  if (joining || (auth.token || auth.guestToken)) {
    return (
      <div className="game-shell">
        <div className="flex-1 flex flex-col items-center justify-center text-center px-4">
          {error ? (
            <div className="space-y-4">
              <div className="text-lg font-semibold text-danger">{error}</div>
              <p className="text-sm text-slate/60">Room code: {normalizedCode}</p>
              <button className="btn-primary px-6 py-3 touch-target" onClick={() => navigate('/home')}>
                Go Home
              </button>
            </div>
          ) : (
            <>
              <Spinner size={32} />
              <div className="mt-4 text-sm text-slate/60">
                Joining room <span className="font-display tracking-wider">{normalizedCode}</span>...
              </div>
            </>
          )}
        </div>
      </div>
    )
  }

  // Not authenticated — show Welcome screen with invite banner
  return (
    <div>
      <div className="bg-accent/5 border-b border-accent/10 px-4 py-3 text-center">
        <span className="text-sm text-accent font-medium">
          You&rsquo;ve been invited to join room{' '}
          <span className="font-display tracking-wider">{normalizedCode}</span>
        </span>
      </div>
      <Welcome
        onGuest={handleGuest}
        onGoogleLogin={handleGoogleLogin}
        onHowTo={() => navigate('/how-to')}
        loadingGuest={Boolean(ui?.loadingKeys?.guest)}
        loadingGoogle={Boolean(ui?.loadingKeys?.login)}
      />
    </div>
  )
}
