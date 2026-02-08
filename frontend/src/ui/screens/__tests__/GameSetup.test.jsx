import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import GameSetup from '../GameSetup.jsx'

describe('GameSetup', () => {
  const defaultProps = {
    gameType: 'charades',
    onCreate: vi.fn(),
    onJoin: vi.fn(),
    onBack: vi.fn(),
    loadingCreate: false,
    loadingJoin: false,
  }

  it('renders the Create Room and Join Room tabs', () => {
    render(<GameSetup {...defaultProps} />)
    // There are two tab buttons plus the submit "Create Room" button
    const createButtons = screen.getAllByText('Create Room')
    expect(createButtons.length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Join Room')).toBeInTheDocument()
  })

  it('shows the game type label (Charades)', () => {
    render(<GameSetup {...defaultProps} gameType="charades" />)
    expect(screen.getByText('Charades')).toBeInTheDocument()
  })

  it('shows the game type label (Scribble)', () => {
    render(<GameSetup {...defaultProps} gameType="scribble" />)
    expect(screen.getByText('Scribble')).toBeInTheDocument()
  })

  it('passes game_type in the onCreate payload', () => {
    const onCreate = vi.fn()
    render(<GameSetup {...defaultProps} gameType="scribble" onCreate={onCreate} />)
    // Click the "Create Room" submit button (last one with that text)
    const createButtons = screen.getAllByText('Create Room')
    fireEvent.click(createButtons[createButtons.length - 1])
    expect(onCreate).toHaveBeenCalledTimes(1)
    const payload = onCreate.mock.calls[0][0]
    expect(payload.game_type).toBe('scribble')
    expect(payload).toHaveProperty('rounds_total')
    expect(payload).toHaveProperty('difficulty')
    expect(payload).toHaveProperty('turn_seconds')
    expect(payload).toHaveProperty('max_players')
  })

  it('switches to join tab and shows room code input', () => {
    render(<GameSetup {...defaultProps} />)
    // Click the "Join Room" tab
    fireEvent.click(screen.getByText('Join Room'))
    expect(screen.getByPlaceholderText('ABCDEF')).toBeInTheDocument()
  })

  it('calls onJoin with the entered room code', () => {
    const onJoin = vi.fn()
    render(<GameSetup {...defaultProps} onJoin={onJoin} />)
    // Switch to join tab
    fireEvent.click(screen.getByText('Join Room'))
    const input = screen.getByPlaceholderText('ABCDEF')
    fireEvent.change(input, { target: { value: 'xyz123' } })
    // The component uppercases the value
    // Click the Join Room submit button (last one)
    const joinButtons = screen.getAllByText('Join Room')
    fireEvent.click(joinButtons[joinButtons.length - 1])
    expect(onJoin).toHaveBeenCalledWith('XYZ123')
  })

  it('calls onBack when back button is clicked', () => {
    const onBack = vi.fn()
    render(<GameSetup {...defaultProps} onBack={onBack} />)
    fireEvent.click(screen.getByText(/Back/))
    expect(onBack).toHaveBeenCalledTimes(1)
  })
})
