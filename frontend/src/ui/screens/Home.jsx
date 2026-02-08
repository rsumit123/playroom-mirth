export default function Home({ onSelectGame, onRejoin, onLeaveRoom, loadingLeave, activeRooms = [], gameHistory = [], isSignedIn = false }) {
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
                        {ar.game_type === 'scribble' ? 'Scribble' : 'Charades'}
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

          {/* More Games Coming Soon */}
          <div className="rounded-2xl border-2 border-dashed border-slate/20 p-6 flex items-start gap-4 opacity-70">
            <div className="h-12 w-12 rounded-xl bg-slate/5 flex items-center justify-center text-2xl shrink-0">
              &#127922;
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-display text-xl mb-1 text-slate/50">More Games Coming Soon</div>
              <p className="text-sm text-slate/40">
                We're cooking up new party games. Stay tuned!
              </p>
            </div>
          </div>
        </div>

        {/* Recent Games */}
        {isSignedIn && gameHistory.length > 0 && (
          <div className="card p-5 space-y-4 animate-pop">
            <h2 className="font-semibold">Recent Games</h2>
            <div className="space-y-2">
              {gameHistory.map((g) => (
                <div key={g.id} className="flex items-center justify-between rounded-xl border border-black/5 px-4 py-3">
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <span className="text-lg">
                      {g.game_type === 'scribble' ? '\u270F\uFE0F' : '\uD83D\uDCAC'}
                    </span>
                    <span className="badge bg-accent/10 text-accent text-[10px]">
                      {g.game_type === 'scribble' ? 'Scribble' : 'Charades'}
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
          </div>
        )}
      </div>
    </div>
  )
}
