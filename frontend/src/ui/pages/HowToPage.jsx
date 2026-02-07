import { useNavigate } from 'react-router-dom'
import HowToPlay from '../screens/HowToPlay.jsx'

export default function HowToPage() {
  const navigate = useNavigate()
  return <HowToPlay onClose={() => navigate(-1)} />
}
