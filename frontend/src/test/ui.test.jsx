import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Home from '../ui/screens/Home.jsx'
import Game from '../ui/screens/Game.jsx'
import Lobby from '../ui/screens/Lobby.jsx'
import RoundEnd from '../ui/screens/RoundEnd.jsx'
import GameEnd from '../ui/screens/GameEnd.jsx'
import AdminWordsPage from '../ui/pages/AdminWordsPage.jsx'
import TopBar from '../ui/components/TopBar.jsx'
import { AppProvider } from '../state/AppContext.jsx'

describe('UI screens', () => {
  it('renders Home game selector and triggers onSelectGame', () => {
    const onSelectGame = vi.fn()
    render(<Home onSelectGame={onSelectGame} onRejoin={() => {}} onLeaveRoom={() => {}} />)

    expect(screen.getByText('Charades')).toBeInTheDocument()
    expect(screen.getByText('Scribble')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Charades'))
    expect(onSelectGame).toHaveBeenCalledWith('charades')
  })

  it('shows correct guess banner when lastGuess is set', () => {
    const game = { lastGuess: { word: 'umbrella' }, turn: { turn_seconds: 60 }, selfPlayerId: 2 }
    render(<Game game={game} onSend={() => {}} onRejoin={() => {}} />)
    expect(screen.getByText(/guessed/)).toBeInTheDocument()
    expect(screen.getByText(/umbrella/)).toBeInTheDocument()
  })

  it('renders chat messages from game state', () => {
    const game = { messages: [{ player_id: 1, message: 'hello' }], turn: { turn_seconds: 60 }, selfPlayerId: 2 }
    render(<Game game={game} onSend={() => {}} onRejoin={() => {}} />)
    expect(screen.getByText('Player 1')).toBeInTheDocument()
    expect(screen.getByText('hello')).toBeInTheDocument()
  })

  it('renders scoreboard entries', () => {
    const game = { scores: { 1: 10, 2: 5 }, turn: { turn_seconds: 60 }, selfPlayerId: 2 }
    render(<Game game={game} onSend={() => {}} onRejoin={() => {}} />)
    expect(screen.getAllByText('Player 1').length).toBeGreaterThan(0)
    expect(screen.getAllByText('10').length).toBeGreaterThan(0)
  })

  it('renders lobby settings for host', () => {
    const lobby = {
      room: { rounds_total: 2, difficulty: 1, turn_seconds: 45, game_type: 'charades' },
      players: [],
      host_player_id: 1
    }
    const onSaveSettings = vi.fn()
    render(<Lobby lobby={lobby} onStart={() => {}} onLeave={() => {}} onSaveSettings={onSaveSettings} selfPlayerId={1} />)
    expect(screen.getByText('Game Settings')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Save Settings'))
    expect(onSaveSettings).toHaveBeenCalled()
  })

  it('shows reconnect banner when reconnecting', () => {
    const game = { reconnecting: true, turn: { turn_seconds: 60 }, selfPlayerId: 2 }
    render(<Game game={game} onSend={() => {}} onRejoin={() => {}} />)
    expect(screen.getByText('Reconnecting...')).toBeInTheDocument()
  })

  it('renders share and copy buttons in lobby', () => {
    const lobby = { room: { rounds_total: 2, difficulty: 1, turn_seconds: 45 }, players: [] }
    render(<Lobby lobby={lobby} onStart={() => {}} onLeave={() => {}} />)
    expect(screen.getAllByText('Copy').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Share').length).toBeGreaterThan(0)
  })

  it('shows game in progress alert for active rooms', () => {
    const lobby = {
      room: { rounds_total: 2, difficulty: 1, turn_seconds: 45, status: 'active' },
      players: [{ id: 1, user_id: null, in_game: false }]
    }
    render(<Lobby lobby={lobby} onStart={() => {}} onLeave={() => {}} selfPlayerId={1} />)
    expect(screen.getByText('Game in progress')).toBeInTheDocument()
  })

  it('renders round end scoreboard', () => {
    render(<RoundEnd scores={{ 1: 8, 2: 3 }} onContinue={() => {}} />)
    expect(screen.getAllByText('Player 1').length).toBeGreaterThan(0)
    expect(screen.getByText('Leaderboard')).toBeInTheDocument()
  })

  it('renders game end scoreboard', () => {
    render(<GameEnd scores={{ 1: 12, 2: 6 }} onHome={() => {}} />)
    expect(screen.getByText('Final Results')).toBeInTheDocument()
    expect(screen.getAllByText('Player 1').length).toBeGreaterThan(0)
  })

  it('renders admin word manager UI', () => {
    render(
      <AppProvider>
        <AdminWordsPage />
      </AppProvider>
    )
    expect(screen.getByText('Admin Word Manager')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('JWT token')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Search words')).toBeInTheDocument()
  })

  it('renders top bar guest state', () => {
    render(<TopBar isAuthed={false} isGuest guestDisplayName="TestGuest" />)
    expect(screen.getByText('TestGuest')).toBeInTheDocument()
  })

  it('renders top bar authed state with display name', () => {
    render(<TopBar isAuthed userDisplayName="John" userEmail="me@example.com" onLogout={() => {}} />)
    expect(screen.getByText('Logout')).toBeInTheDocument()
    expect(screen.getByText('John')).toBeInTheDocument()
  })
})
