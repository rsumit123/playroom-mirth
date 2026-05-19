import { useEffect } from 'react'
import PlayerAvatar from '../components/PlayerAvatar.jsx'
import { playSound } from '../../lib/sounds.js'

export default function MatchFoundSplash({ opponentName, category, onDone }) {
  useEffect(() => {
    playSound('match-found')
    try {
      import('@capacitor/haptics').then(({ Haptics, ImpactStyle }) => {
        Haptics.impact({ style: ImpactStyle.Medium }).catch(() => {})
      }).catch(() => {})
    } catch { /* not on capacitor */ }
    const id = setTimeout(onDone, 1800)
    return () => clearTimeout(id)
  }, [onDone])

  return (
    <div className="min-h-[100dvh] flex flex-col items-center justify-center bg-bg safe-area-top safe-area-bottom">
      <div className="mb-6 animate-pop">
        <PlayerAvatar name={opponentName} size="lg" />
      </div>
      <p className="text-2xl font-display text-ink">{opponentName}</p>
      <p className="mt-2 text-sm text-accent font-semibold tracking-widest">MATCH FOUND</p>
      <p className="mt-1 text-xs text-slate/60 capitalize">{category}</p>
      <p className="mt-6 text-slate/50">Get ready...</p>
    </div>
  )
}
