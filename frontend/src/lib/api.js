const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

async function request(path, options = {}) {
  const { headers, ...rest } = options
  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    signal: AbortSignal.timeout(15000),
    headers: {
      'Content-Type': 'application/json',
      ...(headers || {})
    }
  }).catch(err => {
    if (err.name === 'TimeoutError' || err.name === 'AbortError') {
      throw new Error('Request timed out. Please check your connection and try again.')
    }
    throw new Error('Unable to reach the server. Please try again later.')
  })
  if (res.status === 401) {
    const err = new Error('Session expired. Please sign in again.')
    err.status = 401
    throw err
  }
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Request failed: ${res.status}`)
  }
  return res.json()
}

export function loginWithGoogle(idToken) {
  return request('/auth/google', {
    method: 'POST',
    body: JSON.stringify({ id_token: idToken })
  })
}

export function createGuest(displayName) {
  return request('/guest', {
    method: 'POST',
    body: JSON.stringify(displayName ? { display_name: displayName } : {})
  })
}

export function updateGuestName(guestToken, displayName) {
  return request(`/guest?guest_token=${encodeURIComponent(guestToken)}`, {
    method: 'PATCH',
    body: JSON.stringify({ display_name: displayName })
  })
}

export function getActiveRooms(token, guestToken) {
  const params = guestToken ? `?guest_token=${encodeURIComponent(guestToken)}` : ''
  return request(`/rooms/active${params}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined
  })
}

export function leaveRoomApi(token, guestToken, roomCode) {
  const params = guestToken ? `?guest_token=${encodeURIComponent(guestToken)}` : ''
  return request(`/rooms/${roomCode}/leave${params}`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined
  })
}

export function createRoom(token, payload) {
  return request('/rooms', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload)
  })
}

export function createRoomGuest(guestToken, payload) {
  return request('/rooms/guest', {
    method: 'POST',
    body: JSON.stringify({ guest_token: guestToken, ...payload })
  })
}

export function joinRoom(token, guestToken, roomCode) {
  return request('/rooms/join', {
    method: 'POST',
    body: JSON.stringify({ room_code: roomCode, guest_token: guestToken || undefined }),
    headers: token ? { Authorization: `Bearer ${token}` } : undefined
  })
}

export function getRoom(roomCode, token, guestToken) {
  const params = guestToken ? `?guest_token=${encodeURIComponent(guestToken)}` : ''
  return request(`/rooms/${roomCode}${params}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined
  })
}

export function updateRoomSettings(token, guestToken, roomCode, payload) {
  const params = guestToken ? `?guest_token=${encodeURIComponent(guestToken)}` : ''
  return request(`/rooms/${roomCode}/settings${params}`, {
    method: 'PUT',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: JSON.stringify(payload)
  })
}

export function fetchAdminWords(token, params = {}) {
  const query = new URLSearchParams(params).toString()
  const path = query ? `/admin/words?${query}` : '/admin/words'
  return request(path, {
    headers: { Authorization: `Bearer ${token}` }
  })
}

export function createAdminWord(token, payload) {
  return request('/admin/words', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload)
  })
}

export function updateAdminWord(token, wordId, payload) {
  return request(`/admin/words/${wordId}`, {
    method: 'PATCH',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload)
  })
}

export function deleteAdminWord(token, wordId) {
  return request(`/admin/words/${wordId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` }
  })
}

export function getGameHistory(token) {
  return request('/game-history', {
    headers: { Authorization: `Bearer ${token}` }
  })
}

export function fetchAdminStats(token) {
  return request('/admin/stats', {
    headers: { Authorization: `Bearer ${token}` }
  })
}

export function adminCloseRoom(token, roomCode) {
  return request(`/admin/rooms/${roomCode}/close`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` }
  })
}

export function adminCleanupRooms(token) {
  return request('/admin/rooms/cleanup', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` }
  })
}

export function fetchAdminQuestions(token, params = {}) {
  const query = new URLSearchParams(params).toString()
  const path = query ? `/admin/questions?${query}` : '/admin/questions'
  return request(path, {
    headers: { Authorization: `Bearer ${token}` }
  })
}

export function createAdminQuestion(token, payload) {
  return request('/admin/questions', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload)
  })
}

export function deleteAdminQuestion(token, questionId) {
  return request(`/admin/questions/${encodeURIComponent(questionId)}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` }
  })
}

export function getRoomScoreboard(roomCode) {
  return request(`/rooms/${roomCode}/scoreboard`)
}

export function playAgainVote(token, guestToken, roomCode) {
  const params = guestToken ? `?guest_token=${encodeURIComponent(guestToken)}` : ''
  return request(`/rooms/${roomCode}/play-again${params}`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined
  })
}

export function playAgainStatus(roomCode) {
  return request(`/rooms/${roomCode}/play-again`)
}

// Friends API
export function getFriends(token) {
  return request('/friends', { headers: { Authorization: `Bearer ${token}` } })
}

export function getFriendRequests(token) {
  return request('/friends/requests', { headers: { Authorization: `Bearer ${token}` } })
}

export function sendFriendRequest(token, userId) {
  return request('/friends/request', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ user_id: userId })
  })
}

export function acceptFriendRequest(token, userId) {
  return request(`/friends/${userId}/accept`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` }
  })
}

export function rejectFriend(token, userId) {
  return request(`/friends/${userId}/reject`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` }
  })
}

export function searchUsers(token, query) {
  return request(`/users/search?q=${encodeURIComponent(query)}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
}
