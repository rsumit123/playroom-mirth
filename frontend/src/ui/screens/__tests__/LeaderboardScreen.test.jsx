import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import LeaderboardScreen from '../LeaderboardScreen.jsx'

const baseData = {
  top: [
    { rank: 1, user_id: 100, display_name: 'Top Player', avatar_url: null, wins: 42, games_played: 60 },
    { rank: 2, user_id: 101, display_name: 'Runner Up', avatar_url: null, wins: 38, games_played: 55 },
    { rank: 3, user_id: 102, display_name: 'Bronze',    avatar_url: null, wins: 20, games_played: 30 },
    { rank: 4, user_id: 103, display_name: 'Fourth',    avatar_url: null, wins: 12, games_played: 25 },
  ],
  you: null,
  current_streak: 0,
}

function renderScreen(overrides = {}) {
  const props = { data: baseData, loading: false, onBack: vi.fn(), currentUserId: 999, ...overrides }
  return render(<LeaderboardScreen {...props} />)
}

describe('LeaderboardScreen', () => {
  it('renders title and back chip on separate lines (mobile-friendly header)', () => {
    renderScreen()
    expect(screen.getByText(/Leaderboard/i)).toBeTruthy()
    expect(screen.getByText(/Back/i)).toBeTruthy()
  })

  it('renders each top entry with rank, name, and wins', () => {
    renderScreen()
    expect(screen.getByText('Top Player')).toBeTruthy()
    expect(screen.getByText('Runner Up')).toBeTruthy()
    expect(screen.getByText('Bronze')).toBeTruthy()
    expect(screen.getByText('Fourth')).toBeTruthy()
    expect(screen.getByText('42')).toBeTruthy()
    expect(screen.getByText('38')).toBeTruthy()
  })

  it('shows win-rate context for each entry', () => {
    const { container } = renderScreen()
    // 42 / 60 = 70%, 38/55 ≈ 69%, 20/30 ≈ 67%, 12/25 = 48%
    expect(container.textContent).toContain('70% win rate')
    expect(container.textContent).toContain('48% win rate')
  })

  it('highlights the caller row when their user_id matches an entry', () => {
    const { container } = renderScreen({ currentUserId: 100 })
    // The accent ring style is applied to the caller row.
    const accentRow = container.querySelector('.ring-accent\\/20')
    expect(accentRow).toBeTruthy()
    expect(accentRow.textContent).toContain('Top Player')
    expect(accentRow.textContent.toLowerCase()).toContain('you')
  })

  it('shows the "Your rank" pin only when data.you is set (caller outside top)', () => {
    renderScreen({
      data: { ...baseData, you: { rank: 47, user_id: 999, display_name: 'Outsider', avatar_url: null, wins: 5, games_played: 12 } },
      currentUserId: 999,
    })
    expect(screen.getByText(/Your rank/i)).toBeTruthy()
    expect(screen.getByText('Outsider')).toBeTruthy()
    expect(screen.getByText('47')).toBeTruthy()
  })

  it('does NOT show the "Your rank" pin when data.you is null (caller is in top)', () => {
    renderScreen()
    expect(screen.queryByText(/Your rank/i)).toBeNull()
  })

  it('shows a streak card when current_streak >= 2', () => {
    renderScreen({ data: { ...baseData, current_streak: 4 } })
    expect(screen.getByText(/4-win streak/i)).toBeTruthy()
  })

  it('hides the streak card when streak is 0 or 1', () => {
    renderScreen({ data: { ...baseData, current_streak: 1 } })
    expect(screen.queryByText(/-win streak/i)).toBeNull()
  })

  it('renders skeleton state while loading', () => {
    const { container } = renderScreen({ data: null, loading: true })
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
  })

  it('renders empty state when no data', () => {
    renderScreen({ data: { top: [], you: null, current_streak: 0 }, loading: false })
    expect(screen.getByText(/No one has played yet/i)).toBeTruthy()
  })

  it('calls onBack when back chip is clicked', () => {
    const onBack = vi.fn()
    renderScreen({ onBack })
    fireEvent.click(screen.getByText(/Back/i))
    expect(onBack).toHaveBeenCalledOnce()
  })
})
