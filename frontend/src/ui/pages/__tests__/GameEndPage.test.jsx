import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, fireEvent, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import GameEndPage from '../GameEndPage.jsx'

const mockApp = {
  game: { scores: { 1: 100, 2: 50 }, gameEnd: { winner_player_id: 1 } },
  lobby: { players: [{ id: 1, display_name: 'You' }, { id: 2, display_name: 'Priya' }] },
  room: { code: 'QM001' },
  selfPlayerId: 1,
  leaveRoom: vi.fn(),
  emitPlayAgain: vi.fn(),
  quickmatch: {
    status: 'idle',
    category: 'science',
    opponentName: 'Priya',
    roomCode: 'QM001',
    waitSeconds: 15,
    isBot: false,
  },
  quickmatchJoin: vi.fn(),
  quickmatchRematchBot: vi.fn(),
}

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../../state/AppContext.jsx', () => ({
  useApp: () => mockApp,
}))

function renderPage() {
  return render(
    <MemoryRouter>
      <GameEndPage />
    </MemoryRouter>
  )
}

describe('GameEndPage — quickmatch rematch routing', () => {
  beforeEach(() => {
    mockApp.quickmatchJoin.mockClear()
    mockApp.quickmatchRematchBot.mockClear()
    mockApp.leaveRoom.mockClear()
    mockNavigate.mockClear()
    mockApp.quickmatch.isBot = false
  })

  it('Rematch after a BOT match calls quickmatchRematchBot (instant — no 15s queue)', () => {
    mockApp.quickmatch.isBot = true
    renderPage()
    fireEvent.click(screen.getByText(/Rematch/i))
    expect(mockApp.quickmatchRematchBot).toHaveBeenCalledWith('science')
    expect(mockApp.quickmatchJoin).not.toHaveBeenCalled()
    expect(mockApp.leaveRoom).toHaveBeenCalledOnce()
    expect(mockNavigate).toHaveBeenCalledWith('/quickmatch')
  })

  it('Rematch after a HUMAN match falls back to the normal queue', () => {
    mockApp.quickmatch.isBot = false
    renderPage()
    fireEvent.click(screen.getByText(/Rematch/i))
    expect(mockApp.quickmatchJoin).toHaveBeenCalledWith('science')
    expect(mockApp.quickmatchRematchBot).not.toHaveBeenCalled()
  })

  it('New Opponent always goes to the picker, never the rematch shortcut', () => {
    mockApp.quickmatch.isBot = true
    renderPage()
    fireEvent.click(screen.getByText(/New Opponent/i))
    expect(mockApp.quickmatchRematchBot).not.toHaveBeenCalled()
    expect(mockApp.quickmatchJoin).not.toHaveBeenCalled()
    expect(mockNavigate).toHaveBeenCalledWith('/quickmatch')
  })
})
