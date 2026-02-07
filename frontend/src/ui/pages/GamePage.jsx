import { useNavigate } from 'react-router-dom'
import Game from '../screens/Game.jsx'
import { useApp } from '../../state/AppContext.jsx'
import Toast from '../components/Toast.jsx'
import { useEffect, useState } from 'react'

export default function GamePage() {
  const navigate = useNavigate()
  const { room, game, emitChat, emitRoomJoin, selfPlayerId } = useApp()
  const [toast, setToast] = useState(null)

  function handleSend(message) {
    if (!room?.code) return
    emitChat(room.code, message)
  }

  useEffect(() => {
    if (game?.error?.message) {
      setToast(game.error.message)
    }
  }, [game?.error])

  return (
    <>
      <Game
        game={{ ...game, selfPlayerId }}
        onSend={handleSend}
        onRoundEnd={() => navigate('/round-end')}
        onGameEnd={() => navigate('/game-end')}
        onRejoin={() => {
          if (!room?.code) return
          emitRoomJoin(room.code)
        }}
      />
      <Toast message={toast} onClose={() => setToast(null)} />
    </>
  )
}
