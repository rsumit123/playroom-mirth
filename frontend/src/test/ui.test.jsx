import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Home from '../ui/screens/Home.jsx'
import Auth from '../ui/screens/Auth.jsx'
import Game from '../ui/screens/Game.jsx'
import Lobby from '../ui/screens/Lobby.jsx'
import RoundEnd from '../ui/screens/RoundEnd.jsx'
import GameEnd from '../ui/screens/GameEnd.jsx'
import AdminWordsPage from '../ui/pages/AdminWordsPage.jsx'
import TopBar from '../ui/components/TopBar.jsx'
import { AppProvider } from '../state/AppContext.jsx'

describe('UI screens', () => {
  it('renders Home and triggers create/join handlers', () => {
    const onCreate = vi.fn()
    const onJoin = vi.fn()
    render(<Home onCreate={onCreate} onJoin={onJoin} onHowTo={() => {}} />)

    fireEvent.click(screen.getByText('Create Room'))
    expect(onCreate).toHaveBeenCalled()

    fireEvent.change(screen.getByPlaceholderText('Room Code'), { target: { value: 'ABCD12' } })
    fireEvent.click(screen.getByText('Join Room'))
    expect(onJoin).toHaveBeenCalledWith('ABCD12')
  })

  it('renders Auth and calls onDone with inputs', () => {
    const onDone = vi.fn()
    render(<Auth onBack={() => {}} onDone={onDone} />)

    fireEvent.change(screen.getByPlaceholderText('Email'), { target: { value: 'a@example.com' } })
    fireEvent.change(screen.getByPlaceholderText('Password'), { target: { value: 'secret' } })
    const signInButtons = screen.getAllByRole('button', { name: 'Sign In' })
    fireEvent.click(signInButtons[1])

    expect(onDone).toHaveBeenCalledWith('signin', 'a@example.com', 'secret')
  })

  it('shows correct guess banner when lastGuess is set', () => {
    const game = { lastGuess: { word: 'umbrella' }, turn: { turn_seconds: 60 }, selfPlayerId: 2 }
    render(<Game game={game} onSend={() => {}} onRoundEnd={() => {}} onGameEnd={() => {}} onRejoin={() => {}} />)
    expect(screen.getByText('Correct Guess')).toBeInTheDocument()
    expect(screen.getByText('umbrella')).toBeInTheDocument()
  })

  it('renders chat messages from game state', () => {
    const game = { messages: [{ player_id: 1, message: 'hello' }], turn: { turn_seconds: 60 }, selfPlayerId: 2 }
    render(<Game game={game} onSend={() => {}} onRoundEnd={() => {}} onGameEnd={() => {}} onRejoin={() => {}} />)
    expect(screen.getByText('Player 1:')).toBeInTheDocument()
    expect(screen.getByText('hello')).toBeInTheDocument()
  })

  it('renders scoreboard entries', () => {
    const game = { scores: { 1: 10, 2: 5 }, turn: { turn_seconds: 60 }, selfPlayerId: 2 }
    render(<Game game={game} onSend={() => {}} onRoundEnd={() => {}} onGameEnd={() => {}} onRejoin={() => {}} />)
    expect(screen.getByText('#1 Player 1')).toBeInTheDocument()
    expect(screen.getByText('10 pts')).toBeInTheDocument()
  })

  it('allows editing lobby settings', () => {
    const lobby = { room: { rounds_total: 2, difficulty: 1, turn_seconds: 45 }, players: [] }
    const onSaveSettings = vi.fn()
    render(<Lobby lobby={lobby} onStart={() => {}} onLeave={() => {}} onSaveSettings={onSaveSettings} />)
    const rounds = screen.getByPlaceholderText('Enter rounds')
    fireEvent.change(rounds, { target: { value: '4' } })
    expect(rounds.value).toBe('4')
    fireEvent.click(screen.getByText('Save Settings'))
    expect(onSaveSettings).toHaveBeenCalled()
  })

  it('shows reconnect banner when reconnecting', () => {
    const game = { reconnecting: true, reconnectGrace: { expires_at: Math.floor(Date.now() / 1000) + 30 }, turn: { turn_seconds: 60 }, selfPlayerId: 2 }
    render(<Game game={game} onSend={() => {}} onRoundEnd={() => {}} onGameEnd={() => {}} onRejoin={() => {}} />)
    expect(screen.getByText('Reconnecting…')).toBeInTheDocument()
  })

  it('shows player removed banner', () => {
    const game = { removed: { player_id: 2 }, turn: { turn_seconds: 60 }, selfPlayerId: 2 }
    render(<Game game={game} onSend={() => {}} onRoundEnd={() => {}} onGameEnd={() => {}} onRejoin={() => {}} />)
    expect(screen.getByText('Player removed')).toBeInTheDocument()
  })

  it('renders share and copy buttons in lobby', () => {
    const lobby = { room: { rounds_total: 2, difficulty: 1, turn_seconds: 45 }, players: [] }
    render(<Lobby lobby={lobby} onStart={() => {}} onLeave={() => {}} />)
    expect(screen.getAllByText('Copy').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Share').length).toBeGreaterThan(0)
  })

  it('shows waiting label for non-active players', () => {
    const lobby = {
      room: { rounds_total: 2, difficulty: 1, turn_seconds: 45, status: 'active' },
      players: [{ id: 1, user_id: null, in_game: false }]
    }
    render(<Lobby lobby={lobby} onStart={() => {}} onLeave={() => {}} selfPlayerId={1} />)
    expect(screen.getByText((content) => content.includes('Waiting for next game'))).toBeInTheDocument()
    expect(screen.getByText('Game in progress')).toBeInTheDocument()
  })

  it('renders round end scoreboard', () => {
    render(<RoundEnd scores={{ 1: 8, 2: 3 }} onContinue={() => {}} />)
    expect(screen.getAllByText('#1 Player 1').length).toBeGreaterThan(0)
  })

  it('renders game end scoreboard', () => {
    render(<GameEnd scores={{ 1: 12, 2: 6 }} onHome={() => {}} />)
    expect(screen.getAllByText('#1 Player 1').length).toBeGreaterThan(0)
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

  it('renders top bar login/logout states', () => {
    render(<TopBar isAuthed={false} onLogin={() => {}} />)
    expect(screen.getByText('Login')).toBeInTheDocument()

    render(<TopBar isAuthed userEmail="me@example.com" onLogout={() => {}} onProfile={() => {}} />)
    expect(screen.getByText('Logout')).toBeInTheDocument()
    expect(screen.getByText('me@example.com')).toBeInTheDocument()
  })
})
