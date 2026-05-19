import { useEffect, useState, useCallback } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { Capacitor } from '@capacitor/core'
import { App as CapApp } from '@capacitor/app'
import { StatusBar, Style } from '@capacitor/status-bar'
import { AppProvider } from '../state/AppContext.jsx'
import { useApp } from '../state/AppContext.jsx'
import WelcomePage from './pages/WelcomePage.jsx'
import HomePage from './pages/HomePage.jsx'
import GameSetupPage from './pages/GameSetupPage.jsx'
import LobbyPage from './pages/LobbyPage.jsx'
import GamePage from './pages/GamePage.jsx'
import ScribbleGamePage from './pages/ScribbleGamePage.jsx'
import TriviaGamePage from './pages/TriviaGamePage.jsx'
import RoundEndPage from './pages/RoundEndPage.jsx'
import GameEndPage from './pages/GameEndPage.jsx'
import HowToPage from './pages/HowToPage.jsx'
import AdminWordsPage from './pages/AdminWordsPage.jsx'
import AdminDashboardPage from './pages/AdminDashboardPage.jsx'
import JoinPage from './pages/JoinPage.jsx'
import PrivacyPage from './pages/PrivacyPage.jsx'
import FriendsPage from './pages/FriendsPage.jsx'
import QuickMatchFlowPage from './pages/QuickMatchFlowPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import TopBar from './components/TopBar.jsx'
import NotificationDrawer from './components/NotificationDrawer.jsx'
import * as api from '../lib/api.js'
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
  const { auth, logout, ui, clearToast, fetchActiveRooms, joinRoom, bindLobbyEvents, notifKey } = useApp()
  const [notifications, setNotifications] = useState({ friend_requests_list: [], game_invites: [], total: 0 })
  const [showNotifications, setShowNotifications] = useState(false)

  // Validate JWT on mount — if expired, fetchActiveRooms will get 401 → logout
  useEffect(() => {
    if (auth?.token) fetchActiveRooms()
  }, [])

  // Poll notifications every 30s for signed-in users
  const fetchNotifications = useCallback(async () => {
    if (!auth?.token) return
    try {
      const data = await api.getNotifications(auth.token)
      // Also fetch friend request details for the drawer
      const reqData = await api.getFriendRequests(auth.token)
      setNotifications({
        friend_requests_list: reqData.requests || [],
        game_invites: data.game_invites || [],
        total: data.total || 0,
      })
    } catch { /* */ }
  }, [auth?.token])

  useEffect(() => {
    if (!auth?.token) return
    fetchNotifications()
    const interval = setInterval(fetchNotifications, 30000)
    return () => clearInterval(interval)
  }, [auth?.token, fetchNotifications, notifKey])

  // Android: configure status bar and back button
  useEffect(() => {
    if (!Capacitor.isNativePlatform()) return
    StatusBar.setOverlaysWebView({ overlay: true })
    StatusBar.setBackgroundColor({ color: '#00000000' })
    StatusBar.setStyle({ style: Style.Dark })

    const listener = CapApp.addListener('backButton', ({ canGoBack }) => {
      if (canGoBack) {
        navigate(-1)
      } else {
        CapApp.minimizeApp()
      }
    })
    return () => { listener.then(l => l.remove()) }
  }, [])

  // Redirect to welcome screen when auth is cleared (e.g. expired session)
  const isAuthed = Boolean(auth?.token || auth?.guestToken)
  const path = location.pathname
  useEffect(() => {
    if (!isAuthed && path !== '/' && path !== '/how-to' && path !== '/privacy' && !path.startsWith('/join/') && !path.startsWith('/admin')) {
      navigate('/', { replace: true })
    }
  }, [isAuthed])

  const showTopBar = path === '/home' || path === '/lobby' || path === '/friends' || path === '/history' || path.startsWith('/play/')

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
          notificationCount={notifications.total}
          onNotifications={() => { fetchNotifications(); setShowNotifications(true) }}
          onLogout={() => {
            logout()
            navigate('/')
          }}
          onHome={() => navigate('/home')}
          onHowTo={() => navigate('/how-to')}
          onHistory={() => navigate('/history')}
          onFriends={() => navigate('/friends')}
        />
      )}
      <NotificationDrawer
        open={showNotifications}
        notifications={notifications}
        onAcceptFriend={async (userId) => {
          try {
            await api.acceptFriendRequest(auth.token, userId)
            await fetchNotifications()
          } catch { /* */ }
        }}
        onRejectFriend={async (userId) => {
          try {
            await api.rejectFriend(auth.token, userId)
            await fetchNotifications()
          } catch { /* */ }
        }}
        onJoinRoom={async (roomCode) => {
          setShowNotifications(false)
          try {
            await joinRoom(roomCode)
            bindLobbyEvents(roomCode)
            navigate('/lobby', { state: { fromJoin: true } })
          } catch { /* */ }
        }}
        onClose={() => setShowNotifications(false)}
      />
      <Routes>
        <Route path="/" element={<WelcomePage />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/play/:gameType" element={<GameSetupPage />} />
        <Route path="/lobby" element={<LobbyPage />} />
        <Route path="/game" element={<GamePage />} />
        <Route path="/scribble" element={<ScribbleGamePage />} />
        <Route path="/trivia" element={<TriviaGamePage />} />
        <Route path="/quickmatch" element={<QuickMatchFlowPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/round-end" element={<RoundEndPage />} />
        <Route path="/game-end" element={<GameEndPage />} />
        <Route path="/how-to" element={<HowToPage />} />
        <Route path="/join/:roomCode" element={<JoinPage />} />
        <Route path="/friends" element={<FriendsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/admin" element={<AdminDashboardPage />} />
        <Route path="/admin/words" element={<AdminWordsPage />} />
      </Routes>
    </>
  )
}
