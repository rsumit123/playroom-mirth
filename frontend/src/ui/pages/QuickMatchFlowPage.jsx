import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import QuickMatchCategoryPicker from '../screens/QuickMatchCategoryPicker.jsx'
import QuickMatchSearch from '../screens/QuickMatchSearch.jsx'
import MatchFoundSplash from '../screens/MatchFoundSplash.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function QuickMatchFlowPage() {
  const navigate = useNavigate()
  const { quickmatch, quickmatchJoin, quickmatchCancel, quickmatchReady } = useApp()
  const [category, setCategory] = useState(null)

  function start(cat) {
    setCategory(cat)
    quickmatchJoin(cat)
  }

  function cancel() {
    quickmatchCancel()
    navigate('/play/trivia')
  }

  useEffect(() => {
    if (quickmatch.status === 'matched' && quickmatch.roomCode) {
      quickmatchReady(quickmatch.roomCode)
    }
  }, [quickmatch.status, quickmatch.roomCode])

  if (quickmatch.status === 'matched') {
    return (
      <MatchFoundSplash
        opponentName={quickmatch.opponentName}
        category={category}
        onDone={() => navigate('/trivia')}
      />
    )
  }
  if (quickmatch.status === 'searching') {
    return (
      <QuickMatchSearch
        waitSeconds={quickmatch.waitSeconds}
        category={category}
        onCancel={cancel}
      />
    )
  }
  return (
    <QuickMatchCategoryPicker
      onStart={start}
      onBack={() => navigate('/play/trivia')}
    />
  )
}
