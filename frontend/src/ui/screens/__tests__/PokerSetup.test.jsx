import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import GameSetup from '../GameSetup.jsx'

describe('setting up a poker table', () => {
  const props = { gameType: 'poker', onCreate: vi.fn(), onJoin: vi.fn(), onBack: vi.fn() }

  it('asks for the shape of the table, not for rounds and a turn timer', () => {
    render(<GameSetup {...props} />)
    expect(screen.getByText('Seats')).toBeInTheDocument()
    expect(screen.getByText('Starting chips')).toBeInTheDocument()
    expect(screen.getByText('Blinds')).toBeInTheDocument()
    expect(screen.queryByText(/Rounds/i)).toBeNull()
    expect(screen.queryByText(/^Timer/i)).toBeNull()
    expect(screen.queryByText(/Difficulty/i)).toBeNull()
  })

  it('sends the chosen table to the server', () => {
    const onCreate = vi.fn()
    render(<GameSetup {...props} onCreate={onCreate} />)
    fireEvent.click(screen.getByRole('button', { name: '3' }))
    fireEvent.click(screen.getByRole('button', { name: '5,000' }))
    fireEvent.click(screen.getByRole('button', { name: '25 / 50' }))
    fireEvent.click(screen.getByRole('button', { name: /create table/i }))
    expect(onCreate).toHaveBeenCalledWith(
      expect.objectContaining({ game_type: 'poker', max_players: 3, starting_chips: 5000, small_blind: 25 }),
    )
  })
})
