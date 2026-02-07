const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

async function request(path, options = {}) {
  const { headers, ...rest } = options
  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...(headers || {})
    }
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Request failed: ${res.status}`)
  }
  return res.json()
}

export function registerUser(email, password) {
  return request('/register', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  })
}

export function loginUser(email, password) {
  const body = new URLSearchParams()
  body.set('username', email)
  body.set('password', password)
  return fetch(`${API_BASE}/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body
  }).then(async (res) => {
    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || `Login failed: ${res.status}`)
    }
    return res.json()
  })
}

export function createGuest() {
  return request('/guest', { method: 'POST' })
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

export function updateRoomSettings(token, roomCode, payload) {
  return request(`/rooms/${roomCode}/settings`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}` },
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
