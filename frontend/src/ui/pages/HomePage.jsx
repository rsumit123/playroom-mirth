import { useNavigate } from 'react-router-dom'
import Home from '../screens/Home.jsx'
import { useApp } from '../../state/AppContext.jsx'
import Toast from '../components/Toast.jsx'
import { useEffect, useState } from 'react'

export default function HomePage() {
  const navigate = useNavigate()
  const { createRoom, joinRoom, bindLobbyEvents, game } = useApp()
  const [toast, setToast] = useState(null)

  async function handleCreate(payload) {
    try {
      await createRoom(payload)
      bindLobbyEvents()
      navigate('/lobby')
    } catch {
      // errors surfaced via toast in GamePage or future global toast
    }
  }

  async function handleJoin(roomCode) {
    try {
      await joinRoom(roomCode)
      bindLobbyEvents()
      navigate('/lobby')
    } catch {
      // errors surfaced via toast in GamePage or future global toast
    }
  }

  useEffect(() => {
    if (game?.error?.message) setToast(game.error.message)
  }, [game?.error])

  return (
    <>
      <Home onCreate={handleCreate} onJoin={handleJoin} />
      <Toast message={toast} onClose={() => setToast(null)} />
    </>
  )
}
