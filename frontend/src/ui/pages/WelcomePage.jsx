import { useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Welcome from '../screens/Welcome.jsx'
import { useApp } from '../../state/AppContext.jsx'
import { initAudio } from '../../lib/sounds.js'

export default function WelcomePage() {
  const navigate = useNavigate()
  const { auth, ensureGuest, loginWithGoogle, ui } = useApp()

  // Already authenticated — skip welcome screen
  useEffect(() => {
    if (auth.token || auth.guestToken) {
      navigate('/home', { replace: true })
    }
  }, [auth.token, auth.guestToken])

  const handleGoogleLogin = useCallback(async (idToken) => {
    initAudio()
    await loginWithGoogle(idToken)
    navigate('/home')
  }, [loginWithGoogle, navigate])

  return (
    <Welcome
      onGuest={async (displayName) => {
        initAudio()
        await ensureGuest(displayName)
        navigate('/home')
      }}
      onGoogleLogin={handleGoogleLogin}
      onHowTo={() => navigate('/how-to')}
      loadingGuest={Boolean(ui?.loadingKeys?.guest)}
      loadingGoogle={Boolean(ui?.loadingKeys?.login)}
    />
  )
}
