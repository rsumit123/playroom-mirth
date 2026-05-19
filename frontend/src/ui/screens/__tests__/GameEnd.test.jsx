import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
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

  it('shows softened "Good game!" headline when self is not the winner (instead of harsh "You Lost")', () => {
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
    expect(screen.getByText(/Good game/i)).toBeTruthy()
    expect(screen.queryByText(/You Lost/i)).toBeNull()
  })

  it('shows the score margin under the headline (loss case)', () => {
    render(
      <GameEnd
        scores={{ 1: 100, 2: 250 }}
        playerNames={{ 1: 'You', 2: 'Priya' }}
        selfPlayerId={1}
        winnerPlayerId={2}
        origin="quickmatch"
        onHome={vi.fn()}
        onRematch={vi.fn()}
        onNewOpponent={vi.fn()}
      />
    )
    expect(screen.getByText(/Priya won by 150 pts/i)).toBeTruthy()
  })

  it('shows "You won by N pts" under the headline (win case)', () => {
    render(
      <GameEnd
        scores={{ 1: 1450, 2: 1300 }}
        playerNames={{ 1: 'You', 2: 'Priya' }}
        selfPlayerId={1}
        winnerPlayerId={1}
        origin="quickmatch"
        onHome={vi.fn()}
        onRematch={vi.fn()}
        onNewOpponent={vi.fn()}
      />
    )
    expect(screen.getByText(/You won by 150 pts/i)).toBeTruthy()
  })

  it('shows a streak badge on a win when currentStreak >= 2', () => {
    render(
      <GameEnd
        scores={{ 1: 200, 2: 100 }}
        playerNames={{ 1: 'You', 2: 'Priya' }}
        selfPlayerId={1}
        winnerPlayerId={1}
        origin="quickmatch"
        currentStreak={3}
        onHome={vi.fn()}
        onRematch={vi.fn()}
        onNewOpponent={vi.fn()}
      />
    )
    expect(screen.getByText(/3-win streak/i)).toBeTruthy()
  })

  it('does NOT show a streak badge on a loss even with a streak count', () => {
    render(
      <GameEnd
        scores={{ 1: 100, 2: 200 }}
        playerNames={{ 1: 'You', 2: 'Priya' }}
        selfPlayerId={1}
        winnerPlayerId={2}
        origin="quickmatch"
        currentStreak={3}
        onHome={vi.fn()}
        onRematch={vi.fn()}
        onNewOpponent={vi.fn()}
      />
    )
    expect(screen.queryByText(/-win streak/i)).toBeNull()
  })

  it('renders a Share button on wins when onShare is provided', () => {
    const onShare = vi.fn()
    render(
      <GameEnd
        scores={{ 1: 200, 2: 100 }}
        playerNames={{ 1: 'You', 2: 'Priya' }}
        selfPlayerId={1}
        winnerPlayerId={1}
        origin="quickmatch"
        onShare={onShare}
        onHome={vi.fn()}
        onRematch={vi.fn()}
        onNewOpponent={vi.fn()}
      />
    )
    const btn = screen.getByLabelText(/share your win/i)
    expect(btn).toBeTruthy()
    fireEvent.click(btn)
    expect(onShare).toHaveBeenCalledOnce()
  })

  it('does NOT render the Share button on a loss', () => {
    render(
      <GameEnd
        scores={{ 1: 100, 2: 200 }}
        playerNames={{ 1: 'You', 2: 'Priya' }}
        selfPlayerId={1}
        winnerPlayerId={2}
        origin="quickmatch"
        onShare={vi.fn()}
        onHome={vi.fn()}
        onRematch={vi.fn()}
        onNewOpponent={vi.fn()}
      />
    )
    expect(screen.queryByLabelText(/share your win/i)).toBeNull()
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
