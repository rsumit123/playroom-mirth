import { useState } from 'react'

export default function Home({ onSelectGame, onRejoin, onLeaveRoom, onFriends, loadingLeave, activeRooms = [], gameHistory = [], isSignedIn = false }) {
  const [showHistory, setShowHistory] = useState(false)

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
                    <div className="flex items-center gap-2">
                      <div className="font-display text-lg tracking-wider">{ar.room_code}</div>
                      <span className="badge bg-accent/10 text-accent text-[10px]">
                        {ar.game_type === 'scribble' ? 'Scribble' : ar.game_type === 'trivia' ? 'Trivia' : 'Charades'}
                      </span>
                    </div>
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

        {/* Friends shortcut -- signed-in users only */}
        {isSignedIn && (
          <button
            className="card px-5 py-4 flex items-center gap-3 w-full text-left hover:shadow-hover transition"
            onClick={onFriends}
          >
            <div className="h-10 w-10 rounded-xl bg-accent/10 flex items-center justify-center text-xl shrink-0">&#128101;</div>
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-sm">Friends</div>
              <div className="text-xs text-slate/50">Add friends, manage requests</div>
            </div>
            <span className="text-slate/30 text-lg">&rsaquo;</span>
          </button>
        )}

        {/* Game Selector */}
        <div>
          <h2 className="font-display text-2xl mb-1">Choose a Game</h2>
          <p className="text-sm text-slate/60 mb-4">Pick a game and create or join a room</p>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          {/* Charades card */}
          <button
            className="card p-6 text-left hover:shadow-hover transition group"
            onClick={() => onSelectGame('charades')}
          >
            <div className="flex items-start gap-4">
              <div className="h-12 w-12 rounded-xl bg-accent/10 flex items-center justify-center text-2xl shrink-0">
                &#128172;
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-display text-xl mb-1 group-hover:text-accent transition">Charades</div>
                <p className="text-sm text-slate/60">
                  Describe words with hints — no saying the word! Others guess in the chat.
                </p>
              </div>
            </div>
          </button>

          {/* Scribble card */}
          <button
            className="card p-6 text-left hover:shadow-hover transition group"
            onClick={() => onSelectGame('scribble')}
          >
            <div className="flex items-start gap-4">
              <div className="h-12 w-12 rounded-xl bg-accent/10 flex items-center justify-center text-2xl shrink-0">
                &#9999;&#65039;
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-display text-xl mb-1 group-hover:text-accent transition">Scribble</div>
                <p className="text-sm text-slate/60">
                  Draw the word on a canvas — others try to guess what you're sketching!
                </p>
              </div>
            </div>
          </button>

          {/* Trivia card */}
          <button
            className="card p-6 text-left hover:shadow-hover transition group"
            onClick={() => onSelectGame('trivia')}
          >
            <div className="flex items-start gap-4">
              <div className="h-12 w-12 rounded-xl bg-accent/10 flex items-center justify-center text-2xl shrink-0">
                &#129504;
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-display text-xl mb-1 group-hover:text-accent transition">Trivia</div>
                <p className="text-sm text-slate/60">
                  Race to answer trivia questions — math or general knowledge! All players compete at the same time.
                </p>
              </div>
            </div>
          </button>
        </div>

        {/* Recent Games (collapsible) */}
        {isSignedIn && gameHistory.length > 0 && (
          <div className="card overflow-hidden animate-pop">
            <button
              className="w-full px-5 py-4 flex items-center justify-between text-left"
              onClick={() => setShowHistory((v) => !v)}
            >
              <div className="flex items-center gap-2">
                <h2 className="font-semibold">Recent Games</h2>
                <span className="badge bg-accent/10 text-accent text-[10px]">{gameHistory.length}</span>
              </div>
              <span className={`text-slate/40 transition-transform duration-200 ${showHistory ? 'rotate-180' : ''}`}>&#9662;</span>
            </button>
            {showHistory && (
              <div className="px-5 pb-5 space-y-2">
                {gameHistory.map((g) => (
                  <div key={g.id} className="flex items-center justify-between rounded-xl border border-black/5 px-4 py-3">
                    <div className="flex items-center gap-3 min-w-0 flex-1">
                      <span className="text-lg">
                        {g.game_type === 'scribble' ? '\u270F\uFE0F' : g.game_type === 'trivia' ? '\uD83E\uDDE0' : '\uD83D\uDCAC'}
                      </span>
                      <span className="badge bg-accent/10 text-accent text-[10px]">
                        {g.game_type === 'scribble' ? 'Scribble' : g.game_type === 'trivia' ? 'Trivia' : 'Charades'}
                      </span>
                      {g.is_winner && (
                        <span className="text-sm" title="Winner!">&#127942;</span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-xs text-slate/50 shrink-0">
                      <span>{g.player_count} players</span>
                      <span>{new Date(g.played_at).toLocaleDateString()}</span>
                      <span className="font-semibold text-sm text-slate/80">{g.score} pts</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
