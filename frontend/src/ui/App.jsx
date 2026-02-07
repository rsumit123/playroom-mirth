import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { AppProvider } from '../state/AppContext.jsx'
import { useApp } from '../state/AppContext.jsx'
import WelcomePage from './pages/WelcomePage.jsx'
import AuthPage from './pages/AuthPage.jsx'
import HomePage from './pages/HomePage.jsx'
import LobbyPage from './pages/LobbyPage.jsx'
import GamePage from './pages/GamePage.jsx'
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
  const showTopBar = ['/home', '/lobby'].includes(path)

  return (
    <>
      <LoadingOverlay active={ui?.loading > 0} />
      <Toast message={ui?.toast} onClose={clearToast} />
      {showTopBar && (
        <TopBar
          userEmail={auth?.user?.email}
          isAuthed={Boolean(auth?.token)}
          isGuest={Boolean(auth?.guestToken && !auth?.token)}
          guestDisplayName={auth?.guestDisplayName}
          onLogin={() => navigate('/auth')}
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
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/lobby" element={<LobbyPage />} />
        <Route path="/game" element={<GamePage />} />
        <Route path="/round-end" element={<RoundEndPage />} />
        <Route path="/game-end" element={<GameEndPage />} />
        <Route path="/how-to" element={<HowToPage />} />
        <Route path="/admin/words" element={<AdminWordsPage />} />
      </Routes>
    </>
  )
}
