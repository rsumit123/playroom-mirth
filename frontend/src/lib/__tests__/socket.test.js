import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// A stand-in for a socket.io-client Socket: `active` is true from connect()
// until disconnect(), like the real one.
function fakeSocket() {
  const handlers = {}
  const s = {
    active: false,
    connected: false,
    connect: vi.fn(() => { s.active = true; return s }),
    disconnect: vi.fn(() => { s.active = false; s.connected = false; return s }),
    on: vi.fn((event, fn) => { handlers[event] = fn; return s }),
    removeAllListeners: vi.fn(),
    emit: (event, ...args) => handlers[event]?.(...args),
  }
  return s
}

let created
vi.mock('socket.io-client', () => ({
  io: vi.fn(() => {
    created = fakeSocket()
    return created
  }),
}))

describe('lib/socket', () => {
  let mod

  beforeEach(async () => {
    vi.resetModules()
    vi.useFakeTimers()
    mod = await import('../socket.js')
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('does not send a second CONNECT while the first is still in flight', () => {
    mod.connectSocket()
    mod.connectSocket()
    mod.connectSocket()
    expect(created.connect).toHaveBeenCalledTimes(1)
  })

  it('recovers when the server refuses the CONNECT', () => {
    const s = mod.connectSocket()
    // The client destroys the socket on CONNECT_ERROR: no longer active, but
    // still flagged connected.
    s.active = false
    s.connected = true
    s.emit('connect_error', new Error('Unable to connect'))
    expect(s.disconnect).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(1000)
    expect(s.connect).toHaveBeenCalledTimes(2)
  })

  it('leaves transport errors to the built-in reconnection', () => {
    const s = mod.connectSocket()
    s.emit('connect_error', new Error('xhr poll error'))
    vi.advanceTimersByTime(1000)
    expect(s.disconnect).not.toHaveBeenCalled()
    expect(s.connect).toHaveBeenCalledTimes(1)
  })

  it('does not reconnect a socket that was reset in the meantime', () => {
    const s = mod.connectSocket()
    s.active = false
    s.emit('connect_error', new Error('Unable to connect'))
    mod.resetSocket()
    vi.advanceTimersByTime(1000)
    expect(s.connect).toHaveBeenCalledTimes(1)
  })
})
