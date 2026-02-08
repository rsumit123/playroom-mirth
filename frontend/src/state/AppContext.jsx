import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import * as api from '../lib/api.js'
import { formatError } from '../lib/errors.js'
import { connectSocket, getSocket, resetSocket } from '../lib/socket.js'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [auth, setAuth] = useState(() => {
    try {
      const saved = localStorage.getItem('charade_auth')
      return saved ? JSON.parse(saved) : { token: null, guestToken: null, guestDisplayName: null, user: null }
    } catch {
      return { token: null, guestToken: null, guestDisplayName: null, user: null }
    }
  })
  const [room, setRoom] = useState(null)
  const [lobby, setLobby] = useState(null)
  const [selfPlayerId, setSelfPlayerId] = useState(null)
  const [game, setGame] = useState({ messages: [], scores: {}, word: null, turn: null, lastGuess: null, error: null })
  const [roomRestoreStatus, setRoomRestoreStatus] = useState('pending') // 'pending' | 'done'
  const [activeRooms, setActiveRooms] = useState([])
  const [ui, setUi] = useState({ loading: 0, toast: null, loadingKeys: {} })

  useEffect(() => {
    if (auth.token || auth.guestToken) {
      localStorage.setItem('charade_auth', JSON.stringify(auth))
    } else {
      localStorage.removeItem('charade_auth')
    }
  }, [auth])

  // Persist room code and selfPlayerId to sessionStorage
  useEffect(() => {
    if (room?.code && selfPlayerId) {
      sessionStorage.setItem('charade_room', JSON.stringify({ code: room.code, selfPlayerId }))
    } else if (!room) {
      sessionStorage.removeItem('charade_room')
    }
  }, [room?.code, selfPlayerId])

  // Restore room state on mount (page refresh)
  useEffect(() => {
    async function restoreRoom() {
      try {
        const saved = sessionStorage.getItem('charade_room')
        if (!saved) { setRoomRestoreStatus('done'); return }
        const { code } = JSON.parse(saved)
        if (!code) { setRoomRestoreStatus('done'); return }
        if (!(auth.token || auth.guestToken)) { setRoomRestoreStatus('done'); return }
        const res = await api.getRoom(code, auth.token, auth.guestToken)
        if (res?.room) {
          setRoom(res.room)
          setLobby(res)
          if (res.self_player_id) setSelfPlayerId(res.self_player_id)
        }
      } catch {
        sessionStorage.removeItem('charade_room')
      } finally {
        setRoomRestoreStatus('done')
      }
    }
    restoreRoom()
  }, [])

  const startLoading = (key) =>
    setUi((u) => ({
      ...u,
      loading: u.loading + 1,
      loadingKeys: key ? { ...u.loadingKeys, [key]: true } : u.loadingKeys
    }))
  const stopLoading = (key) =>
    setUi((u) => ({
      ...u,
      loading: Math.max(0, u.loading - 1),
      loadingKeys: key ? { ...u.loadingKeys, [key]: false } : u.loadingKeys
    }))
  const showToast = (message) => setUi((u) => ({ ...u, toast: message }))
  const clearToast = () => setUi((u) => ({ ...u, toast: null }))

  function leaveRoom() {
    setRoom(null)
    setLobby(null)
    setSelfPlayerId(null)
    setGame({ messages: [], scores: {}, word: null, turn: null, lastGuess: null, error: null })
    sessionStorage.removeItem('charade_room')
    resetSocket()
  }

  function logout() {
    localStorage.removeItem('charade_auth')
    sessionStorage.removeItem('charade_room')
    setAuth({ token: null, guestToken: null, guestDisplayName: null, user: null })
    setRoom(null)
    setLobby(null)
    setSelfPlayerId(null)
    setGame({ messages: [], scores: {}, word: null, turn: null, lastGuess: null, error: null })
    setUi({ loading: 0, toast: null, loadingKeys: {} })
    resetSocket()
  }

  async function loginWithGoogle(idToken) {
    startLoading('login')
    try {
      const res = await api.loginWithGoogle(idToken)
      setAuth((prev) => ({
        ...prev,
        token: res.access_token,
        user: {
          email: res.user.email,
          display_name: res.user.display_name,
          avatar_url: res.user.avatar_url,
        },
      }))
      return res
    } catch (err) {
      showToast(formatError(err?.message))
      throw err
    } finally {
      stopLoading('login')
    }
  }

  async function ensureGuest(displayName) {
    if (auth.guestToken) {
      if (displayName && !auth.guestDisplayName) {
        try {
          await api.updateGuestName(auth.guestToken, displayName)
          setAuth((prev) => ({ ...prev, guestDisplayName: displayName }))
        } catch { /* non-critical */ }
      }
      return auth.guestToken
    }
    startLoading('guest')
    try {
      const res = await api.createGuest(displayName)
      setAuth((prev) => ({
        ...prev,
        guestToken: res.guest_token,
        guestDisplayName: res.display_name || displayName || null,
      }))
      return res.guest_token
    } catch (err) {
      showToast(formatError(err?.message))
      throw err
    } finally {
      stopLoading('guest')
    }
  }

  async function createRoom(payload) {
    startLoading('create_room')
    try {
      if (auth.token) {
        const res = await api.createRoom(auth.token, payload)
        setRoom(res.room)
        setLobby(res)
        setSelfPlayerId(res.self_player_id || null)
        return res
      }
      const guestToken = await ensureGuest()
      const res = await api.createRoomGuest(guestToken, payload)
      setRoom(res.room)
      setLobby(res)
      setSelfPlayerId(res.self_player_id || null)
      return res
    } catch (err) {
      const message = formatError(err?.message)
      setGame((g) => ({ ...g, error: { message } }))
      showToast(message)
      throw err
    } finally {
      stopLoading('create_room')
    }
  }

  async function joinRoom(roomCode) {
    startLoading('join_room')
    try {
      const res = await api.joinRoom(auth.token, auth.guestToken, roomCode)
      setRoom(res.room)
      setLobby(res)
      setSelfPlayerId(res.self_player_id || null)
      return res
    } catch (err) {
      const message = formatError(err?.message)
      setGame((g) => ({ ...g, error: { message } }))
      showToast(message)
      throw err
    } finally {
      stopLoading('join_room')
    }
  }

  async function saveRoomSettings(roomCode, payload) {
    if (!auth.token) {
      const message = formatError('Authentication required')
      setGame((g) => ({ ...g, error: { message } }))
      showToast(message)
      return null
    }
    startLoading('save_settings')
    try {
      const res = await api.updateRoomSettings(auth.token, roomCode, payload)
      setLobby(res)
      setRoom(res.room)
      return res
    } catch (err) {
      const message = formatError(err?.message)
      setGame((g) => ({ ...g, error: { message } }))
      showToast(message)
      throw err
    } finally {
      stopLoading('save_settings')
    }
  }

  async function fetchActiveRooms() {
    if (!auth.token && !auth.guestToken) {
      setActiveRooms([])
      return
    }
    try {
      const rooms = await api.getActiveRooms(auth.token, auth.guestToken)
      setActiveRooms(rooms || [])
    } catch {
      setActiveRooms([])
    }
  }

  async function leaveActiveRoom(roomCode) {
    startLoading('leave_room')
    try {
      await api.leaveRoomApi(auth.token, auth.guestToken, roomCode)
      await fetchActiveRooms()
    } catch (err) {
      showToast(formatError(err?.message))
    } finally {
      stopLoading('leave_room')
    }
  }

  function bindLobbyEvents(roomCode) {
    const socket = connectSocket()
    socket.off('room:lobby_update')
    socket.off('game:turn_start')
    socket.off('error')
    socket.on('room:lobby_update', (payload) => {
      setLobby(payload)
      setRoom(payload.room)
    })
    socket.on('game:turn_start', (payload) => setGame((g) => ({ ...g, turn: payload })))
    socket.on('error', (payload) => {
      const message = formatError(payload?.message)
      setGame((g) => ({ ...g, error: { ...payload, message } }))
      showToast(message)
    })
    if (roomCode) {
      const data = auth.token
        ? { room_code: roomCode, token: auth.token }
        : { room_code: roomCode, guest_token: auth.guestToken }
      if (socket.connected) {
        socket.emit('room:register', data)
      } else {
        socket.once('connect', () => socket.emit('room:register', data))
      }
    }
  }

  function startGameSocket() {
    const socket = connectSocket()
    socket.off('game:turn_start')
    socket.off('game:new_word')
    socket.off('chat:message')
    socket.off('game:correct_guess')
    socket.off('game:round_end')
    socket.off('game:game_end')
    socket.off('game:player_removed')
    socket.off('error')
    socket.off('game:reconnect_grace')
    socket.off('disconnect')
    socket.off('connect')
    socket.on('game:turn_start', (payload) => setGame((g) => ({ ...g, turn: payload, word: null, lastGuess: null, roundEnd: null, gameEnd: null, scribbleStrokes: [] })))
    socket.on('game:new_word', (payload) => setGame((g) => ({ ...g, word: payload.word })))
    socket.on('chat:message', (payload) => {
      setGame((g) => ({ ...g, messages: [...(g.messages || []), payload] }))
    })
    socket.on('game:correct_guess', (payload) => setGame((g) => ({
      ...g,
      lastGuess: payload,
      scores: payload.scores || g.scores,
      messages: [...(g.messages || []), { player_id: payload.guesser_id, message: payload.word, correct: true }]
    })))
    socket.on('game:round_end', (payload) => setGame((g) => ({ ...g, roundEnd: payload })))
    socket.on('game:game_end', (payload) => setGame((g) => ({ ...g, gameEnd: payload })))
    // Scribble events
    socket.off('scribble:draw')
    socket.off('scribble:clear')
    socket.on('scribble:draw', (payload) => {
      setGame((g) => ({ ...g, scribbleStrokes: [...(g.scribbleStrokes || []), payload] }))
    })
    socket.on('scribble:clear', () => {
      setGame((g) => ({ ...g, scribbleStrokes: [] }))
    })
    socket.on('game:player_removed', (payload) => {
      setGame((g) => ({ ...g, removed: payload }))
      if (payload?.player_id) {
        setLobby((l) => {
          if (!l?.players) return l
          return { ...l, players: l.players.filter((p) => p.id !== payload.player_id) }
        })
      }
    })
    socket.on('error', (payload) => {
      const message = formatError(payload?.message)
      setGame((g) => ({ ...g, error: { ...payload, message } }))
      showToast(message)
    })
    socket.on('game:reconnect_grace', (payload) => {
      if (payload?.player_id && payload.player_id === selfPlayerId) {
        setGame((g) => ({ ...g, reconnecting: true, reconnectGrace: payload }))
      }
    })
    socket.on('disconnect', () => setGame((g) => ({ ...g, reconnecting: true, reconnectGrace: { expires_at: Math.floor(Date.now() / 1000) + 60 } })))
    socket.on('connect', () => setGame((g) => ({ ...g, reconnecting: false, reconnectGrace: null })))
  }

  function emitRoomCreate(payload) {
    const socket = connectSocket()
    const data = auth.token ? { token: auth.token, ...payload } : { guest_token: auth.guestToken, ...payload }
    return socket.emit('room:create', data)
  }

  function emitRoomJoin(roomCode) {
    const socket = connectSocket()
    const data = auth.token ? { room_code: roomCode, token: auth.token } : { room_code: roomCode, guest_token: auth.guestToken }
    return socket.emit('room:join', data)
  }

  function emitGameStart(roomCode) {
    const socket = connectSocket()
    const data = auth.token ? { room_code: roomCode, token: auth.token } : { room_code: roomCode, guest_token: auth.guestToken }
    return socket.emit('game:start', data)
  }

  function emitNextRound(roomCode) {
    const socket = connectSocket()
    const data = auth.token ? { room_code: roomCode, token: auth.token } : { room_code: roomCode, guest_token: auth.guestToken }
    return socket.emit('game:next_round', data)
  }

  function emitChat(roomCode, message) {
    const socket = getSocket()
    return socket.emit('chat:message', { room_code: roomCode, message })
  }

  function emitScribbleDraw(roomCode, stroke) {
    const socket = getSocket()
    return socket.emit('scribble:draw', { room_code: roomCode, ...stroke })
  }

  function emitScribbleClear(roomCode) {
    const socket = getSocket()
    return socket.emit('scribble:clear', { room_code: roomCode })
  }

  const value = useMemo(() => ({
    auth,
    room,
    lobby,
    game,
    ui,
    selfPlayerId,
    roomRestoreStatus,
    logout,
    loginWithGoogle,
    ensureGuest,
    createRoom,
    joinRoom,
    saveRoomSettings,
    bindLobbyEvents,
    startGameSocket,
    emitRoomCreate,
    emitRoomJoin,
    emitGameStart,
    emitNextRound,
    emitChat,
    emitScribbleDraw,
    emitScribbleClear,
    activeRooms,
    fetchActiveRooms,
    leaveActiveRoom,
    clearToast,
    leaveRoom
  }), [auth, room, lobby, game, ui, roomRestoreStatus, selfPlayerId, activeRooms])

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  return useContext(AppContext)
}
