import { useEffect, useRef, useState } from 'react'
import CircularTimer from '../components/CircularTimer.jsx'
import ConfettiBurst from '../components/ConfettiBurst.jsx'
import Scoreboard from '../components/Scoreboard.jsx'
import PlayerAvatar from '../components/PlayerAvatar.jsx'
import GameAlerts, { useGameAlerts } from '../components/GameAlerts.jsx'
import { playSound } from '../../lib/sounds.js'

const OPTION_COLORS = [
  { bg: 'bg-[#e74c3c]/10', border: 'border-[#e74c3c]/20', activeBg: 'bg-[#e74c3c]/20' },
  { bg: 'bg-[#3498db]/10', border: 'border-[#3498db]/20', activeBg: 'bg-[#3498db]/20' },
  { bg: 'bg-[#f39c12]/10', border: 'border-[#f39c12]/20', activeBg: 'bg-[#f39c12]/20' },
  { bg: 'bg-[#2ecc71]/10', border: 'border-[#2ecc71]/20', activeBg: 'bg-[#2ecc71]/20' },
]

export default function TriviaGame({ game, onAnswer, playerNames = {} }) {
  const [confettiKey, setConfettiKey] = useState(0)
  const [remaining, setRemaining] = useState(null)
  const [showScoreboard, setShowScoreboard] = useState(false)
  const [selectedAnswer, setSelectedAnswer] = useState(null)
  const { alerts, addAlert, removeAlert } = useGameAlerts()
  const prevQuestionRef = useRef(null)
  const questionReceivedRef = useRef(null)

  const trivia = game?.trivia
  const result = game?.triviaResult
  const answered = game?.triviaAnswered
  const answerCount = game?.triviaAnswerCount

  // Track when question arrives (for timer)
  useEffect(() => {
    if (trivia && trivia.question_index !== prevQuestionRef.current) {
      prevQuestionRef.current = trivia.question_index
      questionReceivedRef.current = Date.now()
      setSelectedAnswer(null)
      if (trivia.question_index === 0) {
        addAlert(`Round ${trivia.round_index} - Let's go!`, 'accent', null, 2000)
      }
    }
  }, [trivia?.question_index, trivia?.round_index])

  // Timer countdown
  useEffect(() => {
    if (!trivia?.time_seconds || result) {
      setRemaining(null)
      return
    }
    const startedAt = questionReceivedRef.current || Date.now()
    const update = () => {
      const elapsed = (Date.now() - startedAt) / 1000
      const r = Math.max(0, Math.ceil(trivia.time_seconds - elapsed))
      setRemaining(r)
    }
    update()
    const id = setInterval(update, 250)
    return () => clearInterval(id)
  }, [trivia?.question_index, trivia?.time_seconds, result])

  // Confetti + sound on correct answer
  useEffect(() => {
    if (!result) return
    const me = result.player_results?.find((r) => String(r.player_id) === String(game?.selfPlayerId))
    if (me?.correct) {
      setConfettiKey((k) => k + 1)
      playSound('correct-guess')
    }
  }, [result])

  function handleAnswer(index) {
    if (answered || result) return
    setSelectedAnswer(index)
    onAnswer(index)
  }

  const totalPlayers = answerCount?.total_players || 0
  const answeredCount = answerCount?.answered_count || 0

  return (
    <div className="game-shell">
      <ConfettiBurst key={confettiKey} />
      <GameAlerts alerts={alerts} onRemove={removeAlert} />

      <div className="flex flex-col lg:flex-row h-full">
        {/* Main area */}
        <div className="flex-1 flex flex-col min-w-0">

          {/* Top bar: progress + timer */}
          <div className="bg-white/60 backdrop-blur border-b border-black/5 px-4 py-3 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-3">
              <span className="badge bg-accent/10 text-accent text-xs font-semibold">
                Round {trivia?.round_index || 1}
              </span>
              <span className="text-sm text-slate/60">
                Question {(trivia?.question_index ?? 0) + 1} of {trivia?.total_questions || 10}
              </span>
            </div>
            {remaining != null && !result && (
              <CircularTimer remaining={remaining} total={trivia?.time_seconds || 15} />
            )}
            {result && (
              <span className="text-sm font-medium text-correct">Results</span>
            )}
          </div>

          {/* Question + Options */}
          <div className="flex-1 overflow-y-auto px-4 py-6">
            <div className="max-w-lg mx-auto space-y-6">

              {/* Question card */}
              {trivia && (
                <div className="card p-6 text-center animate-pop">
                  <p className={`font-display ${result ? 'text-xl' : 'text-2xl sm:text-3xl'} text-ink leading-snug`}>
                    {trivia.question_text}
                  </p>
                </div>
              )}

              {/* Options grid */}
              {trivia && (
                <div className="grid grid-cols-2 gap-3">
                  {trivia.options.map((opt, i) => {
                    const colors = OPTION_COLORS[i]
                    let className = `rounded-xl border-2 py-5 px-4 text-center font-semibold text-lg transition-all touch-target select-none `

                    if (result) {
                      // Result phase: show correct/wrong
                      if (i === result.correct_index) {
                        className += 'bg-correct/15 border-correct ring-2 ring-correct text-correct'
                      } else if (i === selectedAnswer && i !== result.correct_index) {
                        className += 'bg-danger/15 border-danger ring-2 ring-danger text-danger'
                      } else {
                        className += `${colors.bg} ${colors.border} opacity-30`
                      }
                    } else if (answered) {
                      // Answered but waiting for results
                      if (i === selectedAnswer) {
                        className += `${colors.activeBg} ${colors.border} ring-2 ring-accent`
                      } else {
                        className += `${colors.bg} ${colors.border} opacity-40`
                      }
                    } else {
                      // Active: can click
                      className += `${colors.bg} ${colors.border} hover:shadow-hover active:scale-[0.97] cursor-pointer`
                    }

                    return (
                      <button
                        key={i}
                        className={className}
                        onClick={() => handleAnswer(i)}
                        disabled={answered || !!result}
                      >
                        {opt}
                      </button>
                    )
                  })}
                </div>
              )}

              {/* Answer count (during question) */}
              {trivia && !result && totalPlayers > 0 && (
                <div className="text-center text-sm text-slate/50">
                  {answeredCount} of {totalPlayers} answered
                </div>
              )}

              {/* Result details */}
              {result && (
                <div className="card p-4 space-y-2 animate-pop">
                  <h3 className="text-sm font-semibold text-slate/60 mb-2">Results</h3>
                  {result.player_results
                    ?.slice()
                    .sort((a, b) => b.points - a.points)
                    .map((r) => {
                      const name = playerNames[r.player_id] || `Player ${r.player_id}`
                      const isSelf = String(r.player_id) === String(game?.selfPlayerId)
                      return (
                        <div
                          key={r.player_id}
                          className={`flex items-center gap-3 rounded-xl px-3 py-2 ${isSelf ? 'bg-accent/5 ring-1 ring-accent/20' : ''}`}
                        >
                          <PlayerAvatar name={name} size="sm" />
                          <span className="font-medium text-sm flex-1 truncate">
                            {name}
                            {isSelf && <span className="text-accent ml-1 text-xs">(You)</span>}
                          </span>
                          <span className="text-lg mr-2">
                            {r.correct ? '\u2705' : r.answer_index === -1 ? '\u23F0' : '\u274C'}
                          </span>
                          {r.correct && (
                            <span className="text-sm font-semibold text-correct">+{r.points}</span>
                          )}
                          {r.correct && r.time_taken != null && (
                            <span className="text-xs text-slate/40">{r.time_taken}s</span>
                          )}
                        </div>
                      )
                    })}
                  <div className="text-center text-xs text-slate/40 mt-2 animate-pulse">
                    Next question in a moment...
                  </div>
                </div>
              )}

              {/* Waiting state */}
              {!trivia && !result && (
                <div className="card p-8 text-center">
                  <div className="text-slate/40 animate-pulse">Waiting for question...</div>
                </div>
              )}

            </div>
          </div>
        </div>

        {/* Desktop scoreboard sidebar */}
        <div className="hidden lg:block w-64 xl:w-72 border-l border-black/5 bg-white/40 overflow-y-auto p-4">
          <Scoreboard scores={game?.scores || {}} playerNames={playerNames} highlight={game?.selfPlayerId} />
        </div>
      </div>

      {/* Mobile scoreboard FAB */}
      <button
        className="lg:hidden fixed bottom-4 right-4 z-30 h-12 w-12 rounded-full bg-accent text-white shadow-lg flex items-center justify-center text-xl touch-target active:scale-95 transition"
        onClick={() => setShowScoreboard((v) => !v)}
        aria-label="Scoreboard"
      >
        &#127942;
      </button>

      {/* Mobile scoreboard drawer */}
      {showScoreboard && (
        <>
          <div className="lg:hidden fixed inset-0 z-40 bg-black/30" onClick={() => setShowScoreboard(false)} />
          <div className="lg:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur rounded-t-2xl shadow-2xl p-4 max-h-[60vh] overflow-y-auto safe-area-bottom animate-pop">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">Scoreboard</h3>
              <button className="text-slate/40 text-xl" onClick={() => setShowScoreboard(false)}>&times;</button>
            </div>
            <Scoreboard scores={game?.scores || {}} playerNames={playerNames} highlight={game?.selfPlayerId} />
          </div>
        </>
      )}
    </div>
  )
}
