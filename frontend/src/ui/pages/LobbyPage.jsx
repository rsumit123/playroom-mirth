import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Lobby from '../screens/Lobby.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function LobbyPage() {
  const navigate = useNavigate()
  const { lobby, game, emitGameStart, startGameSocket, saveRoomSettings, selfPlayerId, ui } = useApp()

  useEffect(() => {
    if (game?.turn) {
      startGameSocket()
      navigate('/game')
    }
  }, [game?.turn])

  async function handleStart() {
    if (!lobby?.room?.code) return
    startGameSocket()
    emitGameStart(lobby.room.code)
    navigate('/game')
  }

  return (
    <Lobby
      lobby={lobby}
      onStart={handleStart}
      onLeave={() => navigate('/home')}
      onSaveSettings={(payload) => {
        if (!lobby?.room?.code) return
        saveRoomSettings(lobby.room.code, payload)
      }}
      loadingSave={Boolean(ui?.loadingKeys?.save_settings)}
      selfPlayerId={selfPlayerId}
    />
  )
}
