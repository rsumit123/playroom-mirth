import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import QuickMatchFlowPage from '../QuickMatchFlowPage.jsx'

const mockApp = {
  quickmatch: { status: 'idle', category: null, opponentName: null, roomCode: null, waitSeconds: 15 },
  quickmatchJoin: vi.fn(),
  quickmatchCancel: vi.fn(),
  quickmatchReady: vi.fn(),
  quickmatchReset: vi.fn(),
  bindLobbyEvents: vi.fn(),
  startGameSocket: vi.fn(),
}

vi.mock('../../../state/AppContext.jsx', () => ({
  useApp: () => mockApp,
}))

function renderPage() {
  return render(
    <MemoryRouter>
      <QuickMatchFlowPage />
    </MemoryRouter>
  )
}

describe('QuickMatchFlowPage', () => {
  beforeEach(() => {
    for (const fn of [mockApp.quickmatchJoin, mockApp.quickmatchCancel, mockApp.quickmatchReady, mockApp.quickmatchReset, mockApp.bindLobbyEvents, mockApp.startGameSocket]) {
      fn.mockClear()
    }
    mockApp.quickmatch = { status: 'idle', category: null, opponentName: null, roomCode: null, waitSeconds: 15 }
  })

  it('auto-joins with "surprise" category on idle landing (no picker step)', () => {
    renderPage()
    expect(mockApp.quickmatchJoin).toHaveBeenCalledWith('surprise')
  })

  it('renders the search screen as the default surface (idle still shows searching UI)', () => {
    const { container } = renderPage()
    expect(container.textContent).toMatch(/Finding a player/i)
  })

  it('renders the search screen when searching', () => {
    mockApp.quickmatch = { ...mockApp.quickmatch, status: 'searching', waitSeconds: 15 }
    const { container } = renderPage()
    expect(container.textContent).toMatch(/Finding a player/i)
  })

  it('renders the match-found splash + binds listeners when matched arrives MID-SESSION (searching → matched)', () => {
    // Normal flow: mount in `searching`, then state transitions to `matched`.
    mockApp.quickmatch = { ...mockApp.quickmatch, status: 'searching' }
    const { container, rerender } = render(
      <MemoryRouter><QuickMatchFlowPage /></MemoryRouter>
    )
    // Simulate the server's `quickmatch:matched` event arriving.
    mockApp.quickmatch = { ...mockApp.quickmatch, status: 'matched', opponentName: 'Priya', roomCode: 'QM123' }
    rerender(<MemoryRouter><QuickMatchFlowPage /></MemoryRouter>)
    expect(container.textContent).toMatch(/MATCH FOUND/i)
    expect(mockApp.bindLobbyEvents).toHaveBeenCalledWith('QM123')
    expect(mockApp.startGameSocket).toHaveBeenCalledTimes(1)
    expect(mockApp.quickmatchReady).toHaveBeenCalledWith('QM123')
    // And we did NOT wipe state — this is a legitimate match, not stale carry-over.
    expect(mockApp.quickmatchReset).not.toHaveBeenCalled()
  })

  it('WIPES stale `matched` state on mount (regression: Home from GameEnd → Quick Play again was matching the same bot instantly)', () => {
    // User played a bot game, clicked Home (which previously didn't reset
    // quickmatch state), looked at leaderboard, came back to Quick Play.
    // Landing here with `matched` from the prior game is always stale.
    mockApp.quickmatch = {
      status: 'matched', category: 'science',
      opponentName: 'Vivaan', roomCode: 'OLD123',
      waitSeconds: 15, isBot: true,
    }
    const { container } = renderPage()
    expect(mockApp.quickmatchReset).toHaveBeenCalledOnce()
    // Critically: must NOT render the splash with the stale opponent name.
    expect(container.textContent).not.toMatch(/MATCH FOUND/i)
    expect(container.textContent).not.toMatch(/Vivaan/i)
    // And must NOT try to bind against the dead room — that's how the user
    // ended up stuck on "waiting for question" on the trivia screen.
    expect(mockApp.bindLobbyEvents).not.toHaveBeenCalledWith('OLD123')
    expect(mockApp.quickmatchReady).not.toHaveBeenCalledWith('OLD123')
  })

  it('does NOT bind game listeners while only searching', () => {
    mockApp.quickmatch = { ...mockApp.quickmatch, status: 'searching' }
    renderPage()
    expect(mockApp.bindLobbyEvents).not.toHaveBeenCalled()
    expect(mockApp.startGameSocket).not.toHaveBeenCalled()
    expect(mockApp.quickmatchReady).not.toHaveBeenCalled()
  })
})
