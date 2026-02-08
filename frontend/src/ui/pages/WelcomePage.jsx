import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import Welcome from '../screens/Welcome.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function WelcomePage() {
  const navigate = useNavigate()
  const { ensureGuest, loginWithGoogle, ui } = useApp()

  const handleGoogleLogin = useCallback(async (idToken) => {
    await loginWithGoogle(idToken)
    navigate('/home')
  }, [loginWithGoogle, navigate])

  return (
    <Welcome
      onGuest={async (displayName) => {
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
