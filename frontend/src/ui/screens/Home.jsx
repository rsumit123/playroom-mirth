import { useState } from 'react'
import Spinner from '../components/Spinner.jsx'
import DifficultySelector from '../components/DifficultySelector.jsx'
import RangeSlider from '../components/RangeSlider.jsx'

export default function Home({ onCreate, onJoin, onRejoin, onLeaveRoom, loadingCreate, loadingJoin, loadingLeave, activeRooms = [] }) {
  const [tab, setTab] = useState('create')
  const [rounds, setRounds] = useState(3)
  const [timer, setTimer] = useState(60)
  const [difficulty, setDifficulty] = useState(0)
  const [maxPlayers, setMaxPlayers] = useState(20)
  const [roomCode, setRoomCode] = useState('')

  return (
    <div className="game-shell py-6">
      <div className="page-medium space-y-6">

        {/* Active Rooms */}
        {activeRooms.length > 0 && (
          <div className="card p-5 space-y-4 animate-pop">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">Active Rooms</h2>
              <span className="badge bg-gold/10 text-gold text-xs">{activeRooms.length} active</span>
            </div>
            <div className="space-y-2">
              {activeRooms.map((ar) => (
                <div key={ar.room_code} className="flex items-center justify-between rounded-xl border border-black/5 px-4 py-3">
                  <div className="min-w-0 flex-1">
                    <div className="font-display text-lg tracking-wider">{ar.room_code}</div>
                    <div className="text-xs text-slate/50">
                      {ar.player_count}/{ar.max_players} players
                      <span className="mx-1">&middot;</span>
                      <span className={ar.room_status === 'active' ? 'text-correct' : 'text-accent'}>
                        {ar.room_status === 'active' ? 'In Game' : 'Lobby'}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      className="btn-ghost-sm touch-target text-accent"
                      onClick={() => onRejoin(ar.room_code)}
                    >
                      Rejoin
                    </button>
                    <button
                      className="btn-ghost-sm touch-target text-danger/70 hover:text-danger"
                      onClick={() => onLeaveRoom(ar.room_code)}
                      disabled={loadingLeave}
                    >
                      Leave
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="segmented">
          <button
            className={tab === 'create' ? 'segmented-option-active' : 'segmented-option'}
            onClick={() => setTab('create')}
          >
            Create Room
          </button>
          <button
            className={tab === 'join' ? 'segmented-option-active' : 'segmented-option'}
            onClick={() => setTab('join')}
          >
            Join Room
          </button>
        </div>

        {tab === 'create' ? (
          <div className="card p-6 space-y-6 animate-pop">
            <div>
              <h2 className="font-display text-2xl mb-1">Create a Room</h2>
              <p className="text-sm text-slate/60">Configure your game and invite friends</p>
            </div>

            <RangeSlider label="Rounds" value={rounds} min={1} max={10} onChange={setRounds} />
            <RangeSlider label="Timer" value={timer} min={30} max={120} step={10} unit="s" onChange={setTimer} />

            <div className="space-y-2">
              <span className="text-xs text-slate/60 font-medium">Difficulty</span>
              <DifficultySelector value={difficulty} onChange={setDifficulty} />
            </div>

            <RangeSlider label="Max Players" value={maxPlayers} min={2} max={20} onChange={setMaxPlayers} />

            <button
              className="btn-primary w-full py-3.5 text-base touch-target flex items-center justify-center gap-2"
              onClick={() =>
                onCreate({
                  rounds_total: rounds,
                  difficulty: difficulty,
                  turn_seconds: timer,
                  max_players: maxPlayers
                })
              }
              disabled={loadingCreate}
            >
              {loadingCreate ? <Spinner size={18} /> : null}
              Create Room
            </button>
          </div>
        ) : (
          <div className="card p-6 space-y-6 animate-pop">
            <div>
              <h2 className="font-display text-2xl mb-1">Join a Room</h2>
              <p className="text-sm text-slate/60">Enter the code shared by your host</p>
            </div>

            <input
              className="w-full rounded-xl border-2 border-accent/20 focus:border-accent px-4 py-4 text-center font-display text-2xl tracking-[0.3em] uppercase touch-target outline-none transition"
              placeholder="ABCDEF"
              maxLength={6}
              value={roomCode}
              onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && roomCode.trim()) onJoin(roomCode)
              }}
            />

            <button
              className="btn-primary w-full py-3.5 text-base touch-target flex items-center justify-center gap-2"
              onClick={() => onJoin(roomCode)}
              disabled={loadingJoin || !roomCode.trim()}
            >
              {loadingJoin ? <Spinner size={18} /> : null}
              Join Room
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
