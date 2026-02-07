import { useState } from 'react'
import StatPill from '../components/StatPill.jsx'
import Spinner from '../components/Spinner.jsx'

export default function Home({ onCreate, onJoin, loadingCreate, loadingJoin }) {
  const [rounds, setRounds] = useState('3')
  const [timer, setTimer] = useState('60')
  const [difficulty, setDifficulty] = useState('2')
  const [maxPlayers, setMaxPlayers] = useState('20')
  const [roomCode, setRoomCode] = useState('')

  return (
    <div className="min-h-screen page py-10">
      <div className="page-inner space-y-10">
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Welcome Back</div>
          <div className="font-display text-2xl">Control Center</div>
        </div>

        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <div className="hero-card space-y-4">
              <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Tonight’s Highlight</div>
              <h2 className="font-display text-3xl">Host a fast, elegant room.</h2>
              <p className="text-sm text-slate/70">
                Rooms are capped at 20 players, rounds rotate in join order, and every correct guess
                keeps the energy flowing.
              </p>
              <div className="flex flex-wrap gap-3 pt-2">
                <StatPill label="Avg Round" value="2:15" />
                <StatPill label="Replay Rate" value="82%" />
                <StatPill label="Tips" value="3" />
              </div>
            </div>

            <div className="card p-6 space-y-4">
              <h3 className="font-display text-2xl">Quick Host Checklist</h3>
              <ul className="space-y-2 text-sm text-slate/70">
                <li>Set rounds and timer to match your group’s pace.</li>
                <li>Pick difficulty before the first round begins.</li>
                <li>Players who miss the start will join next game.</li>
              </ul>
            </div>
          </div>

          <div className="space-y-6">
            <div className="card p-6 space-y-5 hover:shadow-hover transition">
              <h2 className="font-display text-2xl">Create a Room</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="space-y-1 text-xs text-slate/60">
                  Rounds
                  <input className="rounded-xl border border-black/10 px-4 py-3 text-sm text-ink" placeholder="Rounds (e.g. 3)" value={rounds} onChange={(e) => setRounds(e.target.value)} />
                </label>
                <label className="space-y-1 text-xs text-slate/60">
                  Timer
                  <input className="rounded-xl border border-black/10 px-4 py-3 text-sm text-ink" placeholder="Timer (30-120s)" value={timer} onChange={(e) => setTimer(e.target.value)} />
                </label>
                <label className="space-y-1 text-xs text-slate/60">
                  Difficulty
                  <input className="rounded-xl border border-black/10 px-4 py-3 text-sm text-ink" placeholder="Difficulty (1-3)" value={difficulty} onChange={(e) => setDifficulty(e.target.value)} />
                </label>
                <label className="space-y-1 text-xs text-slate/60">
                  Max Players
                  <input className="rounded-xl border border-black/10 px-4 py-3 text-sm text-ink" placeholder="Max Players (20)" value={maxPlayers} onChange={(e) => setMaxPlayers(e.target.value)} />
                </label>
              </div>
              <button
                className="btn-primary w-full transition-transform active:scale-[0.98] glow-chip flex items-center justify-center gap-2"
                onClick={() =>
                  onCreate({
                    rounds_total: Math.max(1, Number(rounds)),
                    difficulty: Math.min(3, Math.max(1, Number(difficulty))),
                    turn_seconds: Math.min(120, Math.max(30, Number(timer))),
                    max_players: Math.min(20, Math.max(2, Number(maxPlayers)))
                  })
                }
                disabled={loadingCreate}
              >
                {loadingCreate ? <Spinner size={18} /> : null}
                Create Room
              </button>
            </div>

            <div className="card p-6 space-y-5 hover:shadow-hover transition">
              <h2 className="font-display text-2xl">Join a Room</h2>
              <label className="space-y-1 text-xs text-slate/60">
                Room Code
                <input
                  className="rounded-xl border border-black/10 px-4 py-3 text-sm text-ink"
                  placeholder="Room Code"
                  value={roomCode}
                  onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
                />
              </label>
              <button className="btn-ghost w-full transition-transform active:scale-[0.98] flex items-center justify-center gap-2" onClick={() => onJoin(roomCode)} disabled={loadingJoin}>
                {loadingJoin ? <Spinner size={18} /> : null}
                Join Room
              </button>
              <div className="flex flex-wrap gap-3 pt-4">
                <StatPill label="Active Rooms" value="12" />
                <StatPill label="Players" value="67" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
