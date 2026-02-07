import { useEffect, useMemo, useState } from 'react'
import TimerSweep from '../components/TimerSweep.jsx'
import ConfettiBurst from '../components/ConfettiBurst.jsx'
import Scoreboard from '../components/Scoreboard.jsx'

export default function Game({ game, onSend, onRoundEnd, onGameEnd, onRejoin }) {
  const [message, setMessage] = useState('')
  const [confettiKey, setConfettiKey] = useState(0)
  const [remaining, setRemaining] = useState(null)
  const [graceLeft, setGraceLeft] = useState(null)
  const turn = game?.turn
  const describerId = turn?.describer_id ?? '—'
  const lastGuess = game?.lastGuess
  const role = game?.selfPlayerId === describerId ? 'describer' : 'guesser'

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

  useEffect(() => {
    const expires = game?.reconnectGrace?.expires_at
    if (!expires) return
    const update = () => {
      const left = Math.max(expires - Math.floor(Date.now() / 1000), 0)
      setGraceLeft(left)
    }
    update()
    const id = setInterval(update, 1000)
    return () => clearInterval(id)
  }, [game?.reconnectGrace])

  const chatItems = useMemo(() => game?.messages || [], [game?.messages])

  return (
    <div className="min-h-screen px-6 py-10 space-y-6">
      <ConfettiBurst trigger={confettiKey} />
      {game?.reconnecting && (
        <div className="card px-4 py-3 flex items-center justify-between animate-pop">
          <div className="text-sm text-slate/70">Reconnecting…</div>
          <div className="text-xs text-slate/50">
            {graceLeft != null ? `Grace: ${graceLeft}s` : 'Hold tight, restoring your seat'}
          </div>
        </div>
      )}
      {game?.reconnecting && (
        <div className="flex justify-end">
          <button className="btn-ghost" onClick={onRejoin}>Try Rejoin</button>
        </div>
      )}
      {game?.removed && (
        <div className="card px-4 py-3 flex items-center justify-between animate-pop">
          <div className="text-sm text-slate/70">Player removed</div>
          <div className="text-xs text-slate/50">A player didn’t return in time.</div>
        </div>
      )}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Round {game?.roundIndex || 1}</div>
          <div className="font-display text-2xl">Describer: {describerId}</div>
        </div>
        <div className="flex items-center gap-2">
          <div className="h-12 w-12 rounded-full border border-black/10 flex items-center justify-center font-semibold pulse-ring">
            {remaining ?? (turn?.turn_seconds || 60)}
          </div>
        </div>
      </div>
      {lastGuess?.word && (
        <div className="card px-4 py-3 flex items-center justify-between animate-pop">
          <div className="text-sm text-slate/70">Correct Guess</div>
          <div className="font-semibold text-ink">{lastGuess.word}</div>
        </div>
      )}
      <TimerSweep />

      <div className="card p-6 space-y-4">
        <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Your Word</div>
        <div className="font-display text-4xl">{role === 'describer' ? (game?.word || '...') : 'Hidden'}</div>
        <div className="text-sm text-slate/70">
          {role === 'describer' ? 'Describe without using the word itself.' : 'You are guessing.'}
        </div>
      </div>

      <div className="card p-6 h-[45vh] flex flex-col">
        <div className="flex-1 space-y-3 overflow-y-auto">
          {chatItems.length === 0 && <div className="text-sm text-slate/60">No messages yet.</div>}
          {chatItems.map((m, idx) => (
            <div key={idx} className="text-sm">
              <strong>Player {m.player_id}:</strong> {m.message}
            </div>
          ))}
        </div>
        <div className="pt-4 flex gap-3">
          <input
            className="flex-1 rounded-xl border border-black/10 px-4 py-3"
            placeholder="Type your guess..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
          <button
            className="btn-primary glow-chip"
            onClick={() => {
              if (!message.trim()) return
              onSend(message)
              setMessage('')
            }}
          >
            Send
          </button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        <div className="flex gap-3">
          <button className="btn-ghost" onClick={onRoundEnd}>Simulate Round End</button>
          <button className="btn-ghost" onClick={onGameEnd}>Simulate Game End</button>
        </div>
        <div className="card p-4 space-y-3">
          <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Scoreboard</div>
          <Scoreboard scores={game?.scores || {}} />
        </div>
      </div>
    </div>
  )
}
