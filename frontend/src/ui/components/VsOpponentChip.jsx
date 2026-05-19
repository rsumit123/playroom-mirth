/**
 * Live "you vs opponent" chip shown above the trivia card in 1v1 quickmatch
 * games. Designed to be flat + compact: ~44px tall on mobile, doesn't compete
 * with the question card for attention. Score on each side updates live from
 * scores prop; the player currently in the lead gets the accent treatment.
 *
 * Score reactions: when `questionIndex` increments, we diff scores against the
 * previous question. If a side's score went up they get a floating "+N ⬆️"
 * pulse; if they're on a 3+ streak we surface a 🔥 next to their score.
 */

import { useEffect, useRef, useState } from 'react'

const STREAK_THRESHOLD = 3

function Initial({ name, isYou }) {
  const letter = (name || '?').trim().slice(0, 1).toUpperCase() || '?'
  return (
    <div className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
      isYou ? 'bg-accent text-white' : 'bg-slate/15 text-slate/70'
    }`}>
      {letter}
    </div>
  )
}

function ScoreCell({ name, score, lead, streak, pop, side }) {
  const alignR = side === 'right'
  return (
    <div className={`min-w-0 ${alignR ? 'text-right' : ''} relative`}>
      <div className={`text-[10px] uppercase tracking-wider text-slate/40 leading-none ${alignR ? 'truncate' : ''}`}>
        {name}
      </div>
      <div className={`font-display text-base leading-tight flex items-center gap-1 ${alignR ? 'justify-end' : ''} ${lead ? 'text-accent' : 'text-ink'}`}>
        {streak >= STREAK_THRESHOLD && (
          <span
            className="text-xs leading-none animate-pop"
            title={`${streak}-question streak`}
            aria-label={`${streak} question streak`}
          >🔥</span>
        )}
        <span>{score}</span>
      </div>
      {pop && (
        // key on pop.id forces the floating element to remount + re-run its
        // entry animation each time the user gets another one right.
        <div
          key={pop.id}
          className={`absolute -top-3 ${alignR ? 'right-0' : 'left-9'} text-[11px] font-bold text-correct pointer-events-none animate-score-pop`}
          aria-hidden="true"
        >
          <span className="inline-flex items-center gap-0.5">
            <span>⬆</span>
            <span>+{pop.delta}</span>
          </span>
        </div>
      )}
    </div>
  )
}

export default function VsOpponentChip({ scores, playerNames, selfPlayerId, playerOrder, questionIndex }) {
  // Build the two-player breakdown. We only render for exactly 2 players —
  // for friend games with 3+, scoreboard takes over.
  const ids = (playerOrder && playerOrder.length === 2) ? playerOrder : Object.keys(scores || {})
  const validPair = ids && ids.length === 2

  // ─── Score-reaction state ────────────────────────────────────────────────
  // We diff against the scores snapshot we held at the previous question_index
  // boundary. Streaks tracked per player id (string keys for stable equality).
  const lastScoresRef = useRef({})
  const lastQuestionIndexRef = useRef(null)
  const [streaks, setStreaks] = useState({})
  const [pops, setPops] = useState({})  // { [pid]: { id, delta } }

  useEffect(() => {
    if (!validPair) return
    if (questionIndex == null) return
    // First observation — just snapshot, no animation.
    if (lastQuestionIndexRef.current == null) {
      lastQuestionIndexRef.current = questionIndex
      lastScoresRef.current = { ...scores }
      return
    }
    // New question started — diff against the snapshot we held entering the
    // PREVIOUS question, then update.
    if (questionIndex === lastQuestionIndexRef.current) return
    // Reset case: question index went backwards (new game) → wipe everything.
    if (questionIndex < lastQuestionIndexRef.current) {
      lastQuestionIndexRef.current = questionIndex
      lastScoresRef.current = { ...scores }
      setStreaks({})
      setPops({})
      return
    }
    const prev = lastScoresRef.current
    const nextStreaks = { ...streaks }
    const nextPops = { ...pops }
    for (const pid of ids) {
      const before = prev?.[pid] ?? 0
      const after = scores?.[pid] ?? 0
      if (after > before) {
        nextStreaks[pid] = (streaks[pid] || 0) + 1
        nextPops[pid] = { id: `${questionIndex}-${pid}`, delta: after - before }
      } else {
        nextStreaks[pid] = 0
        // Clear stale pop so it doesn't linger on a wrong answer.
        delete nextPops[pid]
      }
    }
    setStreaks(nextStreaks)
    setPops(nextPops)
    lastQuestionIndexRef.current = questionIndex
    lastScoresRef.current = { ...scores }

    // Auto-clear pop after the animation finishes.
    const id = setTimeout(() => setPops(p => {
      const next = { ...p }
      for (const pid of ids) delete next[pid]
      return next
    }), 1500)
    return () => clearTimeout(id)
  }, [questionIndex, validPair])

  if (!validPair) return null

  const youId = String(selfPlayerId)
  const meId = ids.find(id => String(id) === youId) ?? ids[0]
  const oppId = ids.find(id => String(id) !== String(meId)) ?? ids[1]
  const meScore = scores?.[meId] ?? 0
  const oppScore = scores?.[oppId] ?? 0
  const oppName = playerNames?.[oppId] || 'Opponent'

  const meLeads = meScore > oppScore
  const oppLeads = oppScore > meScore

  return (
    <div className="bg-white/70 backdrop-blur border-b border-black/5 px-4 py-2 shrink-0">
      <div className="max-w-lg mx-auto flex items-center justify-between gap-3">
        {/* You — left */}
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <Initial name="You" isYou />
          <ScoreCell
            name="You"
            score={meScore}
            lead={meLeads}
            streak={streaks[meId] || 0}
            pop={pops[meId]}
            side="left"
          />
        </div>

        {/* vs separator */}
        <div className="text-[10px] uppercase tracking-widest text-slate/40 shrink-0">vs</div>

        {/* Opponent — right (mirrored layout so scores meet in the middle) */}
        <div className="flex items-center gap-2 min-w-0 flex-1 justify-end">
          <ScoreCell
            name={oppName}
            score={oppScore}
            lead={oppLeads}
            streak={streaks[oppId] || 0}
            pop={pops[oppId]}
            side="right"
          />
          <Initial name={oppName} isYou={false} />
        </div>
      </div>
    </div>
  )
}
