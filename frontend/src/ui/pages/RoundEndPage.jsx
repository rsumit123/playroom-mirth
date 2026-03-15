import { useEffect, useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import RoundEnd from '../screens/RoundEnd.jsx'
import { useApp } from '../../state/AppContext.jsx'
import { getSocket } from '../../lib/socket.js'

export default function RoundEndPage() {
  const navigate = useNavigate()
  const { game, room, lobby, selfPlayerId, leaveRoom, roomRestoreStatus, emitNextRound } = useApp()
  const turnRef = useRef(game?.turn)

  useEffect(() => {
    if (roomRestoreStatus !== 'done') return
    if (!room?.code) {
      navigate('/home', { replace: true })
      return
    }
  }, [room, roomRestoreStatus])

  // Auto-navigate to game when new turn starts
  useEffect(() => {
    if (game?.turn && game.turn !== turnRef.current) {
      turnRef.current = game.turn
      const gameType = game.turn.game_type || room?.game_type || 'charades'
      navigate(gameType === 'scribble' ? '/scribble' : gameType === 'trivia' ? '/trivia' : '/game')
    }
  }, [game?.turn])

  const playerNames = useMemo(() => {
    const map = {}
    for (const p of lobby?.players || []) {
      map[p.id] = p.display_name || `Player ${p.id}`
    }
    return map
  }, [lobby?.players])

  const isHost = selfPlayerId && lobby?.host_player_id && String(selfPlayerId) === String(lobby.host_player_id)

  function handleNextRound() {
    if (room?.code) emitNextRound(room.code)
  }

  function handleLeave() {
    if (room?.code) {
      getSocket().emit('game:leave', { room_code: room.code })
    }
    leaveRoom()
    navigate('/home')
  }

  return (
    <RoundEnd
      scores={game?.scores || {}}
      playerNames={playerNames}
      isHost={isHost}
      onContinue={handleNextRound}
      onLeave={handleLeave}
    />
  )
}
