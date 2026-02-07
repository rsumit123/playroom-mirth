import { useNavigate } from 'react-router-dom'
import RoundEnd from '../screens/RoundEnd.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function RoundEndPage() {
  const navigate = useNavigate()
  const { game } = useApp()
  return <RoundEnd scores={game?.scores || {}} onContinue={() => navigate('/game')} />
}
