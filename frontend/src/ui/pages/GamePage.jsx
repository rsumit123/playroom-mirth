import { useNavigate } from 'react-router-dom'
import Game from '../screens/Game.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function GamePage() {
  const navigate = useNavigate()
  const { room, game, emitChat, emitRoomJoin, selfPlayerId } = useApp()

  function handleSend(message) {
    if (!room?.code) return
    emitChat(room.code, message)
  }

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
    </>
  )
}
