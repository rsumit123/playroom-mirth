import { useEffect, useMemo, useRef, useState } from 'react'
import CircularTimer from '../components/CircularTimer.jsx'
import ConfettiBurst from '../components/ConfettiBurst.jsx'
import ChatBubble from '../components/ChatBubble.jsx'
import Scoreboard from '../components/Scoreboard.jsx'

export default function Game({ game, onSend, onRejoin, playerNames = {} }) {
  const [message, setMessage] = useState('')
  const [confettiKey, setConfettiKey] = useState(0)
  const [remaining, setRemaining] = useState(null)
  const [showScoreboard, setShowScoreboard] = useState(false)
  const turn = game?.turn
  const describerId = turn?.describer_id
  const lastGuess = game?.lastGuess
  const role = game?.selfPlayerId && describerId && String(game.selfPlayerId) === String(describerId) ? 'describer' : 'guesser'

  useEffect(() => {
    if (lastGuess?.word) setConfettiKey((k) => k + 1)
  }, [lastGuess])

  useEffect(() => {
    if (!turn?.turn_seconds || !turn?.turn_start_ts) return
    const update = () => {
      const elapsed = Math.floor(Date.now() / 1000 - turn.turn_start_ts)
      const left = Math.max(turn.turn_seconds - elapsed, 0)
      setRemaining(left)
    }
    update()
    const id = setInterval(update, 1000)
    return () => clearInterval(id)
  }, [turn])

  const chatItems = useMemo(() => game?.messages || [], [game?.messages])
  const chatEndRef = useRef(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatItems])

  function handleSend() {
    if (!message.trim()) return
    onSend(message)
    setMessage('')
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && message.trim()) {
      handleSend()
    }
  }

  return (
    <div className="game-shell">
      <ConfettiBurst trigger={confettiKey} />

      {/* Reconnecting bar */}
      {game?.reconnecting && (
        <div className="bg-gold/10 border-b border-gold/20 px-4 py-2 flex items-center justify-between">
          <span className="text-sm text-slate/70">Reconnecting...</span>
          <button className="btn-ghost-sm touch-target" onClick={onRejoin}>Rejoin</button>
        </div>
      )}

      {/* Top status bar */}
      <div className="border-b border-black/5 bg-white/70 backdrop-blur px-4 py-2 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-xs uppercase tracking-wider text-slate/50">
            Round {turn?.round_index || 1}
          </span>
          <span className={role === 'describer' ? 'badge-describer' : 'badge-guesser'}>
            {role === 'describer' ? 'Describer' : 'Guesser'}
          </span>
        </div>
        <CircularTimer remaining={remaining ?? (turn?.turn_seconds || 60)} total={turn?.turn_seconds || 60} size={48} />
      </div>

      {/* Word bar */}
      {role === 'describer' ? (
        <div className="bg-accent/5 border-b border-accent/10 px-4 py-2.5 text-center shrink-0">
          <div className="text-[10px] uppercase tracking-wider text-accent/60 mb-0.5">Your word</div>
          <div className="font-display text-2xl text-accent">{game?.word || '...'}</div>
        </div>
      ) : (
        <div className="bg-mist/50 border-b border-black/5 px-4 py-2 text-center text-sm text-slate/50 shrink-0">
          <span className="font-medium text-ink">{playerNames[describerId] || 'Someone'}</span> is describing...
        </div>
      )}

      {/* Correct guess flash */}
      {lastGuess?.word && (
        <div className="bg-correct/10 border-b border-correct/20 px-4 py-2 text-center animate-pop shrink-0">
          <span className="text-correct font-semibold text-sm">
            &#10003; {playerNames[lastGuess.guesser_id] || 'Someone'} guessed &ldquo;{lastGuess.word}&rdquo;
          </span>
        </div>
      )}

      {/* Main area: chat + optional sidebar */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden min-h-0">

        {/* Chat column */}
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
            {chatItems.length === 0 && (
              <div className="text-center text-sm text-slate/40 py-8">
                {role === 'describer' ? 'Guesses will appear here' : 'Waiting for hints...'}
              </div>
            )}
            {chatItems.map((m, idx) => (
              <ChatBubble
                key={idx}
                playerName={playerNames[m.player_id] || `Player ${m.player_id}`}
                message={m.message}
                isCorrect={m.correct}
                isSelf={m.player_id === game?.selfPlayerId}
              />
            ))}
            <div ref={chatEndRef} />
          </div>

          {/* Input bar */}
          <div className="border-t border-black/5 bg-white/80 backdrop-blur px-3 py-2.5 shrink-0 safe-area-bottom">
            {role === 'describer' ? (
              <div className="text-sm text-slate/50 text-center py-1.5">
                You are describing &mdash; watch the guesses above
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <input
                  className="flex-1 bg-accent/5 rounded-xl px-4 py-2.5 text-sm outline-none placeholder:text-slate/40 touch-target"
                  placeholder="Type your guess..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
                <button
                  className="bg-accent text-white rounded-xl px-4 py-2.5 text-sm font-semibold touch-target shrink-0 transition active:scale-95"
                  onClick={handleSend}
                >
                  Guess
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Desktop sidebar */}
        <div className="hidden lg:block w-72 border-l border-black/5 overflow-y-auto p-4 space-y-4 shrink-0">
          <div className="text-xs uppercase tracking-wider text-slate/50 mb-2">Scoreboard</div>
          <Scoreboard scores={game?.scores || {}} playerNames={playerNames} />
        </div>
      </div>

      {/* Mobile scoreboard FAB */}
      <button
        className="lg:hidden fixed bottom-20 right-4 z-30 h-12 w-12 rounded-full bg-accent text-white shadow-hover flex items-center justify-center text-lg touch-target"
        onClick={() => setShowScoreboard(true)}
      >
        &#127942;
      </button>

      {/* Mobile scoreboard drawer */}
      {showScoreboard && (
        <div className="lg:hidden fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" onClick={() => setShowScoreboard(false)}>
          <div
            className="absolute bottom-0 left-0 right-0 card rounded-t-3xl rounded-b-none p-5 max-h-[60vh] overflow-y-auto animate-slide-up"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="w-10 h-1 rounded-full bg-slate/20 mx-auto mb-4" />
            <div className="text-xs uppercase tracking-wider text-slate/50 mb-3">Scoreboard</div>
            <Scoreboard scores={game?.scores || {}} playerNames={playerNames} />
          </div>
        </div>
      )}
    </div>
  )
}
