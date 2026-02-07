import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import GameEnd from '../screens/GameEnd.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function GameEndPage() {
  const navigate = useNavigate()
  const { game, lobby, leaveRoom } = useApp()
  const playerNames = useMemo(() => {
    const map = {}
    for (const p of lobby?.players || []) {
      map[p.id] = p.display_name || `Player ${p.id}`
    }
    return map
  }, [lobby?.players])
  return <GameEnd scores={game?.scores || {}} playerNames={playerNames} onHome={() => { leaveRoom(); navigate('/home') }} />
}
