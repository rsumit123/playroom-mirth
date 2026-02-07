import { useNavigate } from 'react-router-dom'
import Auth from '../screens/Auth.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function AuthPage() {
  const navigate = useNavigate()
  const { login, register } = useApp()

  async function handleDone(mode, email, password) {
    if (mode === 'signin') await login(email, password)
    if (mode === 'register') await register(email, password)
    navigate('/home')
  }

  return <Auth onBack={() => navigate('/')} onDone={handleDone} />
}
