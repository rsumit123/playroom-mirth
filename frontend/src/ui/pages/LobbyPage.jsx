import { useEffect, useState, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import Lobby from '../screens/Lobby.jsx'
import { useApp } from '../../state/AppContext.jsx'
import * as api from '../../lib/api.js'

const ROUTE_FOR_GAME = {
  scribble: '/scribble',
  trivia: '/trivia',
  poker: '/poker',
  charades: '/game',
}

export default function LobbyPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { lobby, game, auth, leaveRoom, emitGameStart, startGameSocket, saveRoomSettings, selfPlayerId, ui, roomRestoreStatus, bindLobbyEvents } = useApp()
  const [friends, setFriends] = useState([])

  const isJoining = Boolean(ui?.loadingKeys?.join_room)
  // Track whether we arrived here from a join — React may not have flushed
  // the lobby state yet on the first render after navigate().
  const [waitingForJoin, setWaitingForJoin] = useState(() => Boolean(location.state?.fromJoin))

  // Safety timeout: clear guard after 2s so user isn't stuck if lobby never arrives
  useEffect(() => {
    if (!waitingForJoin) return
    const timer = setTimeout(() => setWaitingForJoin(false), 2000)
    return () => clearTimeout(timer)
  }, [waitingForJoin])

  // Bind lobby socket events when room code becomes available
  useEffect(() => {
    if (lobby?.room?.code) {
      bindLobbyEvents(lobby.room.code)
      setWaitingForJoin(false)
    }
  }, [lobby?.room?.code])

  useEffect(() => {
    if (roomRestoreStatus !== 'done') return // wait for restore attempt
    if (isJoining) return // wait for join to complete
    if (waitingForJoin) return // wait for lobby state to flush after join navigation
    if (!lobby?.room) {
      navigate('/home', { replace: true })
      return
    }
  }, [lobby, roomRestoreStatus, isJoining, waitingForJoin])

  useEffect(() => {
    if (game?.turn) {
      startGameSocket()
      const gameType = game.turn.game_type || lobby?.room?.game_type || 'charades'
      navigate(ROUTE_FOR_GAME[gameType] || '/game')
    }
  }, [game?.turn])

  // Fetch friends list for invite drawer
  const fetchFriends = useCallback(async () => {
    if (!auth?.token) return
    try {
      const data = await api.getFriends(auth.token)
      setFriends(data.friends || [])
    } catch { /* */ }
  }, [auth?.token])

  useEffect(() => {
    fetchFriends()
  }, [fetchFriends])

  async function handleInviteFriend(userId) {
    if (!lobby?.room?.code || !auth?.token) return
    await api.inviteFriendToRoom(auth.token, lobby.room.code, userId)
  }

  async function handleStart(pendingSettings) {
    if (!lobby?.room?.code) return
    // Auto-save any unsaved settings before starting the game
    if (pendingSettings) {
      await saveRoomSettings(lobby.room.code, pendingSettings)
    }
    startGameSocket()
    emitGameStart(lobby.room.code)
    const gameType = lobby?.room?.game_type || 'charades'
    navigate(ROUTE_FOR_GAME[gameType] || '/game')
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
      isSignedIn={Boolean(auth?.token)}
      friends={friends}
      onInviteFriend={handleInviteFriend}
    />
  )
}
