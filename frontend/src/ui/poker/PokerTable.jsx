import { useMemo } from 'react'
import { Felt } from './Felt.tsx'
import { ActionBar } from './ActionBar.tsx'
import { WaitingNote } from './WaitingNote.tsx'
import { NextHandNote } from './NextHandNote.tsx'
import { DeadlineRing } from './DeadlineRing.tsx'
import { phraseFor } from './actionPhrase.ts'
import './poker-tokens.css'
import './table.css'

/** The poker table.
 *
 *  Everything below the header is the table UI brought over from the standalone
 *  game; this file is the join between it and PlayRoom's socket and lobby.
 */
export default function PokerTable({ view, seatCount, aiSeats = [], pending, error, onAct, onDealNext, isHost, onLeave }) {
  const deadline = useMemo(
    () => (view?.deadline_ts ? new Date(view.deadline_ts * 1000).toISOString() : null),
    [view?.deadline_ts],
  )
  const revealDeadline = useMemo(
    () => (view?.reveal_ts ? new Date(view.reveal_ts * 1000).toISOString() : null),
    [view?.reveal_ts],
  )

  if (!view) {
    return <div className="poker-root"><p className="poker-opening" aria-busy="true">Taking your seat&hellip;</p></div>
  }

  const pub = view.public
  const complete = pub.street === 'complete'
  const myTurn = pub.current_seat === view.seat_id
  const turnSeat = pub.current_seat
  const waitingFor = !myTurn && turnSeat !== null && turnSeat !== undefined
    ? pub.names?.[turnSeat] || `Seat ${turnSeat}`
    : null

  const actions = pub.actions || []
  const last = actions[actions.length - 1]
  const lastAction = last
    ? phraseFor(last, last.seat_id === view.seat_id ? 'You' : pub.names?.[last.seat_id] || `Seat ${last.seat_id}`)
    : null

  return (
    <div className="poker-root">
      <header className="poker-header">
        <button type="button" className="poker-leave" onClick={onLeave}>&larr;</button>
        <span className="poker-blinds">{pub.small_blind}/{pub.big_blind}</span>
      </header>

      <Felt
        projection={{ public: pub, seat_id: view.seat_id, hole_cards: view.hole_cards, legal_actions: view.legal_actions, hand_rank: view.hand_rank }}
        deadline={deadline}
        seatCount={seatCount}
        aiSeats={aiSeats}
        thinkingSeats={turnSeat !== null && aiSeats.includes(turnSeat) ? [turnSeat] : []}
      />

      <div className="action-slot">
        {complete && <NextHandNote revealDeadline={revealDeadline} onNextHand={isHost ? onDealNext : null} />}
        {!complete && waitingFor && (
          <WaitingNote
            name={waitingFor}
            isAi={aiSeats.includes(turnSeat)}
            deadline={<DeadlineRing deadline={deadline} />}
            lastAction={lastAction}
          />
        )}
        {!complete && myTurn && (
          <ActionBar
            legal={view.legal_actions || []}
            canAct={!pending}
            onAct={onAct}
            status={pending ? 'submitting' : 'your-turn'}
            pot={pub.pot}
            bigBlind={pub.big_blind}
            deadline={<DeadlineRing deadline={deadline} />}
            error={error}
          />
        )}
      </div>
    </div>
  )
}
