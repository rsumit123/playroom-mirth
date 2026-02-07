import { useState } from 'react'
import Spinner from '../components/Spinner.jsx'
import PlayerAvatar from '../components/PlayerAvatar.jsx'
import DifficultySelector from '../components/DifficultySelector.jsx'
import RangeSlider from '../components/RangeSlider.jsx'

export default function Lobby({ lobby, onStart, onLeave, onSaveSettings, selfPlayerId, loadingSave }) {
  const code = lobby?.room?.code || '------'
  const players = lobby?.players || []
  const roomMeta = lobby?.room
  const minPlayers = 2
  const maxPlayers = roomMeta?.max_players ?? 20
  const canStart = players.length >= minPlayers
  const isHost = selfPlayerId && lobby?.host_player_id && String(selfPlayerId) === String(lobby.host_player_id)
  const [settings, setSettings] = useState({
    rounds: lobby?.room?.rounds_total ?? 3,
    difficulty: lobby?.room?.difficulty ?? 2,
    timer: lobby?.room?.turn_seconds ?? 60
  })
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard?.writeText?.(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  function handleShare() {
    const payload = { title: 'Charade Chat', text: `Join my room: ${code}`, url: window.location.href }
    if (navigator.share) {
      navigator.share(payload)
    } else {
      handleCopy()
    }
  }

  return (
    <div className="game-shell py-6">
      <div className="page-medium space-y-6">

        {/* Room code hero */}
        <div className="card p-6 text-center space-y-3">
          <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Room Code</div>
          <div className="font-display text-4xl sm:text-5xl tracking-[0.2em] text-accent">{code}</div>
          <div className="flex items-center justify-center gap-3">
            <button className="btn-ghost-sm touch-target" onClick={handleCopy}>
              {copied ? 'Copied!' : 'Copy'}
            </button>
            <button className="btn-ghost-sm touch-target" onClick={handleShare}>
              Share
            </button>
            <button className="btn-ghost-sm touch-target text-danger/70 hover:text-danger hover:border-danger/30" onClick={onLeave}>
              Leave
            </button>
          </div>
        </div>

        {/* Game in progress alert */}
        {lobby?.room?.status === 'active' && (
          <div className="card px-4 py-3 flex items-center justify-between animate-pop">
            <span className="text-sm text-slate/70">Game in progress</span>
            <span className="text-xs text-slate/50">You'll join the next round</span>
          </div>
        )}

        {/* Players */}
        <div className="card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Players</h2>
            <span className="badge bg-accent/10 text-accent">{players.length} / {maxPlayers}</span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {players.map((p) => {
              const name = p.display_name || `Player ${p.id}`
              return (
                <div key={p.id} className="flex items-center gap-2.5 rounded-xl border border-black/5 px-3 py-2.5">
                  <PlayerAvatar name={name} size="md" />
                  <div className="min-w-0 flex-1">
                    <div className="font-medium text-sm truncate">
                      {name}
                      {String(p.id) === String(selfPlayerId) && <span className="text-accent ml-1 text-xs">(You)</span>}
                    </div>
                    {String(p.id) === String(lobby?.host_player_id) && <span className="badge-host text-[10px]">Host</span>}
                  </div>
                  <div className={`h-2 w-2 rounded-full shrink-0 ${p.in_game ? 'bg-correct animate-pulse' : 'bg-slate/20'}`} />
                </div>
              )
            })}
            {/* Empty slots */}
            {players.length < minPlayers && Array.from({ length: minPlayers - players.length }).map((_, i) => (
              <div key={`empty-${i}`} className="flex items-center gap-2.5 rounded-xl border-2 border-dashed border-black/10 px-3 py-2.5">
                <div className="h-9 w-9 rounded-full bg-mist flex items-center justify-center text-slate/30 shrink-0">?</div>
                <div className="text-sm text-slate/40">Waiting...</div>
              </div>
            ))}
          </div>
        </div>

        {/* Settings (host only) */}
        {isHost && (
          <div className="card p-5 space-y-4">
            <h2 className="font-semibold">Game Settings</h2>
            <RangeSlider label="Rounds" value={Number(settings.rounds)} min={1} max={10}
              onChange={(v) => setSettings((s) => ({ ...s, rounds: v }))} />
            <RangeSlider label="Timer" value={Number(settings.timer)} min={30} max={120} step={10} unit="s"
              onChange={(v) => setSettings((s) => ({ ...s, timer: v }))} />
            <div className="space-y-2">
              <span className="text-xs text-slate/60 font-medium">Difficulty</span>
              <DifficultySelector value={Number(settings.difficulty)}
                onChange={(v) => setSettings((s) => ({ ...s, difficulty: v }))} />
            </div>
            <button
              className="btn-ghost w-full touch-target flex items-center justify-center gap-2"
              onClick={() =>
                onSaveSettings?.({
                  rounds_total: Number(settings.rounds),
                  difficulty: Number(settings.difficulty),
                  turn_seconds: Number(settings.timer)
                })
              }
              disabled={loadingSave}
            >
              {loadingSave ? <Spinner size={18} /> : null}
              Save Settings
            </button>
          </div>
        )}

        {/* Non-host waiting state */}
        {!isHost && (
          <div className="card p-5">
            <div className="flex items-center justify-center gap-2">
              <div className="h-2 w-2 rounded-full bg-accent animate-pulse" />
              <span className="text-sm text-slate/60">
                {canStart ? 'Waiting for host to start...' : `Need ${minPlayers}+ players`}
              </span>
            </div>
          </div>
        )}

        {/* Start button — sticky */}
        {isHost && (
          <div className="sticky bottom-4 z-10">
            <button
              className={`w-full py-4 text-lg touch-target rounded-xl font-semibold transition ${canStart ? 'btn-primary animate-glow' : 'btn-ghost opacity-60 cursor-not-allowed'}`}
              onClick={onStart}
              disabled={!canStart}
            >
              {canStart ? 'Start Game' : `Need ${minPlayers - players.length} more player(s)`}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
