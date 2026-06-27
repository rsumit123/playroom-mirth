import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import QuickMatchSearch from '../screens/QuickMatchSearch.jsx'
import MatchFoundSplash from '../screens/MatchFoundSplash.jsx'
import { useApp } from '../../state/AppContext.jsx'

const DEFAULT_CATEGORY = 'surprise'

export default function QuickMatchFlowPage() {
  const navigate = useNavigate()
  const { quickmatch, quickmatchJoin, quickmatchCancel, quickmatchReady, quickmatchReset, bindLobbyEvents, startGameSocket } = useApp()

  // Defensive: if we mount with `matched` already set, it's stale carry-over
  // from a prior game (e.g. user clicked Home from GameEnd then came back).
  // In the normal flow, `matched` only arrives AFTER mount — during the search
  // countdown — so seeing it at mount-time is always wrong. We block the
  // matched UI/effects synchronously via `staleBlocked` (so the splash never
  // flashes), fire the reset in an effect, and clear the block once status
  // moves away from 'matched' (i.e. the reset has landed).
  const [staleBlocked, setStaleBlocked] = useState(quickmatch.status === 'matched')
  useEffect(() => {
    if (staleBlocked) {
      quickmatchReset()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  useEffect(() => {
    if (staleBlocked && quickmatch.status !== 'matched') {
      setStaleBlocked(false)
    }
  }, [quickmatch.status, staleBlocked])

  // Frictionless entry: if we land here with no queue active, auto-join with
  // the random "surprise" category exactly once. The user can override
  // mid-search via the topic chip on the search screen.
  //
  // We deliberately do NOT trigger on 'cancelled' — that state arrives during
  // the changeCategory cancel-then-join sequence, and re-triggering here would
  // race with the user's pick and slam them back to 'surprise'.
  const autoJoinedRef = useRef(false)
  useEffect(() => {
    if (autoJoinedRef.current) return
    if (quickmatch.status === 'idle') {
      autoJoinedRef.current = true
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
    if (staleBlocked) return  // about to reset — don't bind against a dead room
    if (quickmatch.status === 'matched' && quickmatch.roomCode) {
      // bindLobbyEvents registers room:register on connect + room:lobby_update.
      // startGameSocket registers game:game_end / game:round_end / game:player_removed
      // and the in-game trivia/chat listeners. Quickmatch skips the lobby, so we
      // need both bound before the game starts on the backend.
      bindLobbyEvents(quickmatch.roomCode)
      startGameSocket()
      quickmatchReady(quickmatch.roomCode)
    }
  }, [quickmatch.status, quickmatch.roomCode, staleBlocked])

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

  if (quickmatch.status === 'matched' && !staleBlocked) {
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
