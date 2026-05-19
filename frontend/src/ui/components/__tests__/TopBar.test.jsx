import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TopBar from '../TopBar.jsx'

const baseAuthed = {
  userEmail: 'alice@example.com',
  userDisplayName: 'Alice',
  userAvatarUrl: null,
  isAuthed: true,
  isGuest: false,
  onLogout: vi.fn(),
  onHome: vi.fn(),
}

function openMenu() {
  // The trigger is the avatar button (only one menu-toggle button in authed mode beyond the home logo).
  // The display name is rendered inside the trigger on >= sm screens; click that container's button.
  const trigger = screen.getByText('Alice').closest('button')
  fireEvent.click(trigger)
}

describe('TopBar — profile dropdown', () => {
  it('renders Game history entry when onHistory is provided', () => {
    render(<TopBar {...baseAuthed} onHistory={vi.fn()} />)
    openMenu()
    expect(screen.getByText(/Game history/i)).toBeTruthy()
  })

  it('does NOT render Game history entry when onHistory is undefined', () => {
    render(<TopBar {...baseAuthed} />)
    openMenu()
    expect(screen.queryByText(/Game history/i)).toBeNull()
  })

  it('calls onHistory and closes the menu when Game history is clicked', () => {
    const onHistory = vi.fn()
    render(<TopBar {...baseAuthed} onHistory={onHistory} />)
    openMenu()
    fireEvent.click(screen.getByText(/Game history/i))
    expect(onHistory).toHaveBeenCalledOnce()
    // Menu closes — Game history is no longer visible.
    expect(screen.queryByText(/Game history/i)).toBeNull()
  })

  it('does NOT show Game history for guest users (entry only on authed dropdown)', () => {
    render(<TopBar isAuthed={false} isGuest guestDisplayName="Guest42" onLogout={vi.fn()} onHistory={vi.fn()} />)
    // Open the guest dropdown
    fireEvent.click(screen.getByText('Guest42').closest('button'))
    expect(screen.queryByText(/Game history/i)).toBeNull()
  })

  it('renders the Friends entry when onFriends is provided', () => {
    render(<TopBar {...baseAuthed} onFriends={vi.fn()} />)
    openMenu()
    expect(screen.getByText(/^Friends$/)).toBeTruthy()
  })

  it('calls onFriends and closes the menu when Friends is clicked', () => {
    const onFriends = vi.fn()
    render(<TopBar {...baseAuthed} onFriends={onFriends} />)
    openMenu()
    fireEvent.click(screen.getByText(/^Friends$/))
    expect(onFriends).toHaveBeenCalledOnce()
    expect(screen.queryByText(/^Friends$/)).toBeNull()
  })

  it('does NOT render Friends entry for guests', () => {
    render(<TopBar isAuthed={false} isGuest guestDisplayName="Guest42" onLogout={vi.fn()} onFriends={vi.fn()} />)
    fireEvent.click(screen.getByText('Guest42').closest('button'))
    expect(screen.queryByText(/^Friends$/)).toBeNull()
  })

  it('renders the Leaderboard entry when onLeaderboard is provided', () => {
    render(<TopBar {...baseAuthed} onLeaderboard={vi.fn()} />)
    openMenu()
    expect(screen.getByText(/Leaderboard/i)).toBeTruthy()
  })

  it('calls onLeaderboard and closes the menu when Leaderboard is clicked', () => {
    const onLeaderboard = vi.fn()
    render(<TopBar {...baseAuthed} onLeaderboard={onLeaderboard} />)
    openMenu()
    fireEvent.click(screen.getByText(/Leaderboard/i))
    expect(onLeaderboard).toHaveBeenCalledOnce()
  })
})
