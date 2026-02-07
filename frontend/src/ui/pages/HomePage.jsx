import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Home from '../screens/Home.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function HomePage() {
  const navigate = useNavigate()
  const { createRoom, joinRoom, bindLobbyEvents, ui, activeRooms, fetchActiveRooms, leaveActiveRoom } = useApp()

  useEffect(() => {
    fetchActiveRooms()
  }, [])

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

  async function handleRejoin(roomCode) {
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
      onRejoin={handleRejoin}
      onLeaveRoom={leaveActiveRoom}
      loadingCreate={Boolean(ui?.loadingKeys?.create_room)}
      loadingJoin={Boolean(ui?.loadingKeys?.join_room)}
      loadingLeave={Boolean(ui?.loadingKeys?.leave_room)}
      activeRooms={activeRooms}
    />
  )
}
