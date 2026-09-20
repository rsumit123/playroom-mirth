import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import Lobby from '../Lobby.jsx'

const lobby = (gameType, extra = {}) => ({
  room: { code: 'AB7K92', max_players: 3, game_type: gameType, rounds_total: 1, difficulty: 1, turn_seconds: 30, starting_chips: 1000, small_blind: 5, ...extra },
  players: [{ id: 1, display_name: 'Ana', in_game: true }],
  host_player_id: 1,
})

describe('seating a model at a poker table', () => {
  it('offers the open seat to a model, and only at a poker table', () => {
    const { rerender } = render(<Lobby lobby={lobby('poker')} selfPlayerId={1} isSignedIn onAddBot={vi.fn()} />)
    expect(screen.getByTestId('seat-a-model')).toBeInTheDocument()

    rerender(<Lobby lobby={lobby('charades')} selfPlayerId={1} isSignedIn onAddBot={vi.fn()} />)
    expect(screen.queryByTestId('seat-a-model')).toBeNull()
  })

  it('asks for the tier the host picked', () => {
    const onAddBot = vi.fn()
    render(<Lobby lobby={lobby('poker')} selfPlayerId={1} isSignedIn onAddBot={onAddBot} />)
    fireEvent.click(within(screen.getByTestId('seat-a-model')).getByRole('button', { name: 'Hard' }))
    expect(onAddBot).toHaveBeenCalledWith('Hard')
  })

  it('leaves the stronger models to players who have signed in', () => {
    render(<Lobby lobby={lobby('poker')} selfPlayerId={1} isSignedIn={false} onAddBot={vi.fn()} />)
    const seat = within(screen.getByTestId('seat-a-model'))
    expect(seat.getByRole('button', { name: 'Easy' })).toBeEnabled()
    expect(seat.getByRole('button', { name: 'Hard' })).toBeDisabled()
    expect(screen.getByText(/sign in to play the stronger models/i)).toBeInTheDocument()
  })
})

describe('what a poker lobby does not ask', () => {
  it('leaves out rounds, the turn timer and word difficulty', () => {
    const table = {
      room: { code: 'AB7K92', max_players: 2, game_type: 'poker', rounds_total: 1, difficulty: 1, turn_seconds: 30 },
      players: [{ id: 1, display_name: 'Ana', in_game: true }],
      host_player_id: 1,
    }
    render(<Lobby lobby={table} selfPlayerId={1} isSignedIn onAddBot={vi.fn()} />)
    expect(screen.queryByText('Game Settings')).toBeNull()
  })
})
