import { useEffect, useState } from 'react'
import Scoreboard from '../components/Scoreboard.jsx'
import ConfettiBurst from '../components/ConfettiBurst.jsx'
import PlayerAvatar from '../components/PlayerAvatar.jsx'
import { playSound } from '../../lib/sounds.js'

export default function GameEnd({
  scores, playerNames, playAgain, onPlayAgain, onHome,
  selfPlayerId, winnerPlayerId, origin, onRematch, onNewOpponent,
}) {
  const [confettiKey, setConfettiKey] = useState(0)
  const [voted, setVoted] = useState(false)

  useEffect(() => {
    setConfettiKey((k) => k + 1)
    playSound('game-end')
  }, [])

  const isQuickmatch = origin === 'quickmatch'
  const youWon = winnerPlayerId != null && String(winnerPlayerId) === String(selfPlayerId)

  const entries = Object.entries(scores || {})
    .map(([id, score]) => ({ id, score, name: playerNames?.[id] || `Player ${id}` }))
    .sort((a, b) => b.score - a.score)
  const winner = entries[0]

  const handlePlayAgain = () => {
    setVoted(true)
    onPlayAgain()
  }

  const waiting = voted && !playAgain?.expired && !playAgain?.ready
  const remaining = playAgain ? playAgain.total - playAgain.voted : null

  return (
    <div className="game-shell">
      <ConfettiBurst trigger={confettiKey} />

      <div className="flex-1 overflow-y-auto">
        <div className="flex flex-col items-center min-h-full my-auto page-narrow py-8 text-center justify-center">
          <div className="text-6xl mb-2 animate-trophy-bounce">{isQuickmatch && !youWon ? '😔' : '🏆'}</div>
          <div className="text-xs uppercase tracking-[0.3em] text-slate/60 mb-1">Game Over</div>
          <h1 className="font-display text-3xl sm:text-4xl mb-6">
            {isQuickmatch
              ? (youWon ? 'You Win!' : 'You Lost')
              : 'Final Results'}
          </h1>

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

          {isQuickmatch ? (
            <div className="w-full max-w-xs space-y-3">
              <button className="btn-primary w-full py-3.5 text-base touch-target" onClick={onRematch}>
                🔁 Rematch
              </button>
              <button className="btn-secondary w-full py-3.5 text-base touch-target" onClick={onNewOpponent}>
                🎲 New Opponent
              </button>
              <button className="btn-ghost w-full touch-target" onClick={onHome}>
                🏠 Home
              </button>
            </div>
          ) : (
            <div className="w-full max-w-xs space-y-3">
              {playAgain?.expired ? (
                <>
                  <div className="text-sm text-slate/60 mb-2">
                    Not everyone wanted to play again ({playAgain.voted}/{playAgain.total} voted)
                  </div>
                  <button className="btn-ghost w-full touch-target" onClick={onHome}>
                    Back to Home
                  </button>
                </>
              ) : waiting ? (
                <>
                  <div className="btn-primary w-full py-3.5 text-base opacity-70 cursor-default flex items-center justify-center gap-2">
                    <span className="inline-block w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                    Waiting for {remaining} more player{remaining !== 1 ? 's' : ''}...
                  </div>
                  <button className="btn-ghost w-full touch-target" onClick={onHome}>
                    Leave
                  </button>
                </>
              ) : (
                <>
                  <button
                    className="btn-primary w-full py-3.5 text-base touch-target"
                    onClick={handlePlayAgain}
                  >
                    Play Again
                  </button>
                  <button
                    className="btn-ghost w-full touch-target"
                    onClick={onHome}
                  >
                    Back to Home
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
