import { useEffect, useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import ScribbleGame from '../screens/ScribbleGame.jsx'
import { useApp } from '../../state/AppContext.jsx'
import { getSocket } from '../../lib/socket.js'

export default function ScribbleGamePage() {
  const navigate = useNavigate()
  const { room, lobby, game, emitChat, emitScribbleDraw, emitScribbleClear, emitScribbleUndo, emitRoomJoin, leaveRoom, selfPlayerId, roomRestoreStatus } = useApp()
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

  function handleStroke(stroke) {
    if (!room?.code) return
    emitScribbleDraw(room.code, stroke)
  }

  function handleClear() {
    if (!room?.code) return
    emitScribbleClear(room.code)
  }

  function handleUndo() {
    if (!room?.code) return
    emitScribbleUndo(room.code)
  }

  function handleLeave() {
    if (room?.code) {
      getSocket().emit('game:leave', { room_code: room.code })
    }
    leaveRoom()
    navigate('/home')
  }

  return (
    <ScribbleGame
      game={{ ...game, selfPlayerId }}
      playerNames={playerNames}
      onSend={handleSend}
      onStroke={handleStroke}
      onClear={handleClear}
      onUndo={handleUndo}
      onLeave={handleLeave}
      onRejoin={() => {
        if (!room?.code) return
        emitRoomJoin(room.code)
      }}
    />
  )
}
