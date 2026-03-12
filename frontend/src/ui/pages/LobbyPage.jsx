import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Lobby from '../screens/Lobby.jsx'
import { useApp } from '../../state/AppContext.jsx'

export default function LobbyPage() {
  const navigate = useNavigate()
  const { lobby, game, leaveRoom, emitGameStart, startGameSocket, saveRoomSettings, selfPlayerId, ui, roomRestoreStatus, bindLobbyEvents } = useApp()

  // Bind lobby socket events on mount and when room code is available
  useEffect(() => {
    if (roomRestoreStatus === 'done' && lobby?.room?.code) {
      bindLobbyEvents(lobby.room.code)
    }
  }, [roomRestoreStatus, lobby?.room?.code])

  // Also re-bind when this page mounts (e.g. returning from game-end via play again)
  useEffect(() => {
    if (lobby?.room?.code) {
      bindLobbyEvents(lobby.room.code)
    }
  }, [])

  useEffect(() => {
    console.log('[LobbyPage] lobby check — roomRestoreStatus:', roomRestoreStatus, 'lobby?.room:', !!lobby?.room, 'lobby?.room?.code:', lobby?.room?.code)
    if (roomRestoreStatus !== 'done') return // wait for restore attempt
    if (!lobby?.room) {
      console.log('[LobbyPage] NO LOBBY ROOM — redirecting to /home')
      navigate('/home', { replace: true })
      return
    }
  }, [lobby, roomRestoreStatus])

  useEffect(() => {
    console.log('[LobbyPage] turn check — game?.turn:', !!game?.turn, 'game_type:', game?.turn?.game_type)
    if (game?.turn) {
      console.log('[LobbyPage] HAS TURN — navigating to game')
      startGameSocket()
      const gameType = game.turn.game_type || lobby?.room?.game_type || 'charades'
      navigate(gameType === 'scribble' ? '/scribble' : gameType === 'trivia' ? '/trivia' : '/game')
    }
  }, [game?.turn])

  async function handleStart() {
    if (!lobby?.room?.code) return
    startGameSocket()
    emitGameStart(lobby.room.code)
    const gameType = lobby?.room?.game_type || 'charades'
    navigate(gameType === 'scribble' ? '/scribble' : gameType === 'trivia' ? '/trivia' : '/game')
  }

  return (
    <Lobby
      lobby={lobby}
      onStart={handleStart}
      onLeave={() => { leaveRoom(); navigate('/home') }}
      onSaveSettings={(payload) => {
        if (!lobby?.room?.code) return
        saveRoomSettings(lobby.room.code, payload)
      }}
      loadingSave={Boolean(ui?.loadingKeys?.save_settings)}
      selfPlayerId={selfPlayerId}
    />
  )
}
