import { useEffect, useMemo, useRef, useState } from 'react'
import CircularTimer from '../components/CircularTimer.jsx'
import ConfettiBurst from '../components/ConfettiBurst.jsx'
import ChatBubble from '../components/ChatBubble.jsx'
import Scoreboard from '../components/Scoreboard.jsx'
import GameAlerts, { useGameAlerts } from '../components/GameAlerts.jsx'
import LeaveGameModal from '../components/LeaveGameModal.jsx'
import { playSound } from '../../lib/sounds.js'

export default function Game({ game, onSend, onRejoin, onLeave, playerNames = {} }) {
  const [message, setMessage] = useState('')
  const [showLeaveModal, setShowLeaveModal] = useState(false)
  const [confettiKey, setConfettiKey] = useState(0)
  const [remaining, setRemaining] = useState(null)
  const [showScoreboard, setShowScoreboard] = useState(false)
  const [viewport, setViewport] = useState(null)
  const { alerts, addAlert, removeAlert } = useGameAlerts()
  const turn = game?.turn
  const describerId = turn?.describer_id
  const lastGuess = game?.lastGuess
  const role = game?.selfPlayerId && describerId && String(game.selfPlayerId) === String(describerId) ? 'describer' : 'guesser'
  const inputRef = useRef(null)
  const prevTurnRef = useRef(null)
  const prevWordRef = useRef(null)
  const timedUpRef = useRef(false)
  const tickPlayedRef = useRef(false)

  // Track visual viewport height + offset to handle mobile keyboard
  useEffect(() => {
    const vv = window.visualViewport
    if (!vv) return
    const onResize = () => {
      setViewport({ height: vv.height, offsetTop: vv.offsetTop })
    }
    vv.addEventListener('resize', onResize)
    vv.addEventListener('scroll', onResize)
    onResize()
    return () => {
      vv.removeEventListener('resize', onResize)
      vv.removeEventListener('scroll', onResize)
    }
  }, [])

  useEffect(() => {
    if (lastGuess) {
      setConfettiKey((k) => k + 1)
      playSound('correct-guess')
    }
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

  // Alert: new turn / new describer
  useEffect(() => {
    if (!turn?.describer_id || !turn?.turn_start_ts) return
    const prev = prevTurnRef.current
    if (prev?.describer_id === turn.describer_id && prev?.turn_start_ts === turn.turn_start_ts) return
    const isFirst = !prev
    prevTurnRef.current = turn
    timedUpRef.current = false
    tickPlayedRef.current = false
    if (isFirst) return
    playSound('turn-start')
    const isDescriber = game?.selfPlayerId && String(game.selfPlayerId) === String(turn.describer_id)
    if (isDescriber) {
      addAlert('Your turn to describe!', 'accent', '\u{1F3A4}')
    } else {
      const name = playerNames[turn.describer_id] || 'Someone'
      addAlert(`${name} is now describing`, 'info', '\u{1F4AC}')
    }
  }, [turn?.describer_id, turn?.turn_start_ts])

  // Sound: tick at 10 seconds
  useEffect(() => {
    if (remaining === 10 && !tickPlayedRef.current) {
      tickPlayedRef.current = true
      playSound('tick')
    }
  }, [remaining])

  // Alert: time's up
  useEffect(() => {
    if (remaining === 0 && !timedUpRef.current) {
      timedUpRef.current = true
      addAlert("Time's up!", 'warning', '\u23F0')
      playSound('times-up')
    }
  }, [remaining])

  // Alert: new word (describer only, after first word)
  useEffect(() => {
    if (role !== 'describer' || !game?.word) return
    if (prevWordRef.current && prevWordRef.current !== game.word) {
      addAlert('Next word!', 'success', '\u2728')
      playSound('correct-guess')
    }
    prevWordRef.current = game.word
  }, [game?.word, role])

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

  const shellStyle = viewport
    ? { position: 'fixed', top: `max(env(safe-area-inset-top, 0px), ${viewport.offsetTop}px)`, left: 0, right: 0, height: `${viewport.height}px` }
    : { height: '100dvh' }

  return (
    <div className="flex flex-col overflow-hidden relative" style={shellStyle}>
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
          <button className="touch-target p-1.5 -ml-1.5 rounded-lg text-slate/40 hover:text-slate/70 hover:bg-black/5 transition-colors" onClick={() => setShowLeaveModal(true)} aria-label="Leave game">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          </button>
          <span className="text-xs uppercase tracking-wider text-slate/50">
            Round {turn?.round_index || 1}
          </span>
          <span className={role === 'describer' ? 'badge-describer' : 'badge-guesser'}>
            {role === 'describer' ? 'Describer' : 'Guesser'}
          </span>
        </div>
        <CircularTimer remaining={remaining ?? (turn?.turn_seconds || 60)} total={turn?.turn_seconds || 60} size={48} />
      </div>
      <LeaveGameModal open={showLeaveModal} onConfirm={onLeave} onCancel={() => setShowLeaveModal(false)} />

      {/* Word / info bar */}
      {role === 'describer' ? (
        <div className="bg-accent/5 border-b border-accent/10 px-4 py-3 text-center shrink-0 animate-word-pulse">
          <div className="text-[10px] uppercase tracking-widest text-accent/50 mb-1">&#127908; Describe this word</div>
          <div key={game?.word} className="font-display text-3xl sm:text-4xl text-accent animate-pop">{game?.word || '...'}</div>
          <div className="text-[10px] text-slate/40 mt-1">Don&apos;t say the word!</div>
        </div>
      ) : (
        <div className="bg-mist/50 border-b border-black/5 px-4 py-2 text-center shrink-0">
          <div className="text-sm text-slate/50">
            <span className="font-medium text-ink">{playerNames[describerId] || 'Someone'}</span> is describing...
          </div>
          {game?.hint && (
            <div className="font-mono text-lg sm:text-xl tracking-[0.25em] text-ink/70 mt-1.5 select-none">
              {game.hint}
            </div>
          )}
        </div>
      )}

      {/* Correct guess flash */}
      {lastGuess && (
        <div className="bg-correct/10 border-b border-correct/20 px-4 py-2 text-center animate-pop shrink-0">
          <span className="text-correct font-semibold text-sm">
            &#10003; {playerNames[lastGuess.guesser_id] || 'Someone'}{' '}
            {lastGuess.word ? <>guessed &ldquo;{lastGuess.word}&rdquo;</> : <>guessed correctly!</>}
          </span>
        </div>
      )}

      {/* Main area: chat + optional sidebar */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden min-h-0">

        {/* Chat column */}
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2">
            {chatItems.length === 0 && (
              <div className="text-center text-slate/40 py-8">
                <div className="text-2xl mb-2">&#128172;</div>
                <div className="text-sm">{role === 'describer' ? 'Guesses will appear here' : 'Waiting for clues...'}</div>
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

          {/* Game alerts - above input so visible when keyboard is open */}
          <GameAlerts alerts={alerts} onRemove={removeAlert} />

          {/* Input bar */}
          <div className="border-t border-black/5 bg-white/80 backdrop-blur px-3 py-2.5 shrink-0 safe-area-bottom">
            {role === 'describer' ? (
              <div className="text-sm text-slate/50 text-center py-1.5">
                Give clues out loud &mdash; guesses appear above
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <input
                  ref={inputRef}
                  className="flex-1 bg-white rounded-xl px-4 py-3 sm:py-2.5 text-base sm:text-sm outline-none placeholder:text-slate/40 touch-target animate-input-glow"
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
