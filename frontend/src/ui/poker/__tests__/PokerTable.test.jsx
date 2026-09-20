import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import PokerTable from '../PokerTable.jsx'

const card = (rank, suit) => ({ rank, suit })

const view = {
  seat_id: 11,
  revision: 4,
  deadline_ts: null,
  reveal_ts: null,
  hole_cards: [card(14, 'spades'), card(13, 'spades')],
  legal_actions: [{ type: 'fold' }, { type: 'call', amount: 10 }, { type: 'raise', min_amount: 20, max_amount: 990 }],
  hand_rank: null,
  public: {
    street: 'preflop', community_cards: [], pot: 15, current_seat: 11,
    dealer_seat: 11, small_blind_seat: 11, big_blind_seat: 22, small_blind: 5, big_blind: 10,
    current_bet: 10, min_raise: 10, winners: [], payouts: [], showdown: [], actions: [],
    players: [
      { seat_id: 11, stack: 995, folded: false, all_in: false, contribution: 5, street_contribution: 5, has_acted: false },
      { seat_id: 22, stack: 990, folded: false, all_in: false, contribution: 10, street_contribution: 10, has_acted: false },
    ],
    names: { 11: 'Ana', 22: 'Gemini 3.7 Flash' },
  },
}

describe('the poker table inside PlayRoom', () => {
  it('shows your cards, the pot, and what you can do about it', () => {
    render(<PokerTable view={view} seatCount={2} onAct={vi.fn()} onLeave={vi.fn()} />)
    expect(screen.getByLabelText('Table')).toBeInTheDocument()
    expect(screen.getByText('15')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: /ace of spades/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Fold' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Call 10' })).toBeInTheDocument()
  })

  it('says who it is waiting for instead of offering you buttons', () => {
    const waiting = { ...view, legal_actions: [], public: { ...view.public, current_seat: 22 } }
    render(<PokerTable view={waiting} seatCount={2} aiSeats={[22]} onAct={vi.fn()} onLeave={vi.fn()} />)
    expect(screen.queryByRole('button', { name: 'Fold' })).toBeNull()
    // The name is on the seat as well as in the line below the table, which is
    // the point: the seat is lit and the line explains the quiet.
    const note = screen.getByRole('status')
    expect(note).toHaveTextContent('Gemini 3.7 Flash')
    expect(note).toHaveTextContent(/is thinking/i)
  })

  it('waits for a seat before it draws a table', () => {
    render(<PokerTable view={null} onAct={vi.fn()} onLeave={vi.fn()} />)
    expect(screen.getByText(/taking your seat/i)).toBeInTheDocument()
  })
})
