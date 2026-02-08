import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Home from '../Home.jsx'

describe('Home', () => {
  const defaultProps = {
    onSelectGame: vi.fn(),
    onRejoin: vi.fn(),
    onLeaveRoom: vi.fn(),
    loadingLeave: false,
    activeRooms: [],
  }

  it('renders the Charades game card', () => {
    render(<Home {...defaultProps} />)
    expect(screen.getByText('Charades')).toBeInTheDocument()
    expect(screen.getByText(/Describe words with hints/)).toBeInTheDocument()
  })

  it('renders the Scribble game card', () => {
    render(<Home {...defaultProps} />)
    expect(screen.getByText('Scribble')).toBeInTheDocument()
    expect(screen.getByText(/Draw the word on a canvas/)).toBeInTheDocument()
  })

  it('renders the "Choose a Game" heading', () => {
    render(<Home {...defaultProps} />)
    expect(screen.getByText('Choose a Game')).toBeInTheDocument()
  })

  it('calls onSelectGame with "charades" when Charades card is clicked', () => {
    const onSelectGame = vi.fn()
    render(<Home {...defaultProps} onSelectGame={onSelectGame} />)
    fireEvent.click(screen.getByText('Charades'))
    expect(onSelectGame).toHaveBeenCalledWith('charades')
  })

  it('calls onSelectGame with "scribble" when Scribble card is clicked', () => {
    const onSelectGame = vi.fn()
    render(<Home {...defaultProps} onSelectGame={onSelectGame} />)
    fireEvent.click(screen.getByText('Scribble'))
    expect(onSelectGame).toHaveBeenCalledWith('scribble')
  })

  it('does not render active rooms section when activeRooms is empty', () => {
    render(<Home {...defaultProps} activeRooms={[]} />)
    expect(screen.queryByText('Active Rooms')).not.toBeInTheDocument()
  })

  it('renders active rooms when provided', () => {
    const activeRooms = [
      { room_code: 'ABC123', game_type: 'charades', player_count: 3, max_players: 10, room_status: 'lobby' },
    ]
    render(<Home {...defaultProps} activeRooms={activeRooms} />)
    expect(screen.getByText('Active Rooms')).toBeInTheDocument()
    expect(screen.getByText('ABC123')).toBeInTheDocument()
    expect(screen.getByText('Rejoin')).toBeInTheDocument()
    expect(screen.getByText('Leave')).toBeInTheDocument()
  })

  it('calls onRejoin with the room code when Rejoin is clicked', () => {
    const onRejoin = vi.fn()
    const activeRooms = [
      { room_code: 'ABC123', game_type: 'scribble', player_count: 2, max_players: 8, room_status: 'active' },
    ]
    render(<Home {...defaultProps} onRejoin={onRejoin} activeRooms={activeRooms} />)
    fireEvent.click(screen.getByText('Rejoin'))
    expect(onRejoin).toHaveBeenCalledWith('ABC123')
  })

  it('calls onLeaveRoom with the room code when Leave is clicked', () => {
    const onLeaveRoom = vi.fn()
    const activeRooms = [
      { room_code: 'XYZ789', game_type: 'charades', player_count: 4, max_players: 10, room_status: 'lobby' },
    ]
    render(<Home {...defaultProps} onLeaveRoom={onLeaveRoom} activeRooms={activeRooms} />)
    fireEvent.click(screen.getByText('Leave'))
    expect(onLeaveRoom).toHaveBeenCalledWith('XYZ789')
  })
})
