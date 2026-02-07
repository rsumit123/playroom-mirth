import { useNavigate } from 'react-router-dom'
import Home from '../screens/Home.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function HomePage() {
  const navigate = useNavigate()
  const { createRoom, joinRoom, bindLobbyEvents, ui } = useApp()

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

  return (
    <Home
      onCreate={handleCreate}
      onJoin={handleJoin}
      loadingCreate={Boolean(ui?.loadingKeys?.create_room)}
      loadingJoin={Boolean(ui?.loadingKeys?.join_room)}
    />
  )
}
