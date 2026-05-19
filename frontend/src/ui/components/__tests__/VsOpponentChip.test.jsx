import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import VsOpponentChip from '../VsOpponentChip.jsx'

function rerenderWith(props) {
  return render(<VsOpponentChip {...props} />)
}

describe('VsOpponentChip', () => {
  it('renders nothing when fewer than 2 players are present', () => {
    const { container } = render(
      <VsOpponentChip scores={{}} playerNames={{}} selfPlayerId={1} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing when more than 2 players are present (friend games take a different surface)', () => {
    const { container } = render(
      <VsOpponentChip
        scores={{ 1: 100, 2: 50, 3: 80 }}
        playerNames={{ 1: 'You', 2: 'Bob', 3: 'Eve' }}
        selfPlayerId={1}
      />
    )
    expect(container.firstChild).toBeNull()
  })

  it('renders both scores and the opponent name in 1v1', () => {
    const { container } = render(
      <VsOpponentChip
        scores={{ 1: 175, 2: 0 }}
        playerNames={{ 1: 'Alice', 2: 'Rohan' }}
        selfPlayerId={1}
      />
    )
    expect(container.textContent).toContain('175')
    expect(container.textContent).toContain('0')
    expect(container.textContent).toContain('Rohan')
    expect(container.textContent).toContain('You')
  })

  it('highlights the leader with the accent class', () => {
    const { container } = render(
      <VsOpponentChip
        scores={{ 1: 50, 2: 200 }}
        playerNames={{ 1: 'Alice', 2: 'Rohan' }}
        selfPlayerId={1}
      />
    )
    // The opponent score block has text-accent because they lead.
    const accent = container.querySelectorAll('.text-accent')
    expect(accent.length).toBeGreaterThan(0)
  })

  it('does not highlight either side on a tie', () => {
    const { container } = render(
      <VsOpponentChip
        scores={{ 1: 100, 2: 100 }}
        playerNames={{ 1: 'Alice', 2: 'Rohan' }}
        selfPlayerId={1}
      />
    )
    // Neither score block carries text-accent on a tie.
    // (The avatar bubble may still be accent — that's the "you" identity, not the leader cue.)
    const scoreBlocks = [...container.querySelectorAll('.font-display')]
    expect(scoreBlocks.every(el => !el.classList.contains('text-accent'))).toBe(true)
  })

  it('uses playerOrder when provided to locate self vs opponent', () => {
    const { container } = render(
      <VsOpponentChip
        scores={{ 9: 50, 10: 75 }}
        playerNames={{ 9: 'Self Name (ignored)', 10: 'Priya' }}
        selfPlayerId={9}
        playerOrder={[9, 10]}
      />
    )
    // Opponent name surfaces; self side uses the hardcoded "You" label.
    expect(container.textContent).toContain('Priya')
    expect(container.textContent).toContain('You')
  })

  it('shows a +N pop when a player\'s score goes up across a question boundary', () => {
    const baseProps = {
      playerNames: { 1: 'Alice', 2: 'Rohan' },
      selfPlayerId: 1,
      playerOrder: [1, 2],
    }
    // First question — snapshot scores 0/0. No animation yet.
    const { container, rerender } = render(
      <VsOpponentChip {...baseProps} scores={{ 1: 0, 2: 0 }} questionIndex={1} />
    )
    expect(container.textContent).not.toMatch(/\+\d/)
    // Question advances; self got it right.
    rerender(
      <VsOpponentChip {...baseProps} scores={{ 1: 100, 2: 0 }} questionIndex={2} />
    )
    expect(container.textContent).toMatch(/\+100/)
  })

  it('shows the 🔥 streak emoji after 3 consecutive correct answers', () => {
    const baseProps = {
      playerNames: { 1: 'Alice', 2: 'Rohan' },
      selfPlayerId: 1,
      playerOrder: [1, 2],
    }
    const { container, rerender } = render(
      <VsOpponentChip {...baseProps} scores={{ 1: 0, 2: 0 }} questionIndex={1} />
    )
    rerender(<VsOpponentChip {...baseProps} scores={{ 1: 100, 2: 0 }} questionIndex={2} />)
    rerender(<VsOpponentChip {...baseProps} scores={{ 1: 200, 2: 0 }} questionIndex={3} />)
    expect(container.textContent).not.toMatch(/🔥/)  // streak=2, not enough
    rerender(<VsOpponentChip {...baseProps} scores={{ 1: 300, 2: 0 }} questionIndex={4} />)
    expect(container.textContent).toMatch(/🔥/)
  })

  it('resets the streak when a question is missed (no score change)', () => {
    const baseProps = {
      playerNames: { 1: 'Alice', 2: 'Rohan' },
      selfPlayerId: 1,
      playerOrder: [1, 2],
    }
    const { container, rerender } = render(
      <VsOpponentChip {...baseProps} scores={{ 1: 0, 2: 0 }} questionIndex={1} />
    )
    rerender(<VsOpponentChip {...baseProps} scores={{ 1: 100, 2: 0 }} questionIndex={2} />)
    rerender(<VsOpponentChip {...baseProps} scores={{ 1: 200, 2: 0 }} questionIndex={3} />)
    rerender(<VsOpponentChip {...baseProps} scores={{ 1: 300, 2: 0 }} questionIndex={4} />)
    expect(container.textContent).toMatch(/🔥/)
    // Player missed Q4 — score unchanged on Q5.
    rerender(<VsOpponentChip {...baseProps} scores={{ 1: 300, 2: 0 }} questionIndex={5} />)
    expect(container.textContent).not.toMatch(/🔥/)
  })
})
