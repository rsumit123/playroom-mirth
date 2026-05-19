import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import QuickMatchSearch from '../screens/QuickMatchSearch.jsx'
import MatchFoundSplash from '../screens/MatchFoundSplash.jsx'
import { useApp } from '../../state/AppContext.jsx'

const DEFAULT_CATEGORY = 'surprise'

export default function QuickMatchFlowPage() {
  const navigate = useNavigate()
  const { quickmatch, quickmatchJoin, quickmatchCancel, quickmatchReady, bindLobbyEvents, startGameSocket } = useApp()

  // Frictionless entry: if we land here with no queue active, auto-join with
  // the random "surprise" category. The user can override mid-search via the
  // topic chip on the search screen.
  useEffect(() => {
    if (quickmatch.status === 'idle' || quickmatch.status === 'cancelled') {
      quickmatchJoin(DEFAULT_CATEGORY)
    }
  }, [quickmatch.status])

  function cancel() {
    quickmatchCancel()
    navigate('/play/trivia')
  }

  function changeCategory(newCategory) {
    // Re-queue with the new category. Cancel first so the matchmaker drops the
    // current entry; then join immediately. The user expects the gear chip to
    // mean "I want this topic NOW", not "next match".
    quickmatchCancel()
    quickmatchJoin(newCategory)
  }

  useEffect(() => {
    if (quickmatch.status === 'matched' && quickmatch.roomCode) {
      // bindLobbyEvents registers room:register on connect + room:lobby_update.
      // startGameSocket registers game:game_end / game:round_end / game:player_removed
      // and the in-game trivia/chat listeners. Quickmatch skips the lobby, so we
      // need both bound before the game starts on the backend.
      bindLobbyEvents(quickmatch.roomCode)
      startGameSocket()
      quickmatchReady(quickmatch.roomCode)
    }
  }, [quickmatch.status, quickmatch.roomCode])

  // Hardware back button — cancel queue while searching, else go back to trivia
  useEffect(() => {
    let handler
    let cancelled = false
    import('@capacitor/app').then(({ App: CapApp }) => {
      if (cancelled) return
      CapApp.addListener('backButton', () => {
        if (quickmatch.status === 'searching') cancel()
        else navigate('/play/trivia')
      }).then(h => { if (cancelled) h.remove?.(); else handler = h })
    }).catch(() => { /* non-capacitor (web) — no-op */ })
    return () => {
      cancelled = true
      try { handler?.remove?.() } catch {}
    }
  }, [quickmatch.status])

  // App-state — cancel queue if backgrounded for >10s while searching
  useEffect(() => {
    if (quickmatch.status !== 'searching') return
    let backgroundedAt = null
    let handle = null
    let cancelled = false
    import('@capacitor/app').then(({ App: CapApp }) => {
      if (cancelled) return
      CapApp.addListener('appStateChange', ({ isActive }) => {
        if (!isActive) backgroundedAt = Date.now()
        else if (backgroundedAt && Date.now() - backgroundedAt > 10000) {
          backgroundedAt = null
          cancel()
        }
      }).then(h => { if (cancelled) h.remove?.(); else handle = h })
    }).catch(() => {})
    return () => {
      cancelled = true
      try { handle?.remove?.() } catch {}
    }
  }, [quickmatch.status])

  if (quickmatch.status === 'matched') {
    return (
      <MatchFoundSplash
        opponentName={quickmatch.opponentName}
        category={quickmatch.category}
        onDone={() => navigate('/trivia')}
      />
    )
  }
  // Default: searching (or transitioning into it). The brief idle gap before
  // the auto-join kicks in shows the searching UI with the chosen category.
  return (
    <QuickMatchSearch
      waitSeconds={quickmatch.waitSeconds}
      category={quickmatch.category || DEFAULT_CATEGORY}
      onCancel={cancel}
      onChangeCategory={changeCategory}
    />
  )
}
