import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import InviteFriendsDrawer from '../InviteFriendsDrawer.jsx'

const friends = [
  { id: 1, display_name: 'Alice', is_online: true },
  { id: 2, display_name: 'Bob', is_online: false },
]

describe('InviteFriendsDrawer', () => {
  it('renders nothing when closed', () => {
    const { container } = render(
      <InviteFriendsDrawer open={false} friends={friends} onInvite={vi.fn()} onClose={vi.fn()} />
    )
    expect(container.innerHTML).toBe('')
  })

  it('renders friends when open', () => {
    render(<InviteFriendsDrawer open={true} friends={friends} onInvite={vi.fn()} onClose={vi.fn()} />)
    expect(screen.getByText('Alice')).toBeTruthy()
    expect(screen.getByText('Bob')).toBeTruthy()
  })

  it('shows online and offline sections', () => {
    render(<InviteFriendsDrawer open={true} friends={friends} onInvite={vi.fn()} onClose={vi.fn()} />)
    expect(screen.getByText(/online \(1\)/i)).toBeTruthy()
    expect(screen.getByText(/offline \(1\)/i)).toBeTruthy()
  })

  it('shows Invite button for both online and offline friends', () => {
    render(<InviteFriendsDrawer open={true} friends={friends} onInvite={vi.fn()} onClose={vi.fn()} />)
    const inviteButtons = screen.getAllByText('Invite')
    expect(inviteButtons.length).toBe(2)
  })

  it('shows Invited after clicking Invite', async () => {
    const onInvite = vi.fn().mockResolvedValue(undefined)
    render(<InviteFriendsDrawer open={true} friends={friends} onInvite={onInvite} onClose={vi.fn()} />)

    const inviteButtons = screen.getAllByText('Invite')
    fireEvent.click(inviteButtons[0])

    await waitFor(() => {
      expect(onInvite).toHaveBeenCalledWith(1)
      expect(screen.getByText('Invited')).toBeTruthy()
    })
  })

  it('resets invited state on close → open transition', async () => {
    const onInvite = vi.fn().mockResolvedValue(undefined)
    const { rerender } = render(
      <InviteFriendsDrawer open={true} friends={friends} onInvite={onInvite} onClose={vi.fn()} />
    )

    // Invite Alice
    fireEvent.click(screen.getAllByText('Invite')[0])
    await waitFor(() => expect(screen.getByText('Invited')).toBeTruthy())

    // Close drawer
    rerender(<InviteFriendsDrawer open={false} friends={friends} onInvite={onInvite} onClose={vi.fn()} />)

    // Reopen -- should reset invited state
    rerender(<InviteFriendsDrawer open={true} friends={friends} onInvite={onInvite} onClose={vi.fn()} />)

    // Both should show Invite buttons again (not "Invited")
    const freshButtons = screen.getAllByText('Invite')
    expect(freshButtons.length).toBe(2)
  })

  it('does NOT reset invited state on re-render while open', async () => {
    const onInvite = vi.fn().mockResolvedValue(undefined)
    const { rerender } = render(
      <InviteFriendsDrawer open={true} friends={friends} onInvite={onInvite} onClose={vi.fn()} />
    )

    // Invite Alice
    fireEvent.click(screen.getAllByText('Invite')[0])
    await waitFor(() => expect(screen.getByText('Invited')).toBeTruthy())

    // Re-render while still open (e.g., parent state change)
    rerender(<InviteFriendsDrawer open={true} friends={friends} onInvite={onInvite} onClose={vi.fn()} />)

    // Alice should still show "Invited" (not reset)
    expect(screen.getByText('Invited')).toBeTruthy()
  })

  it('shows empty state when no friends', () => {
    render(<InviteFriendsDrawer open={true} friends={[]} onInvite={vi.fn()} onClose={vi.fn()} />)
    expect(screen.getByText(/add friends/i)).toBeTruthy()
  })

  it('calls onClose when backdrop is clicked', () => {
    const onClose = vi.fn()
    const { container } = render(
      <InviteFriendsDrawer open={true} friends={friends} onInvite={vi.fn()} onClose={onClose} />
    )
    // Click the backdrop (first child is the overlay div)
    fireEvent.click(container.firstChild)
    expect(onClose).toHaveBeenCalledOnce()
  })
})
