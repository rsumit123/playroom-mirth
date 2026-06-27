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
    rematchStatus: 'idle',
  },
  quickmatchJoin: vi.fn(),
  quickmatchRematchBot: vi.fn(),
  quickmatchRematchRequest: vi.fn(),
  quickmatchRematchCancel: vi.fn(),
  quickmatchReset: vi.fn(),
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
    mockApp.quickmatchRematchRequest.mockClear()
    mockApp.quickmatchRematchCancel.mockClear()
    mockApp.quickmatchReset.mockClear()
    mockApp.leaveRoom.mockClear()
    mockNavigate.mockClear()
    mockApp.quickmatch.isBot = false
    mockApp.quickmatch.rematchStatus = 'idle'
    mockApp.quickmatch.roomCode = 'QM001'
  })

  it('Rematch after a BOT match calls quickmatchRematchBot with old room_code (so server reuses same bot)', () => {
    mockApp.quickmatch.isBot = true
    renderPage()
    fireEvent.click(screen.getByText(/Rematch/i))
    expect(mockApp.quickmatchRematchBot).toHaveBeenCalledWith('science', 'QM001')
    expect(mockApp.quickmatchJoin).not.toHaveBeenCalled()
    expect(mockApp.leaveRoom).toHaveBeenCalledOnce()
    expect(mockNavigate).toHaveBeenCalledWith('/quickmatch')
  })

  it('Rematch after a HUMAN match sends a rematch_request and stays on GameEnd', () => {
    mockApp.quickmatch.isBot = false
    renderPage()
    fireEvent.click(screen.getByText(/Rematch/i))
    expect(mockApp.quickmatchRematchRequest).toHaveBeenCalledWith('QM001')
    expect(mockApp.quickmatchJoin).not.toHaveBeenCalled()
    expect(mockApp.quickmatchRematchBot).not.toHaveBeenCalled()
    expect(mockApp.leaveRoom).not.toHaveBeenCalled()
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('shows the Waiting state when rematchStatus is "waiting" and Cancel sends rematch_cancel', () => {
    mockApp.quickmatch.isBot = false
    mockApp.quickmatch.rematchStatus = 'waiting'
    renderPage()
    expect(screen.getByText(/Waiting for Priya/i)).toBeTruthy()
    fireEvent.click(screen.getByText(/^Cancel$/))
    expect(mockApp.quickmatchRematchCancel).toHaveBeenCalledWith('QM001')
  })

  it('navigates to /quickmatch when the rematch is accepted (new room_code arrives)', () => {
    mockApp.quickmatch.isBot = false
    mockApp.quickmatch.rematchStatus = 'waiting'
    mockApp.quickmatch.roomCode = 'QM999'  // new room code != room.code='QM001'
    renderPage()
    expect(mockApp.leaveRoom).toHaveBeenCalledOnce()
    expect(mockNavigate).toHaveBeenCalledWith('/quickmatch')
  })

  it('shows a "didn\'t want a rematch" inline notice when declined', () => {
    mockApp.quickmatch.isBot = false
    mockApp.quickmatch.rematchStatus = 'declined'
    renderPage()
    expect(screen.getByText(/didn't want a rematch/i)).toBeTruthy()
    expect(screen.getByText(/Find new opponent/i)).toBeTruthy()
  })

  it('New Opponent always goes to the picker, never the rematch shortcut', () => {
    mockApp.quickmatch.isBot = true
    renderPage()
    fireEvent.click(screen.getByText(/New Opponent/i))
    expect(mockApp.quickmatchRematchBot).not.toHaveBeenCalled()
    expect(mockApp.quickmatchJoin).not.toHaveBeenCalled()
    expect(mockNavigate).toHaveBeenCalledWith('/quickmatch')
  })

  it('New Opponent resets quickmatch state so the category picker shows (not stale MatchFoundSplash)', () => {
    renderPage()
    fireEvent.click(screen.getByText(/New Opponent/i))
    expect(mockApp.quickmatchReset).toHaveBeenCalledOnce()
  })

  it('Home ALSO resets quickmatch state (regression: tapping Quick Play later was matching the same bot instantly + getting stuck on the trivia screen)', () => {
    mockApp.quickmatch.isBot = true
    renderPage()
    fireEvent.click(screen.getByText(/🏠 Home/i))
    expect(mockApp.leaveRoom).toHaveBeenCalledOnce()
    expect(mockApp.quickmatchReset).toHaveBeenCalledOnce()
    expect(mockNavigate).toHaveBeenCalledWith('/home')
  })
})
