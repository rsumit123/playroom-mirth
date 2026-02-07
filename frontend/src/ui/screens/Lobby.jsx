import { useState } from 'react'

export default function Lobby({ lobby, onStart, onLeave, onSaveSettings, selfPlayerId }) {
  const code = lobby?.room?.code || '------'
  const players = lobby?.players || []
  const [settings, setSettings] = useState({
    rounds: lobby?.room?.rounds_total ?? 3,
    difficulty: lobby?.room?.difficulty ?? 2,
    timer: lobby?.room?.turn_seconds ?? 60
  })

  return (
    <div className="min-h-screen px-6 py-10 space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Room Code</div>
            <div className="font-display text-3xl">{code}</div>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="btn-ghost"
              onClick={() => navigator.clipboard?.writeText?.(code)}
            >
              Copy
            </button>
            <button
              className="btn-ghost"
              onClick={() => {
                const payload = { title: 'Charade Chat', text: `Join my room: ${code}`, url: window.location.href }
                if (navigator.share) {
                  navigator.share(payload)
                } else {
                  navigator.clipboard?.writeText?.(code)
                }
              }}
            >
              Share
            </button>
            <button className="btn-ghost" onClick={onLeave}>Leave</button>
          </div>
        </div>
      <div className="card px-4 py-3 flex items-center justify-between animate-pop">
        <div className="text-sm text-slate/70">Lobby is live</div>
        <div className="text-xs uppercase tracking-[0.3em] text-slate/60">{players.length} players</div>
      </div>
      {lobby?.room?.status === 'active' && (
        <div className="card px-4 py-3 flex items-center justify-between">
          <div className="text-sm text-slate/70">Game in progress</div>
          <div className="text-xs text-slate/50">You’ll join the next round</div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="card p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-2xl">Players</h2>
            <div className="text-sm text-slate/60">Join order locked</div>
          </div>
          <div className="space-y-3">
            {players.length === 0 && (
              <div className="text-sm text-slate/60">Waiting for players...</div>
            )}
            {players.map((p, idx) => (
              <div key={p.id} className="flex items-center justify-between rounded-xl border border-black/5 px-4 py-3">
                <div>
                  <div className="font-semibold">{idx + 1}. Player {p.id} {p.id === selfPlayerId ? '(You)' : ''}</div>
                  <div className="text-xs text-slate/60">
                    {p.user_id ? 'Registered' : 'Guest'} · {p.in_game ? 'Active' : 'Waiting for next game'}
                  </div>
                </div>
                <div className={`h-2 w-2 rounded-full ${p.in_game ? 'bg-accent animate-glow' : 'bg-slate/30'}`} />
              </div>
            ))}
          </div>
        </div>

        <div className="card p-6 space-y-4">
          <h2 className="font-display text-2xl">Settings</h2>
          <div className="space-y-3">
            <label className="text-xs text-slate/60">Rounds</label>
            <input
              className="rounded-xl border border-black/10 px-4 py-3 text-sm"
              value={settings.rounds}
              onChange={(e) => setSettings((s) => ({ ...s, rounds: e.target.value }))}
              placeholder="Enter rounds"
            />
            <label className="text-xs text-slate/60">Difficulty (1-3)</label>
            <input
              className="rounded-xl border border-black/10 px-4 py-3 text-sm"
              value={settings.difficulty}
              onChange={(e) => setSettings((s) => ({ ...s, difficulty: e.target.value }))}
              placeholder="Enter difficulty"
            />
            <label className="text-xs text-slate/60">Timer (30-120s)</label>
            <input
              className="rounded-xl border border-black/10 px-4 py-3 text-sm"
              value={settings.timer}
              onChange={(e) => setSettings((s) => ({ ...s, timer: e.target.value }))}
              placeholder="Enter timer"
            />
          </div>
          <button
            className="btn-ghost w-full"
            onClick={() =>
              onSaveSettings?.({
                rounds_total: Number(settings.rounds),
                difficulty: Number(settings.difficulty),
                turn_seconds: Number(settings.timer)
              })
            }
          >
            Save Settings
          </button>
          <button className="btn-primary w-full" onClick={onStart}>Start Game</button>
          <div className="text-xs text-slate/60">Waiting for 2+ players</div>
        </div>
      </div>
    </div>
  )
}
