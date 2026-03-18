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
  const [gameHistory, setGameHistory] = useState([])
  const [ui, setUi] = useState({ loading: 0, toast: null, loadingKeys: {} })

  useEffect(() => {
    if (auth.token || auth.guestToken) {
      localStorage.setItem('charade_auth', JSON.stringify(auth))
    } else {
      localStorage.removeItem('charade_auth')
    }
  }, [auth])

  // Persist room code and selfPlayerId to sessionStorage
  // NOTE: Only write when we have valid data. Don't clear on null —
  // leaveRoom() and logout() already handle cleanup. Clearing here
  // would race with restoreRoom() on page load and destroy the saved room.
  useEffect(() => {
    if (room?.code && selfPlayerId) {
      sessionStorage.setItem('charade_room', JSON.stringify({ code: room.code, selfPlayerId }))
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

  // Connect socket and register presence when signed in
  useEffect(() => {
    if (!auth.token) return
    const socket = connectSocket()
    const emitPresence = () => socket.emit('presence:connect', { token: auth.token })
    socket.on('connect', emitPresence)
    if (socket.connected) emitPresence()
    return () => socket.off('connect', emitPresence)
  }, [auth.token])

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

  function handleApiError(err) {
    if (err?.status === 401) {
      logout()
      showToast('Session expired. Please sign in again.')
      return true
    }
    return false
  }

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
      if (displayName && displayName !== auth.guestDisplayName) {
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
      if (handleApiError(err)) throw err
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
      if (handleApiError(err)) throw err
      const message = formatError(err?.message)
      setGame((g) => ({ ...g, error: { message } }))
      showToast(message)
      throw err
    } finally {
      stopLoading('join_room')
    }
  }

  async function saveRoomSettings(roomCode, payload) {
    if (!auth.token && !auth.guestToken) {
      const message = formatError('Authentication required')
      setGame((g) => ({ ...g, error: { message } }))
      showToast(message)
      return null
    }
    startLoading('save_settings')
    try {
      const res = await api.updateRoomSettings(auth.token, auth.guestToken, roomCode, payload)
      setLobby(res)
      setRoom(res.room)
      return res
    } catch (err) {
      if (handleApiError(err)) throw err
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
    } catch (err) {
      if (handleApiError(err)) return
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

  async function fetchGameHistory() {
    if (!auth.token) {
      setGameHistory([])
      return
    }
    try {
      const history = await api.getGameHistory(auth.token)
      setGameHistory(history || [])
    } catch (err) {
      if (handleApiError(err)) return
      setGameHistory([])
    }
  }

  function bindLobbyEvents(roomCode) {
    // Reset game turn so stale data from a previous game doesn't trigger auto-navigation
    setGame((g) => ({ ...g, turn: null, word: null, lastGuess: null, roundEnd: null, gameEnd: null, playAgain: null, messages: [] }))
    const socket = connectSocket()
    socket.off('room:lobby_update')
    socket.off('game:turn_start')
    socket.off('error')
    socket.off('connect')
    socket.on('room:lobby_update', (payload) => {
      setLobby(payload)
      setRoom(payload.room)
    })
    socket.on('game:turn_start', (payload) => setGame((g) => ({ ...g, turn: payload, hint: payload.hint || null })))
    // Pre-register trivia listeners so non-host players don't miss the first question
    socket.off('trivia:question')
    socket.off('trivia:answer_update')
    socket.off('trivia:question_result')
    socket.on('trivia:question', (payload) => setGame((g) => ({
      ...g, trivia: payload, triviaResult: null, triviaAnswered: false, triviaAnswerCount: null,
    })))
    socket.on('trivia:answer_update', (payload) => setGame((g) => ({ ...g, triviaAnswerCount: payload })))
    socket.on('trivia:question_result', (payload) => setGame((g) => ({
      ...g, triviaResult: payload, scores: payload.scores || g.scores,
    })))
    socket.on('error', (payload) => {
      const message = formatError(payload?.message)
      setGame((g) => ({ ...g, error: { ...payload, message } }))
      showToast(message)
    })
    if (roomCode) {
      const data = auth.token
        ? { room_code: roomCode, token: auth.token }
        : { room_code: roomCode, guest_token: auth.guestToken }
      // Re-register on every (re)connection so the socket stays in the room
      socket.on('connect', () => {
        socket.emit('room:register', data)
        if (auth.token) socket.emit('presence:connect', { token: auth.token })
      })
      if (socket.connected) {
        socket.emit('room:register', data)
        if (auth.token) socket.emit('presence:connect', { token: auth.token })
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
    socket.on('game:turn_start', (payload) => setGame((g) => {
      const isSameTurn = g.turn && g.turn.describer_id === payload.describer_id && g.turn.turn_start_ts === payload.turn_start_ts
      return { ...g, turn: payload, hint: payload.hint || null, word: isSameTurn ? g.word : null, lastGuess: null, roundEnd: null, gameEnd: null, playAgain: null, scribbleStrokes: isSameTurn ? (g.scribbleStrokes || []) : [], guessedPlayerIds: isSameTurn ? (g.guessedPlayerIds || []) : [] }
    }))
    socket.on('game:new_word', (payload) => setGame((g) => ({ ...g, word: payload.word })))
    socket.on('chat:message', (payload) => {
      setGame((g) => ({ ...g, messages: [...(g.messages || []), payload] }))
    })
    socket.off('game:hint')
    socket.on('game:hint', (payload) => setGame((g) => ({ ...g, hint: payload.hint })))
    socket.on('game:correct_guess', (payload) => setGame((g) => ({
      ...g,
      lastGuess: payload,
      scores: payload.scores || g.scores,
      messages: [...(g.messages || []), { player_id: payload.guesser_id, message: payload.word || null, correct: true }],
      guessedPlayerIds: [...(g.guessedPlayerIds || []), payload.guesser_id],
      // For scribble, keep the drawing on correct guess (same word continues)
      scribbleStrokes: g.turn?.game_type === 'scribble' ? (g.scribbleStrokes || []) : [],
    })))
    socket.on('game:round_end', (payload) => setGame((g) => ({ ...g, roundEnd: payload })))
    socket.on('game:game_end', (payload) => setGame((g) => ({ ...g, gameEnd: payload })))
    // Trivia events
    socket.off('trivia:question')
    socket.off('trivia:answer_update')
    socket.off('trivia:question_result')
    socket.on('trivia:question', (payload) => setGame((g) => ({
      ...g, trivia: payload, triviaResult: null, triviaAnswered: false, triviaAnswerCount: null,
    })))
    socket.on('trivia:answer_update', (payload) => setGame((g) => ({ ...g, triviaAnswerCount: payload })))
    socket.on('trivia:question_result', (payload) => setGame((g) => ({
      ...g, triviaResult: payload, scores: payload.scores || g.scores,
    })))
    // Scribble events
    socket.off('scribble:draw')
    socket.off('scribble:clear')
    socket.off('scribble:stroke_replay')
    socket.on('scribble:draw', (payload) => {
      setGame((g) => ({ ...g, scribbleStrokes: [...(g.scribbleStrokes || []), payload] }))
    })
    socket.on('scribble:clear', () => {
      setGame((g) => ({ ...g, scribbleStrokes: [] }))
    })
    socket.off('scribble:undo')
    socket.on('scribble:undo', () => {
      setGame((g) => ({ ...g, scribbleStrokes: (g.scribbleStrokes || []).slice(0, -1) }))
    })
    socket.on('scribble:stroke_replay', (payload) => {
      setGame((g) => ({ ...g, scribbleStrokes: payload.strokes || [], scribbleReplayGen: (g.scribbleReplayGen || 0) + 1 }))
    })
    socket.off('game:invite')
    socket.on('game:invite', (payload) => {
      const name = payload?.from_user?.display_name || 'A friend'
      showToast(`${name} invited you to play!`)
    })
    socket.off('game:play_again_update')
    socket.off('game:play_again_ready')
    socket.off('game:play_again_expired')
    socket.on('game:play_again_update', (payload) => setGame((g) => ({ ...g, playAgain: { voted: payload.voted, total: payload.total } })))
    socket.on('game:play_again_ready', () => setGame({ messages: [], scores: {}, word: null, turn: null, lastGuess: null, error: null, playAgain: { ready: true } }))
    socket.on('game:play_again_expired', (payload) => setGame((g) => ({ ...g, playAgain: { expired: true, voted: payload.voted, total: payload.total } })))
    socket.on('game:player_removed', (payload) => {
      setGame((g) => ({ ...g, removed: payload }))
      if (payload?.player_id) {
        setLobby((l) => {
          if (!l?.players) return l
          const removed = l.players.find((p) => p.id === payload.player_id)
          if (removed) {
            showToast(`${removed.display_name || 'A player'} left the game`)
          }
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
    socket.on('connect', () => {
      setGame((g) => ({ ...g, reconnecting: false, reconnectGrace: null }))
      // Re-register in room on reconnect so we keep receiving broadcasts
      if (room?.code) {
        const regData = auth.token
          ? { room_code: room.code, token: auth.token }
          : { room_code: room.code, guest_token: auth.guestToken }
        socket.emit('room:register', regData)
      }
      if (auth.token) socket.emit('presence:connect', { token: auth.token })
    })
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

  function emitScribbleUndo(roomCode) {
    const socket = getSocket()
    return socket.emit('scribble:undo', { room_code: roomCode })
  }

  function emitTriviaAnswer(roomCode, answerIndex) {
    setGame((g) => ({ ...g, triviaAnswered: true }))
    const socket = getSocket()
    return socket.emit('trivia:answer', { room_code: roomCode, answer_index: answerIndex })
  }

  async function emitPlayAgain(roomCode) {
    if (!roomCode) { console.log('[PlayAgain] no roomCode'); return }
    const cleanGame = { messages: [], scores: {}, word: null, turn: null, lastGuess: null, error: null, roundEnd: null, gameEnd: null }

    // Helper: refresh lobby state from REST before signaling ready
    async function refreshAndSignalReady() {
      try {
        const lobbyData = await api.getRoom(roomCode, auth.token, auth.guestToken)
        if (lobbyData?.room) {
          setRoom(lobbyData.room)
          setLobby(lobbyData)
          if (lobbyData.self_player_id) setSelfPlayerId(lobbyData.self_player_id)
        }
      } catch (e) {
        console.log('[PlayAgain] lobby refresh failed (non-fatal):', e.message)
      }
      setGame({ ...cleanGame, playAgain: { ready: true } })
    }

    try {
      console.log('[PlayAgain] voting for', roomCode)
      const res = await api.playAgainVote(auth.token, auth.guestToken, roomCode)
      console.log('[PlayAgain] vote response:', JSON.stringify(res))
      if (res.status === 'ready') {
        console.log('[PlayAgain] ready — refreshing lobby and resetting game state')
        await refreshAndSignalReady()
        return
      }
      if (res.status === 'expired') {
        setGame((g) => ({ ...g, playAgain: { expired: true, voted: res.voted, total: res.total } }))
        return
      }
      setGame((g) => ({ ...g, playAgain: { voted: res.voted, total: res.total } }))
      // Poll for updates every 2s
      let attempts = 0
      const poll = setInterval(async () => {
        attempts++
        if (attempts > 20) { // 40 seconds safety limit
          clearInterval(poll)
          setGame((g) => ({ ...g, playAgain: { expired: true, voted: 0, total: 0 } }))
          return
        }
        try {
          const status = await api.playAgainStatus(roomCode)
          if (status.status === 'ready') {
            console.log('[PlayAgain] poll: ready — refreshing lobby and resetting game state')
            clearInterval(poll)
            await refreshAndSignalReady()
          } else if (status.status === 'expired') {
            clearInterval(poll)
            setGame((g) => ({ ...g, playAgain: { expired: true, voted: status.voted, total: status.total } }))
          } else if (status.status === 'waiting') {
            setGame((g) => ({ ...g, playAgain: { voted: status.voted, total: status.total } }))
          }
        } catch { /* ignore poll errors */ }
      }, 2000)
    } catch (err) {
      setGame((g) => ({ ...g, error: { message: err.message } }))
    }
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
    emitScribbleUndo,
    emitTriviaAnswer,
    emitPlayAgain,
    activeRooms,
    fetchActiveRooms,
    leaveActiveRoom,
    gameHistory,
    fetchGameHistory,
    clearToast,
    leaveRoom
  }), [auth, room, lobby, game, ui, roomRestoreStatus, selfPlayerId, activeRooms, gameHistory])

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  return useContext(AppContext)
}
