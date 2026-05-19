import { useMemo, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import GameEnd from '../screens/GameEnd.jsx'
import * as api from '../../lib/api.js'
import { useApp } from '../../state/AppContext.jsx'

const SHARE_URL = 'https://playroom.skdev.one'

export default function GameEndPage() {
  const navigate = useNavigate()
  const { game, lobby, room, leaveRoom, emitPlayAgain, quickmatch, quickmatchJoin, quickmatchRematchBot, quickmatchRematchRequest, quickmatchRematchCancel, quickmatchReset, selfPlayerId, auth } = useApp()
  const [currentStreak, setCurrentStreak] = useState(0)

  const playerNames = useMemo(() => {
    const map = {}
    for (const p of lobby?.players || []) {
      map[p.id] = p.display_name || `Player ${p.id}`
    }
    return map
  }, [lobby?.players])

  // When all players agree, navigate to lobby
  useEffect(() => {
    if (game?.playAgain?.ready) {
      navigate('/lobby')
    }
  }, [game?.playAgain?.ready])

  const origin = quickmatch.roomCode && quickmatch.roomCode === room?.code ? 'quickmatch' : 'friends'
  const winnerPlayerId = game?.gameEnd?.winner_player_id ?? null
  const lastCategory = quickmatch.category || 'surprise'
  const lastOpponentWasBot = quickmatch.isBot
  const youWon = winnerPlayerId != null && String(winnerPlayerId) === String(selfPlayerId)
  const isQuickmatch = origin === 'quickmatch'

  // Fetch current streak after the game ends — drives the 🔥 N-win streak badge
  // on wins. The new game is already saved to history by the time game_end
  // fires, so this returns the up-to-date count.
  useEffect(() => {
    if (!isQuickmatch || !auth?.token || !game?.gameEnd) return
    let cancelled = false
    api.getLeaderboard(auth.token, { origin: 'quickmatch', limit: 1 })
      .then(data => { if (!cancelled) setCurrentStreak(data?.current_streak || 0) })
      .catch(() => { /* badge just won't show */ })
    return () => { cancelled = true }
  }, [isQuickmatch, auth?.token, game?.gameEnd])

  const oldRoomCode = room?.code

  function handleRematch() {
    if (lastOpponentWasBot) {
      // Bots always say yes — instant new room, no waiting state.
      leaveRoom()
      quickmatchRematchBot(lastCategory)
      navigate('/quickmatch')
      return
    }
    // Human rematch: stay on GameEnd, wait for opponent's matching request.
    // We DON'T leaveRoom here — the user has to stay anchored on this screen
    // while the request is pending. We'll bail out when the new room arrives.
    quickmatchRematchRequest(oldRoomCode)
  }

  function handleCancelRematch() {
    quickmatchRematchCancel(oldRoomCode)
  }

  // When the rematch is accepted by the opponent, the server emits a fresh
  // `quickmatch:matched` with a new room_code. That's our cue to leave the old
  // room locally and route through the regular splash-into-trivia flow.
  useEffect(() => {
    if (quickmatch.rematchStatus !== 'waiting') return
    if (!quickmatch.roomCode || quickmatch.roomCode === oldRoomCode) return
    // New room code arrived — accept the rematch.
    leaveRoom()
    navigate('/quickmatch')
  }, [quickmatch.rematchStatus, quickmatch.roomCode, oldRoomCode])

  // Build a shareable summary. We hand the opponent name + score margin to the
  // OS share sheet on devices that support it; clipboard otherwise.
  function handleShare() {
    const myScore = (game?.scores || {})[selfPlayerId] ?? 0
    const opp = Object.entries(game?.scores || {})
      .map(([id, score]) => ({ id, score, name: playerNames[id] || 'Opponent' }))
      .find(e => String(e.id) !== String(selfPlayerId))
    const oppText = opp ? ` vs ${opp.name}` : ''
    const text = `🏆 Won my Trivia Quick Play${oppText} with ${myScore} pts on Playroom! Play me at ${SHARE_URL}`
    const payload = { title: 'Playroom — Trivia win', text, url: SHARE_URL }
    if (typeof navigator !== 'undefined' && navigator.share) {
      navigator.share(payload).catch(() => { /* user cancelled */ })
    } else if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(text).catch(() => {})
    }
  }

  return (
    <GameEnd
      scores={game?.scores || {}}
      playerNames={playerNames}
      playAgain={game?.playAgain}
      onPlayAgain={() => emitPlayAgain(room?.code)}
      onHome={() => { leaveRoom(); navigate('/home') }}
      selfPlayerId={selfPlayerId}
      winnerPlayerId={winnerPlayerId}
      origin={origin}
      onRematch={handleRematch}
      onNewOpponent={() => { leaveRoom(); quickmatchReset(); navigate('/quickmatch') }}
      currentStreak={currentStreak}
      onShare={isQuickmatch && youWon ? handleShare : undefined}
      rematchStatus={isQuickmatch && !lastOpponentWasBot ? quickmatch.rematchStatus : 'idle'}
      onCancelRematch={handleCancelRematch}
      opponentName={quickmatch.opponentName}
    />
  )
}
