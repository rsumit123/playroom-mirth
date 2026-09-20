import { useCallback, useEffect, useRef, useState } from 'react'
import { getSocket } from '../../lib/socket.js'

/** The table, as this client currently understands it.
 *
 *  The server sends one projection per seat, so there is no shared store to
 *  keep in sync and nothing to merge: the newest projection for this seat is
 *  the truth. Two things travel back with an action - the revision it was
 *  decided on, so a stale decision is refused rather than applied, and a key
 *  that makes a retry harmless.
 */
export function usePokerTable(roomCode) {
  const [view, setView] = useState(null)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState(null)
  const keyRef = useRef(0)

  useEffect(() => {
    const socket = getSocket()
    if (!socket) return
    const onState = (next) => {
      setView(next)
      setPending(false)
      setError(null)
    }
    // Always off before on: a duplicate listener applies every update twice.
    socket.off('poker:state', onState)
    socket.on('poker:state', onState)
    return () => socket.off('poker:state', onState)
  }, [roomCode])

  const act = useCallback(async (action) => {
    const socket = getSocket()
    if (!socket || !view) return
    setPending(true)
    keyRef.current += 1
    const ack = await socket.emitWithAck('poker:action', {
      room_code: roomCode,
      action,
      expected_revision: view.revision,
      idempotency_key: `${view.revision}:${keyRef.current}`,
    }).catch(() => ({ ok: false, error: 'NO_REPLY' }))
    if (!ack?.ok) {
      setPending(false)
      setError(ack?.error === 'STALE' ? 'The table moved on. Try again.' : ack?.detail || 'That move was not allowed.')
    }
    return ack
  }, [roomCode, view])

  const dealNext = useCallback(() => {
    const socket = getSocket()
    socket?.emit('poker:next_hand', { room_code: roomCode })
  }, [roomCode])

  return { view, pending, error, act, dealNext }
}
