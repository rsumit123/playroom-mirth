import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Home from '../screens/Home.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function HomePage() {
  const navigate = useNavigate()
  const { joinRoom, bindLobbyEvents, ui, activeRooms, fetchActiveRooms, leaveActiveRoom, auth } = useApp()

  useEffect(() => {
    fetchActiveRooms()
  }, [])

  function handleSelectGame(gameType) {
    navigate(`/play/${gameType}`)
  }

  async function handleRejoin(roomCode) {
    try {
      await joinRoom(roomCode)
      bindLobbyEvents(roomCode)
      navigate('/lobby', { state: { fromJoin: true } })
    } catch {
      // errors surfaced via toast
    }
  }

  return (
    <Home
      onSelectGame={handleSelectGame}
      onRejoin={handleRejoin}
      onLeaveRoom={leaveActiveRoom}
      loadingLeave={Boolean(ui?.loadingKeys?.leave_room)}
      activeRooms={activeRooms}
      isSignedIn={Boolean(auth?.token)}
    />
  )
}
