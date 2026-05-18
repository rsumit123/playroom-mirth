import { useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import GameEnd from '../screens/GameEnd.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function GameEndPage() {
  const navigate = useNavigate()
  const { game, lobby, room, leaveRoom, emitPlayAgain, quickmatch, quickmatchJoin, selfPlayerId } = useApp()
  const playerNames = useMemo(() => {
    const map = {}
    for (const p of lobby?.players || []) {
      map[p.id] = p.display_name || `Player ${p.id}`
    }
    return map
  }, [lobby?.players])

  // When all players agree, navigate to lobby
  useEffect(() => {
    if (game?.playAgain?.ready) {
      navigate('/lobby')
    }
  }, [game?.playAgain?.ready])

  const origin = quickmatch.roomCode && quickmatch.roomCode === room?.code ? 'quickmatch' : 'friends'
  const winnerPlayerId = game?.gameEnd?.winner_player_id ?? null
  const lastCategory = quickmatch.category || 'surprise'

  return (
    <GameEnd
      scores={game?.scores || {}}
      playerNames={playerNames}
      playAgain={game?.playAgain}
      onPlayAgain={() => emitPlayAgain(room?.code)}
      onHome={() => { leaveRoom(); navigate('/home') }}
      selfPlayerId={selfPlayerId}
      winnerPlayerId={winnerPlayerId}
      origin={origin}
      onRematch={() => { leaveRoom(); quickmatchJoin(lastCategory); navigate('/quickmatch') }}
      onNewOpponent={() => { leaveRoom(); navigate('/quickmatch') }}
    />
  )
}
