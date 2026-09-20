import { gameLabel } from '../../lib/gameLabels.js'
import { useEffect, useRef, useState } from 'react'
import Spinner from '../components/Spinner.jsx'
import { playSound } from '../../lib/sounds.js'
import PlayerAvatar from '../components/PlayerAvatar.jsx'
import DifficultySelector from '../components/DifficultySelector.jsx'
import TriviaCategorySelector from '../components/TriviaCategorySelector.jsx'
import RangeSlider from '../components/RangeSlider.jsx'
import RoomScoreboard from '../components/RoomScoreboard.jsx'
import InviteFriendsDrawer from '../components/InviteFriendsDrawer.jsx'
import * as api from '../../lib/api.js'

export default function Lobby({ lobby, onStart, onLeave, onSaveSettings, onInviteFriend, onAddBot, selfPlayerId, loadingSave, isSignedIn = false, friends = [] }) {
  const code = lobby?.room?.code || '------'
  const players = lobby?.players || []
  const roomMeta = lobby?.room
  const minPlayers = 2
  const maxPlayers = roomMeta?.max_players ?? 20
  const canStart = players.length >= minPlayers
  const isHost = selfPlayerId && lobby?.host_player_id && String(selfPlayerId) === String(lobby.host_player_id)
  const isPoker = roomMeta?.game_type === 'poker'
  const signedIn = isSignedIn
  const [settings, setSettings] = useState({
    rounds: lobby?.room?.rounds_total ?? 3,
    difficulty: lobby?.room?.difficulty ?? 2,
    timer: lobby?.room?.turn_seconds ?? 60,
    triviaCategory: lobby?.room?.trivia_category ?? 'general_knowledge',
  })
  const [copied, setCopied] = useState(false)
  const [scoreboard, setScoreboard] = useState(null)
  const [showInvite, setShowInvite] = useState(false)
  const prevPlayerCountRef = useRef(players.length)

  // Sync settings from server when lobby updates (so non-hosts see host changes)
  useEffect(() => {
    if (!roomMeta) return
    setSettings((s) => ({
      ...s,
      rounds: roomMeta.rounds_total ?? s.rounds,
      difficulty: roomMeta.difficulty ?? s.difficulty,
      timer: roomMeta.turn_seconds ?? s.timer,
      triviaCategory: roomMeta.trivia_category ?? s.triviaCategory,
    }))
  }, [roomMeta?.rounds_total, roomMeta?.difficulty, roomMeta?.turn_seconds, roomMeta?.trivia_category])

  useEffect(() => {
    if (players.length > prevPlayerCountRef.current) {
      playSound('player-join')
    }
    prevPlayerCountRef.current = players.length
  }, [players.length])

  // Fetch scoreboard when lobby loads or room code changes
  useEffect(() => {
    if (!roomMeta?.code) return
    api.getRoomScoreboard(roomMeta.code)
      .then((data) => setScoreboard(data))
      .catch(() => {})
  }, [roomMeta?.code])

  const inviteUrl = `${window.location.origin}/join/${code}`

  function handleCopy() {
    navigator.clipboard?.writeText?.(inviteUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const gameType = roomMeta?.game_type || 'charades'
  const gameLabelText = gameLabel(gameType)

  function handleShare() {
    const payload = { title: 'Mirth', text: `Join my ${gameLabelText} room!`, url: inviteUrl }
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
          <div className="flex items-center justify-center gap-2">
            <div className="text-xs uppercase tracking-[0.3em] text-slate/60">Room Code</div>
            <span className="badge bg-accent/10 text-accent text-[10px]">{gameLabelText}</span>
          </div>
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
          {isSignedIn && (
            <button
              className="btn-primary px-4 py-2 text-sm touch-target mt-2"
              onClick={() => setShowInvite(true)}
            >
              Invite Friends
            </button>
          )}
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
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pb-2">
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

          {/* At a poker table an open seat is somewhere to sit a model. */}
          {isPoker && isHost && players.length < maxPlayers && (
            <div className="space-y-2" data-testid="seat-a-model">
              <span className="text-xs text-slate/60 font-medium">Sit a model at the table</span>
              <div className="segmented">
                {['Easy', 'Medium', 'Hard'].map((tier) => (
                  <button
                    key={tier}
                    className="segmented-option"
                    disabled={!signedIn && tier !== 'Easy'}
                    title={!signedIn && tier !== 'Easy' ? 'Sign in to play the stronger models' : undefined}
                    onClick={() => onAddBot?.(tier)}
                  >
                    {tier}
                  </button>
                ))}
              </div>
              {!signedIn && <p className="text-xs text-slate/50">Sign in to play the stronger models.</p>}
            </div>
          )}
        </div>

        {/* Room scoreboard (shown after at least one game) */}
        <RoomScoreboard
          scoreboard={scoreboard}
          selfName={players.find((p) => String(p.id) === String(selfPlayerId))?.display_name}
        />

        {/* Trivia category picker (visible to all) */}
        {gameType === 'trivia' && (
          <div className="card p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">Category</h2>
              {!isHost && <span className="text-[10px] text-slate/40">Host picks</span>}
            </div>
            <TriviaCategorySelector
              value={settings.triviaCategory}
              onChange={(v) => setSettings((s) => ({ ...s, triviaCategory: v }))}
              readOnly={!isHost}
            />
          </div>
        )}

        {/* Settings (host only) */}
        {isHost && (
          <div className="card p-5 space-y-4">
            <h2 className="font-semibold">Game Settings</h2>
            <RangeSlider label="Rounds" value={Number(settings.rounds)} min={1} max={gameType === 'trivia' ? 5 : 10}
              onChange={(v) => setSettings((s) => ({ ...s, rounds: v }))} />
            {gameType !== 'trivia' && (
              <RangeSlider label="Timer" value={Number(settings.timer)} min={30} max={120} step={10} unit="s"
                onChange={(v) => setSettings((s) => ({ ...s, timer: v }))} />
            )}
            <div className="space-y-2">
              <span className="text-xs text-slate/60 font-medium">Difficulty</span>
              <DifficultySelector value={Number(settings.difficulty)}
                onChange={(v) => setSettings((s) => ({ ...s, difficulty: v }))} hideMixed={gameType === 'trivia'} />
            </div>
            <button
              className="btn-ghost w-full touch-target flex items-center justify-center gap-2"
              onClick={() =>
                onSaveSettings?.({
                  rounds_total: Number(settings.rounds),
                  difficulty: Number(settings.difficulty),
                  turn_seconds: Number(settings.timer),
                  trivia_category: settings.triviaCategory,
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
              onClick={() => onStart({
                rounds_total: Number(settings.rounds),
                difficulty: Number(settings.difficulty),
                turn_seconds: Number(settings.timer),
                trivia_category: settings.triviaCategory,
              })}
              disabled={!canStart}
            >
              {canStart ? 'Start Game' : `Need ${minPlayers - players.length} more player(s)`}
            </button>
          </div>
        )}
      </div>
      <InviteFriendsDrawer
        open={showInvite}
        friends={friends}
        onInvite={onInviteFriend}
        onClose={() => setShowInvite(false)}
      />
    </div>
  )
}
