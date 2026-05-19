import { useMemo, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import GameEnd from '../screens/GameEnd.jsx'
import * as api from '../../lib/api.js'
import { useApp } from '../../state/AppContext.jsx'

const SHARE_URL = 'https://playroom.skdev.one'

export default function GameEndPage() {
  const navigate = useNavigate()
  const { game, lobby, room, leaveRoom, emitPlayAgain, quickmatch, quickmatchJoin, quickmatchRematchBot, selfPlayerId, auth } = useApp()
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

  function handleRematch() {
    leaveRoom()
    if (lastOpponentWasBot) {
      quickmatchRematchBot(lastCategory)
    } else {
      quickmatchJoin(lastCategory)
    }
    navigate('/quickmatch')
  }

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
      onNewOpponent={() => { leaveRoom(); navigate('/quickmatch') }}
      currentStreak={currentStreak}
      onShare={isQuickmatch && youWon ? handleShare : undefined}
    />
  )
}
