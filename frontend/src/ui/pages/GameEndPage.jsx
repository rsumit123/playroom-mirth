import { useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import GameEnd from '../screens/GameEnd.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function GameEndPage() {
  const navigate = useNavigate()
  const { game, lobby, room, leaveRoom, emitPlayAgain } = useApp()
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

  return (
    <GameEnd
      scores={game?.scores || {}}
      playerNames={playerNames}
      playAgain={game?.playAgain}
      onPlayAgain={() => emitPlayAgain(room?.code)}
      onHome={() => { leaveRoom(); navigate('/home') }}
    />
  )
}
