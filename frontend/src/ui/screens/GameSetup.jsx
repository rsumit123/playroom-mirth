import { useState } from 'react'
import Spinner from '../components/Spinner.jsx'
import DifficultySelector from '../components/DifficultySelector.jsx'
import TriviaCategorySelector from '../components/TriviaCategorySelector.jsx'
import RangeSlider from '../components/RangeSlider.jsx'

const GAME_LABELS = {
  charades: 'Charades',
  scribble: 'Scribble',
  trivia: 'Trivia',
}

export default function GameSetup({ gameType = 'charades', onCreate, onJoin, onBack, loadingCreate, loadingJoin, signedIn = false, onQuickPlay }) {
  const showQuickPlay = gameType === 'trivia' && signedIn && !!onQuickPlay
  const [tab, setTab] = useState(showQuickPlay ? 'quickplay' : 'create')
  const [rounds, setRounds] = useState(3)
  const [timer, setTimer] = useState(120)
  const [difficulty, setDifficulty] = useState(0)
  const [triviaCategory, setTriviaCategory] = useState('general_knowledge')
  const [maxPlayers, setMaxPlayers] = useState(20)
  const [roomCode, setRoomCode] = useState('')

  const label = GAME_LABELS[gameType] || gameType

  return (
    <div className="game-shell py-6">
      <div className="page-medium space-y-6">

        {/* Back + Title */}
        <div className="relative text-center py-1">
          <button className="btn-ghost-sm touch-target absolute left-0 top-1/2 -translate-y-1/2" onClick={onBack}>&larr; Back</button>
          <h2 className="font-display text-2xl">{label}</h2>
          <p className="text-xs text-slate/50">Create or join a room</p>
        </div>

        <div className="segmented">
          {showQuickPlay && (
            <button
              className={tab === 'quickplay' ? 'segmented-option-active' : 'segmented-option'}
              onClick={() => setTab('quickplay')}
            >
              ⚡ Quick Play
            </button>
          )}
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

        {tab === 'quickplay' ? (
          <div className="card p-6 space-y-4 animate-pop text-center">
            <div className="text-5xl">⚡</div>
            <h2 className="font-display text-2xl">Quick Play</h2>
            <p className="text-sm text-slate/60">
              Test yourself against real live players — get paired instantly,
              no room setup needed.
            </p>
            <button
              className="btn-primary w-full py-3.5 text-base touch-target"
              onClick={onQuickPlay}
            >
              Play Now &rarr;
            </button>
          </div>
        ) : tab === 'create' ? (
          <div className="card p-6 space-y-6 animate-pop">
            <RangeSlider label="Rounds" value={rounds} min={1} max={gameType === 'trivia' ? 5 : 10} onChange={setRounds} />
            {gameType !== 'trivia' && (
              <RangeSlider label="Timer" value={timer} min={30} max={120} step={10} unit="s" onChange={setTimer} />
            )}

            {gameType === 'trivia' && (
              <div className="space-y-2">
                <span className="text-xs text-slate/60 font-medium">Category</span>
                <TriviaCategorySelector value={triviaCategory} onChange={setTriviaCategory} />
              </div>
            )}

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
                  turn_seconds: gameType === 'trivia' ? 0 : timer,
                  max_players: maxPlayers,
                  game_type: gameType,
                  trivia_category: gameType === 'trivia' ? triviaCategory : 'math',
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
