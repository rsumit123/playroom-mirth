import { useNavigate } from 'react-router-dom'
import GameEnd from '../screens/GameEnd.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function GameEndPage() {
  const navigate = useNavigate()
  const { game } = useApp()
  return <GameEnd scores={game?.scores || {}} onHome={() => navigate('/home')} />
}
