import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import QuickMatchFlowPage from '../QuickMatchFlowPage.jsx'

const mockApp = {
  quickmatch: { status: 'idle', category: null, opponentName: null, roomCode: null, waitSeconds: 15 },
  quickmatchJoin: vi.fn(),
  quickmatchCancel: vi.fn(),
  quickmatchReady: vi.fn(),
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
    for (const fn of [mockApp.quickmatchJoin, mockApp.quickmatchCancel, mockApp.quickmatchReady, mockApp.bindLobbyEvents, mockApp.startGameSocket]) {
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

  it('renders the match-found splash when matched', () => {
    mockApp.quickmatch = { ...mockApp.quickmatch, status: 'matched', opponentName: 'Priya', roomCode: 'QM123' }
    const { container } = renderPage()
    expect(container.textContent).toMatch(/MATCH FOUND/i)
  })

  it('on matched: binds BOTH lobby AND game listeners + sends ready', () => {
    mockApp.quickmatch = { ...mockApp.quickmatch, status: 'matched', opponentName: 'Priya', roomCode: 'QM123' }
    renderPage()
    // Without startGameSocket, game:game_end never reaches the frontend and the
    // GameEnd screen never shows after the bot finishes the 10 questions.
    expect(mockApp.bindLobbyEvents).toHaveBeenCalledWith('QM123')
    expect(mockApp.startGameSocket).toHaveBeenCalledTimes(1)
    expect(mockApp.quickmatchReady).toHaveBeenCalledWith('QM123')
  })

  it('does NOT bind game listeners while only searching', () => {
    mockApp.quickmatch = { ...mockApp.quickmatch, status: 'searching' }
    renderPage()
    expect(mockApp.bindLobbyEvents).not.toHaveBeenCalled()
    expect(mockApp.startGameSocket).not.toHaveBeenCalled()
    expect(mockApp.quickmatchReady).not.toHaveBeenCalled()
  })
})
