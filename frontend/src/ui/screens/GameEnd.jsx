import { useEffect, useState } from 'react'
import Scoreboard from '../components/Scoreboard.jsx'
import ConfettiBurst from '../components/ConfettiBurst.jsx'
import PlayerAvatar from '../components/PlayerAvatar.jsx'

export default function GameEnd({ scores, playerNames, onHome }) {
  const [confettiKey, setConfettiKey] = useState(0)

  useEffect(() => {
    setConfettiKey((k) => k + 1)
  }, [])

  const entries = Object.entries(scores || {})
    .map(([id, score]) => ({ id, score, name: playerNames?.[id] || `Player ${id}` }))
    .sort((a, b) => b.score - a.score)
  const winner = entries[0]

  return (
    <div className="game-shell">
      <ConfettiBurst trigger={confettiKey} />

      <div className="flex-1 flex flex-col items-center justify-center page-narrow py-8 text-center">
        <div className="text-6xl mb-2 animate-trophy-bounce">&#127942;</div>
        <div className="text-xs uppercase tracking-[0.3em] text-slate/60 mb-1">Game Over</div>
        <h1 className="font-display text-3xl sm:text-4xl mb-6">Final Results</h1>

        {winner && (
          <div className="card px-6 py-5 mb-6 animate-pop text-center">
            <div className="flex justify-center mb-3">
              <PlayerAvatar name={winner.name} size="lg" />
            </div>
            <div className="font-display text-xl font-semibold">{winner.name}</div>
            <div className="text-sm text-slate/60 mt-1">
              Winner with <span className="font-display text-accent text-lg font-bold">{winner.score}</span> pts
            </div>
          </div>
        )}

        <div className="w-full max-w-sm mb-8">
          <Scoreboard scores={scores} playerNames={playerNames} highlight={winner?.id} />
        </div>

        <div className="w-full max-w-xs space-y-3">
          <button
            className="btn-primary w-full py-3.5 text-base touch-target"
            onClick={onHome}
          >
            Play Again
          </button>
          <button
            className="btn-ghost w-full touch-target"
            onClick={onHome}
          >
            Back to Home
          </button>
        </div>
      </div>
    </div>
  )
}
