import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import HistoryScreen from '../HistoryScreen.jsx'

const baseStats = {
  total_games: 7, total_wins: 4,
  by_game_type: [
    { game_type: 'trivia', origin: 'quickmatch', games_played: 5, wins: 3, losses: 2 },
    { game_type: 'charades', origin: 'friends', games_played: 2, wins: 1, losses: 1 },
  ],
  by_origin: { quickmatch: 5, friends: 2 },
}

const baseRows = [
  { id: 1, game_type: 'trivia', score: 1450, player_count: 2, is_winner: true, played_at: new Date(Date.now() - 60_000).toISOString(), room_code: 'AAA', origin: 'quickmatch' },
  { id: 2, game_type: 'charades', score: 0, player_count: 4, is_winner: false, played_at: new Date(Date.now() - 86_400_000).toISOString(), room_code: 'BBB', origin: 'friends' },
]

function renderScreen(overrides = {}) {
  const props = {
    tab: 'all',
    onTabChange: vi.fn(),
    stats: baseStats,
    rows: baseRows,
    loading: false,
    loadingMore: false,
    hasMore: false,
    onLoadMore: vi.fn(),
    onBack: vi.fn(),
    ...overrides,
  }
  const utils = render(<HistoryScreen {...props} />)
  return { ...utils, props }
}

describe('HistoryScreen', () => {
  it('renders the 3 tabs (All, Quick Play, Friends)', () => {
    renderScreen()
    expect(screen.getByText('All')).toBeTruthy()
    expect(screen.getByText('Quick Play')).toBeTruthy()
    expect(screen.getByText('Friends')).toBeTruthy()
  })

  it('renders the stats summary (games, wins, win-rate, per-game breakdown)', () => {
    renderScreen()
    expect(screen.getByText('7')).toBeTruthy() // total games
    expect(screen.getByText('4')).toBeTruthy() // total wins
    expect(screen.getByText('57%')).toBeTruthy() // win rate
    // Both the stats card and the row list mention game names.
    expect(screen.getAllByText(/Trivia/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Charades/i).length).toBeGreaterThan(0)
  })

  it('renders each game row with score and win/loss state', () => {
    const { container } = renderScreen()
    // Score values appear
    expect(container.textContent).toContain('1450')
    expect(container.textContent).toContain('Win')
    expect(container.textContent).toContain('Loss')
  })

  it('marks quickmatch rows with a Quick badge', () => {
    renderScreen()
    expect(screen.getByText(/^Quick$/)).toBeTruthy()
  })

  it('switches tab when a tab button is clicked', () => {
    const onTabChange = vi.fn()
    renderScreen({ onTabChange })
    fireEvent.click(screen.getByText('Quick Play'))
    expect(onTabChange).toHaveBeenCalledWith('quickmatch')
  })

  it('renders empty state when there are no rows', () => {
    renderScreen({ rows: [] })
    expect(screen.getByText(/No games yet/i)).toBeTruthy()
  })

  it('shows Load more button when hasMore is true', () => {
    const onLoadMore = vi.fn()
    renderScreen({ hasMore: true, onLoadMore })
    fireEvent.click(screen.getByText(/Load more/i))
    expect(onLoadMore).toHaveBeenCalledOnce()
  })

  it('disables Load more while loadingMore', () => {
    renderScreen({ hasMore: true, loadingMore: true })
    const btn = screen.getByText(/Loading/i).closest('button')
    expect(btn.disabled).toBe(true)
  })

  it('shows skeleton loading state when loading with no rows', () => {
    const { container } = renderScreen({ loading: true, rows: [] })
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
  })

  it('calls onBack when back button is clicked', () => {
    const onBack = vi.fn()
    renderScreen({ onBack })
    fireEvent.click(screen.getByText(/Back/i))
    expect(onBack).toHaveBeenCalledOnce()
  })

  it('handles stats=null gracefully (skeleton, no crash)', () => {
    renderScreen({ stats: null })
    // Did not throw; renders something
    expect(document.querySelector('.card')).toBeTruthy()
  })
})
