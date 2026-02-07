import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Game from '../screens/Game.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function GamePage() {
  const navigate = useNavigate()
  const { room, game, emitChat, emitRoomJoin, selfPlayerId } = useApp()
  const navigatedRef = useRef(false)

  useEffect(() => {
    if (!room?.code) {
      navigate('/home', { replace: true })
      return
    }
  }, [room])

  useEffect(() => {
    if (game?.gameEnd && !navigatedRef.current) {
      navigatedRef.current = true
      navigate('/game-end')
    }
  }, [game?.gameEnd])

  useEffect(() => {
    if (game?.roundEnd && !game?.gameEnd && !navigatedRef.current) {
      navigatedRef.current = true
      navigate('/round-end')
    }
  }, [game?.roundEnd])

  function handleSend(message) {
    if (!room?.code) return
    emitChat(room.code, message)
  }

  return (
    <Game
      game={{ ...game, selfPlayerId }}
      onSend={handleSend}
      onRejoin={() => {
        if (!room?.code) return
        emitRoomJoin(room.code)
      }}
    />
  )
}
