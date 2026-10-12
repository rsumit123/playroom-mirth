import { io } from 'socket.io-client'

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:8000'

let socket

export function getSocket() {
  if (!socket) {
    const s = io(SOCKET_URL, {
      path: '/socket.io',
      autoConnect: false
    })
    // When the server refuses a CONNECT, the client tears the socket down
    // without reconnecting and leaves `connected` set, so connect() would
    // no-op forever. Clear it and start over; the app's 'connect' handlers
    // re-register the room.
    s.on('connect_error', () => {
      if (s.active) return  // a transport failure the manager is already retrying
      s.disconnect()
      setTimeout(() => { if (socket === s && !s.active) s.connect() }, 1000)
    })
    socket = s
  }
  return socket
}

export function connectSocket() {
  const s = getSocket()
  // `active` stays true from the first connect() until a disconnect, so a call
  // made while the CONNECT ack is still in flight doesn't send a second
  // CONNECT. The server answers a duplicate with CONNECT_ERROR, which kills
  // the socket: on a slow link the lobby would silently stop updating.
  if (!s.active) s.connect()
  return s
}

export function disconnectSocket() {
  if (socket && socket.connected) socket.disconnect()
}

export function resetSocket() {
  if (socket) {
    socket.removeAllListeners()
    // Also stops a connect that is still in flight.
    socket.disconnect()
    socket = null
  }
}
