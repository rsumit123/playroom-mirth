import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import PokerTable from '../poker/PokerTable.jsx'
import { usePokerTable } from '../poker/usePokerTable.js'
import { useApp } from '../../state/AppContext.jsx'

export default function PokerGamePage() {
  const navigate = useNavigate()
  const { room, lobby, game, leaveRoom, roomRestoreStatus, auth } = useApp()
  const { view, pending, error, act, dealNext } = usePokerTable(room?.code)
  const navigatedRef = useRef(false)

  useEffect(() => {
    if (roomRestoreStatus !== 'done') return
    if (!room?.code) navigate('/home', { replace: true })
  }, [room, roomRestoreStatus, navigate])

  useEffect(() => {
    if (game?.gameEnd && !navigatedRef.current) {
      navigatedRef.current = true
      navigate('/game-end')
    }
  }, [game?.gameEnd, navigate])

  const isHost = !!lobby?.room && !!auth?.user && lobby.room.host_user_id === auth.user.id
  const aiSeats = (lobby?.players || []).filter((player) => player.is_bot).map((player) => player.id)

  return (
    <PokerTable
      view={view}
      seatCount={lobby?.room?.max_players}
      aiSeats={aiSeats}
      pending={pending}
      error={error}
      isHost={isHost}
      onAct={act}
      onDealNext={dealNext}
      onLeave={() => { leaveRoom?.(); navigate('/home') }}
    />
  )
}
