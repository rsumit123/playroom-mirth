import { useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import GameEnd from '../screens/GameEnd.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function GameEndPage() {
  const navigate = useNavigate()
  const { game, lobby, room, leaveRoom, emitPlayAgain, quickmatch, quickmatchJoin, quickmatchRematchBot, selfPlayerId } = useApp()
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

  function handleRematch() {
    leaveRoom()
    if (lastOpponentWasBot) {
      // Instant bot rematch — skip the 15s queue, server pairs synchronously.
      quickmatchRematchBot(lastCategory)
    } else {
      // Human v1: re-queue. Human-vs-human rematch handshake is deferred to v1.1.
      quickmatchJoin(lastCategory)
    }
    navigate('/quickmatch')
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
    />
  )
}
