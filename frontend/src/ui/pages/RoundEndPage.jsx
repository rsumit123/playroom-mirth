import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import RoundEnd from '../screens/RoundEnd.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function RoundEndPage() {
  const navigate = useNavigate()
  const { game, room } = useApp()
  const turnRef = useRef(game?.turn)

  useEffect(() => {
    if (!room?.code) {
      navigate('/home', { replace: true })
      return
    }
  }, [room])

  useEffect(() => {
    if (game?.turn && game.turn !== turnRef.current) {
      turnRef.current = game.turn
      navigate('/game')
    }
  }, [game?.turn])

  return <RoundEnd scores={game?.scores || {}} onContinue={() => navigate('/game')} />
}
