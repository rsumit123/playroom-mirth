import { useState } from 'react'
import Logo from '../components/Logo.jsx'
import StatPill from '../components/StatPill.jsx'

export default function Home({ onCreate, onJoin, onHowTo }) {
  const [rounds, setRounds] = useState('3')
  const [timer, setTimer] = useState('60')
  const [difficulty, setDifficulty] = useState('2')
  const [maxPlayers, setMaxPlayers] = useState('20')
  const [roomCode, setRoomCode] = useState('')

  return (
    <div className="min-h-screen px-6 py-10 space-y-8">
      <div className="flex items-center justify-between">
        <div className="font-display text-2xl">Home</div>
        <button className="text-sm text-slate/70" onClick={onHowTo}>How to play</button>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card p-6 space-y-5 hover:shadow-hover transition">
          <h2 className="font-display text-2xl">Create a Room</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <input className="rounded-xl border border-black/10 px-4 py-3" placeholder="Rounds (e.g. 3)" value={rounds} onChange={(e) => setRounds(e.target.value)} />
            <input className="rounded-xl border border-black/10 px-4 py-3" placeholder="Timer (30-120s)" value={timer} onChange={(e) => setTimer(e.target.value)} />
            <input className="rounded-xl border border-black/10 px-4 py-3" placeholder="Difficulty (1-3)" value={difficulty} onChange={(e) => setDifficulty(e.target.value)} />
            <input className="rounded-xl border border-black/10 px-4 py-3" placeholder="Max Players (20)" value={maxPlayers} onChange={(e) => setMaxPlayers(e.target.value)} />
          </div>
          <button
            className="btn-primary w-full transition-transform active:scale-[0.98] glow-chip"
            onClick={() =>
              onCreate({
                rounds_total: Math.max(1, Number(rounds)),
                difficulty: Math.min(3, Math.max(1, Number(difficulty))),
                turn_seconds: Math.min(120, Math.max(30, Number(timer))),
                max_players: Math.min(20, Math.max(2, Number(maxPlayers)))
              })
            }
          >
            Create Room
          </button>
        </div>

        <div className="card p-6 space-y-5 hover:shadow-hover transition">
          <h2 className="font-display text-2xl">Join a Room</h2>
          <input
            className="rounded-xl border border-black/10 px-4 py-3"
            placeholder="Room Code"
            value={roomCode}
            onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
          />
          <button className="btn-ghost w-full transition-transform active:scale-[0.98]" onClick={() => onJoin(roomCode)}>Join Room</button>
          <div className="flex flex-wrap gap-3 pt-4">
            <StatPill label="Active Rooms" value="12" />
            <StatPill label="Players" value="67" />
          </div>
        </div>
      </div>
    </div>
  )
}
