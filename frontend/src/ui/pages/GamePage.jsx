import { useEffect, useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import Game from '../screens/Game.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function GamePage() {
  const navigate = useNavigate()
  const { room, lobby, game, emitChat, emitRoomJoin, selfPlayerId, roomRestoreStatus } = useApp()
  const navigatedRef = useRef(false)

  useEffect(() => {
    if (roomRestoreStatus !== 'done') return
    if (!room?.code) {
      navigate('/home', { replace: true })
      return
    }
  }, [room, roomRestoreStatus])

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

  const playerNames = useMemo(() => {
    const map = {}
    for (const p of lobby?.players || []) {
      map[p.id] = p.display_name || `Player ${p.id}`
    }
    return map
  }, [lobby?.players])

  function handleSend(message) {
    if (!room?.code) return
    emitChat(room.code, message)
  }

  return (
    <Game
      game={{ ...game, selfPlayerId }}
      playerNames={playerNames}
      onSend={handleSend}
      onRejoin={() => {
        if (!room?.code) return
        emitRoomJoin(room.code)
      }}
    />
  )
}
