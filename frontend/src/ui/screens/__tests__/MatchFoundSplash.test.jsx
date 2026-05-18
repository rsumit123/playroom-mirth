import { describe, it, expect, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import MatchFoundSplash from '../MatchFoundSplash.jsx'

describe('MatchFoundSplash', () => {
  it('renders opponent name', () => {
    render(<MatchFoundSplash opponentName="Priya" category="science" onDone={vi.fn()} />)
    expect(screen.getByText('Priya')).toBeTruthy()
  })

  it('calls onDone after 1800ms', () => {
    vi.useFakeTimers()
    const onDone = vi.fn()
    render(<MatchFoundSplash opponentName="Priya" category="science" onDone={onDone} />)
    act(() => { vi.advanceTimersByTime(1800) })
    expect(onDone).toHaveBeenCalledOnce()
    vi.useRealTimers()
  })
})
