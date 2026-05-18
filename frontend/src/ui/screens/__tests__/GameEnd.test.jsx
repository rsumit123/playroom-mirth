import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import GameEnd from '../GameEnd.jsx'

describe('GameEnd — quickmatch additions', () => {
  it('shows "You Win!" when self is winner_player_id', () => {
    render(
      <GameEnd
        scores={{ 1: 1450, 2: 1120 }}
        playerNames={{ 1: 'You', 2: 'Priya' }}
        selfPlayerId={1}
        winnerPlayerId={1}
        origin="quickmatch"
        onHome={vi.fn()}
        onRematch={vi.fn()}
        onNewOpponent={vi.fn()}
      />
    )
    expect(screen.getByText(/You Win/i)).toBeTruthy()
  })

  it('shows "You Lost" when self is not the winner', () => {
    render(
      <GameEnd
        scores={{ 1: 100, 2: 200 }}
        playerNames={{ 1: 'You', 2: 'Priya' }}
        selfPlayerId={1}
        winnerPlayerId={2}
        origin="quickmatch"
        onHome={vi.fn()}
        onRematch={vi.fn()}
        onNewOpponent={vi.fn()}
      />
    )
    expect(screen.getByText(/You Lost/i)).toBeTruthy()
  })

  it('shows Rematch + New Opponent for quickmatch games', () => {
    render(
      <GameEnd
        scores={{ 1: 100, 2: 200 }}
        playerNames={{ 1: 'You', 2: 'Priya' }}
        selfPlayerId={1}
        winnerPlayerId={2}
        origin="quickmatch"
        onHome={vi.fn()}
        onRematch={vi.fn()}
        onNewOpponent={vi.fn()}
      />
    )
    expect(screen.getByText(/Rematch/i)).toBeTruthy()
    expect(screen.getByText(/New Opponent/i)).toBeTruthy()
  })

  it('hides Rematch + New Opponent for friends games', () => {
    render(
      <GameEnd
        scores={{ 1: 100, 2: 200 }}
        playerNames={{ 1: 'You', 2: 'Friend' }}
        selfPlayerId={1}
        origin="friends"
        onHome={vi.fn()}
      />
    )
    expect(screen.queryByText(/Rematch/i)).toBeNull()
    expect(screen.queryByText(/New Opponent/i)).toBeNull()
  })
})
