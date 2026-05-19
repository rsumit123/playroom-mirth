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
  return { ...render(<HistoryScreen {...props} />), props }
}

describe('HistoryScreen', () => {
  it('renders the back chip and title on separate lines (mobile-friendly header)', () => {
    renderScreen()
    const back = screen.getByText(/Back/i)
    const title = screen.getByText('Game History')
    expect(back).toBeTruthy()
    expect(title).toBeTruthy()
    // Title should not be inside the back button (overlap regression check).
    expect(back.closest('button')).not.toBe(title.closest('button'))
  })

  it('renders the 3 filter tabs', () => {
    renderScreen()
    expect(screen.getByText('All')).toBeTruthy()
    expect(screen.getByText('Quick Play')).toBeTruthy()
    expect(screen.getByText('Friends')).toBeTruthy()
  })

  it('renders headline totals (games / wins / win-rate)', () => {
    renderScreen()
    expect(screen.getByText('7')).toBeTruthy()
    expect(screen.getByText('4')).toBeTruthy()
    expect(screen.getByText('57%')).toBeTruthy()
  })

  it('renders one tile per game type (collapsing across origins)', () => {
    renderScreen()
    // Two game types in stats -> two tiles. Headers appear once each in the stats grid.
    // (The row list also mentions "Trivia"/"Charades", but those are separate from the tiles.)
    const trivia = screen.getAllByText(/^Trivia$/)
    const charades = screen.getAllByText(/^Charades$/)
    expect(trivia.length).toBeGreaterThanOrEqual(1)
    expect(charades.length).toBeGreaterThanOrEqual(1)
  })

  it('collapses same game_type across origins into a single tile (stats summary)', () => {
    const stats = {
      total_games: 8, total_wins: 4,
      by_game_type: [
        { game_type: 'trivia', origin: 'quickmatch', games_played: 5, wins: 3, losses: 2 },
        { game_type: 'trivia', origin: 'friends', games_played: 3, wins: 1, losses: 2 },
      ],
      by_origin: { quickmatch: 5, friends: 3 },
    }
    const { container } = renderScreen({ stats, rows: [] })
    // Only ONE Trivia tile in the grid (stats tiles), even though by_game_type has two rows.
    const tiles = container.querySelectorAll('.grid.grid-cols-2 .card-flat')
    expect(tiles.length).toBe(1)
    // Combined: 8 played, 4W 4L
    expect(container.textContent).toContain('8 played')
    expect(container.textContent).toContain('4W')
    expect(container.textContent).toContain('4L')
  })

  it('renders each match row with score + win/loss state', () => {
    const { container } = renderScreen()
    expect(container.textContent).toContain('1450')
    expect(container.textContent).toMatch(/Loss/i)
  })

  it('marks quickmatch match-rows with a Quick badge', () => {
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

  it('handles stats=null gracefully (skeleton totals, no game-type tiles, no crash)', () => {
    const { container } = renderScreen({ stats: null })
    // Skeletons exist
    expect(container.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0)
    // No game-type tiles when stats is null
    expect(container.querySelector('.grid.grid-cols-2 .card-flat')).toBeNull()
  })
})
