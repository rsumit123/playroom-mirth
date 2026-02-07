import { useEffect, useMemo, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import RoundEnd from '../screens/RoundEnd.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function RoundEndPage() {
  const navigate = useNavigate()
  const { game, room, lobby, roomRestoreStatus } = useApp()
  const turnRef = useRef(game?.turn)

  useEffect(() => {
    if (roomRestoreStatus !== 'done') return
    if (!room?.code) {
      navigate('/home', { replace: true })
      return
    }
  }, [room, roomRestoreStatus])

  useEffect(() => {
    if (game?.turn && game.turn !== turnRef.current) {
      turnRef.current = game.turn
      navigate('/game')
    }
  }, [game?.turn])

  const playerNames = useMemo(() => {
    const map = {}
    for (const p of lobby?.players || []) {
      map[p.id] = p.display_name || `Player ${p.id}`
    }
    return map
  }, [lobby?.players])

  return <RoundEnd scores={game?.scores || {}} playerNames={playerNames} onContinue={() => navigate('/game')} />
}
