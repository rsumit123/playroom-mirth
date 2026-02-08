import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { AppProvider } from '../state/AppContext.jsx'
import { useApp } from '../state/AppContext.jsx'
import WelcomePage from './pages/WelcomePage.jsx'
import HomePage from './pages/HomePage.jsx'
import GameSetupPage from './pages/GameSetupPage.jsx'
import LobbyPage from './pages/LobbyPage.jsx'
import GamePage from './pages/GamePage.jsx'
import ScribbleGamePage from './pages/ScribbleGamePage.jsx'
import RoundEndPage from './pages/RoundEndPage.jsx'
import GameEndPage from './pages/GameEndPage.jsx'
import HowToPage from './pages/HowToPage.jsx'
import AdminWordsPage from './pages/AdminWordsPage.jsx'
import TopBar from './components/TopBar.jsx'
import Toast from './components/Toast.jsx'
import LoadingOverlay from './components/LoadingOverlay.jsx'

export default function App() {
  return (
    <div className="min-h-screen bg-texture noise relative">
      <div className="relative z-10">
        <AppProvider>
          <BrowserRouter>
            <AppShell />
          </BrowserRouter>
        </AppProvider>
      </div>
    </div>
  )
}

function AppShell() {
  const navigate = useNavigate()
  const location = useLocation()
  const { auth, logout, ui, clearToast } = useApp()

  const path = location.pathname
  const showTopBar = path === '/home' || path === '/lobby' || path.startsWith('/play/')

  return (
    <>
      <LoadingOverlay active={ui?.loading > 0} />
      <Toast message={ui?.toast} onClose={clearToast} />
      {showTopBar && (
        <TopBar
          userEmail={auth?.user?.email}
          userDisplayName={auth?.user?.display_name}
          userAvatarUrl={auth?.user?.avatar_url}
          isAuthed={Boolean(auth?.token)}
          isGuest={Boolean(auth?.guestToken && !auth?.token)}
          guestDisplayName={auth?.guestDisplayName}
          onLogout={() => {
            logout()
            navigate('/')
          }}
          onHome={() => navigate('/home')}
          onHowTo={() => navigate('/how-to')}
        />
      )}
      <Routes>
        <Route path="/" element={<WelcomePage />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/play/:gameType" element={<GameSetupPage />} />
        <Route path="/lobby" element={<LobbyPage />} />
        <Route path="/game" element={<GamePage />} />
        <Route path="/scribble" element={<ScribbleGamePage />} />
        <Route path="/round-end" element={<RoundEndPage />} />
        <Route path="/game-end" element={<GameEndPage />} />
        <Route path="/how-to" element={<HowToPage />} />
        <Route path="/admin/words" element={<AdminWordsPage />} />
      </Routes>
    </>
  )
}
