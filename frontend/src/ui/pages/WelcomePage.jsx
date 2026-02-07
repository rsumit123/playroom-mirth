import { useNavigate } from 'react-router-dom'
import Welcome from '../screens/Welcome.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function WelcomePage() {
  const navigate = useNavigate()
  const { ensureGuest } = useApp()

  return (
    <Welcome
      onGuest={async () => {
        await ensureGuest()
        navigate('/home')
      }}
      onSignIn={() => navigate('/auth')}
      onHowTo={() => navigate('/how-to')}
    />
  )
}
