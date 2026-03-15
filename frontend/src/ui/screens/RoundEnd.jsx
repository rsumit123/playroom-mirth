import { useEffect, useState } from 'react'
import Scoreboard from '../components/Scoreboard.jsx'
import ConfettiBurst from '../components/ConfettiBurst.jsx'
import PlayerAvatar from '../components/PlayerAvatar.jsx'
import { playSound } from '../../lib/sounds.js'

export default function RoundEnd({ scores, playerNames, isHost, onContinue, onLeave }) {
  const [confettiKey, setConfettiKey] = useState(0)

  useEffect(() => {
    setConfettiKey((k) => k + 1)
    playSound('round-end')
  }, [])

  const entries = Object.entries(scores || {})
    .map(([id, score]) => ({ id, score, name: playerNames?.[id] || `Player ${id}` }))
    .sort((a, b) => b.score - a.score)
  const leader = entries[0]

  return (
    <div className="game-shell">
      <ConfettiBurst trigger={confettiKey} />

      <div className="flex-1 overflow-y-auto">
        <div className="flex flex-col items-center min-h-full my-auto page-narrow py-8 text-center justify-center">
          <div className="text-5xl mb-3">&#127919;</div>
          <div className="text-xs uppercase tracking-[0.3em] text-slate/60 mb-1">Round Complete</div>
          <h1 className="font-display text-3xl sm:text-4xl mb-6">Leaderboard</h1>

          {leader && (
            <div className="card px-5 py-4 mb-6 flex items-center gap-3 animate-pop">
              <PlayerAvatar name={leader.name} size="lg" />
              <div className="text-left">
                <div className="font-semibold">{leader.name}</div>
                <div className="text-sm text-slate/60">Leading with <span className="font-display text-accent font-bold">{leader.score}</span> pts</div>
              </div>
            </div>
          )}

          <div className="w-full max-w-sm mb-8">
            <Scoreboard scores={scores} playerNames={playerNames} highlight={leader?.id} />
          </div>

          <div className="w-full max-w-xs space-y-3">
            {isHost ? (
              <button
                className="btn-primary w-full py-3.5 text-base touch-target animate-pop"
                onClick={onContinue}
              >
                Next Round &rarr;
              </button>
            ) : (
              <div className="text-sm text-slate/50 animate-pop">Waiting for host to continue...</div>
            )}
            <button className="btn-ghost w-full touch-target" onClick={onLeave}>
              Leave Game
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
