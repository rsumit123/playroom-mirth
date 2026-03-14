import { useEffect, useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import TriviaGame from '../screens/TriviaGame.jsx'
import { useApp } from '../../state/AppContext.jsx'
import { getSocket } from '../../lib/socket.js'

export default function TriviaGamePage() {
  const navigate = useNavigate()
  const { room, lobby, game, emitTriviaAnswer, leaveRoom, selfPlayerId, roomRestoreStatus } = useApp()
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

  function handleAnswer(answerIndex) {
    if (!room?.code) return
    emitTriviaAnswer(room.code, answerIndex)
  }

  function handleLeave() {
    if (room?.code) {
      getSocket().emit('game:leave', { room_code: room.code })
    }
    leaveRoom()
    navigate('/home')
  }

  return (
    <TriviaGame
      game={{ ...game, selfPlayerId }}
      playerNames={playerNames}
      onAnswer={handleAnswer}
      onLeave={handleLeave}
    />
  )
}
