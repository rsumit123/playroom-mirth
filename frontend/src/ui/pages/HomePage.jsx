import { useNavigate } from 'react-router-dom'
import Home from '../screens/Home.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function HomePage() {
  const navigate = useNavigate()
  const { createRoom, joinRoom, bindLobbyEvents, ui } = useApp()

  async function handleCreate(payload) {
    try {
      const res = await createRoom(payload)
      bindLobbyEvents(res.room.code)
      navigate('/lobby')
    } catch {
      // errors surfaced via toast
    }
  }

  async function handleJoin(roomCode) {
    try {
      await joinRoom(roomCode)
      bindLobbyEvents(roomCode)
      navigate('/lobby')
    } catch {
      // errors surfaced via toast
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
