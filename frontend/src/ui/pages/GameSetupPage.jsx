import { useNavigate, useParams } from 'react-router-dom'
import GameSetup from '../screens/GameSetup.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function GameSetupPage() {
  const navigate = useNavigate()
  const { gameType } = useParams()
  const { createRoom, joinRoom, bindLobbyEvents, ui, auth } = useApp()
  const signedIn = !!auth?.user

  async function handleCreate(payload) {
    try {
      const res = await createRoom(payload)
      bindLobbyEvents(res.room.code)
      navigate('/lobby', { state: { fromJoin: true } })
    } catch {
      // errors surfaced via toast
    }
  }

  async function handleJoin(roomCode) {
    try {
      await joinRoom(roomCode)
      bindLobbyEvents(roomCode)
      navigate('/lobby', { state: { fromJoin: true } })
    } catch {
      // errors surfaced via toast
    }
  }

  return (
    <GameSetup
      gameType={gameType || 'charades'}
      onCreate={handleCreate}
      onJoin={handleJoin}
      onBack={() => navigate('/home')}
      loadingCreate={Boolean(ui?.loadingKeys?.create_room)}
      loadingJoin={Boolean(ui?.loadingKeys?.join_room)}
      signedIn={signedIn}
      onQuickPlay={() => navigate('/quickmatch')}
    />
  )
}
