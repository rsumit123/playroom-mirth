import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import QuickMatchCategoryPicker from '../QuickMatchCategoryPicker.jsx'
import { CATEGORIES } from '../../components/TriviaCategorySelector.jsx'

describe('QuickMatchCategoryPicker', () => {
  it('renders 14 tiles (13 categories + Random)', () => {
    const { container } = render(<QuickMatchCategoryPicker onStart={vi.fn()} onBack={vi.fn()} />)
    const tiles = container.querySelectorAll('button[data-category]')
    expect(tiles.length).toBe(14)
  })

  it('renames the catch-all tile from "Surprise me" to "Random"', () => {
    render(<QuickMatchCategoryPicker onStart={vi.fn()} onBack={vi.fn()} />)
    expect(screen.getByText('Random')).toBeTruthy()
    expect(screen.queryByText(/Surprise me/i)).toBeNull()
  })

  it('disables Start after first tap (no double-fire)', () => {
    const onStart = vi.fn()
    render(<QuickMatchCategoryPicker onStart={onStart} onBack={vi.fn()} />)
    fireEvent.click(screen.getByText('Science'))
    const btn = screen.getByText(/Start Searching/i)
    fireEvent.click(btn)
    fireEvent.click(btn)
    expect(onStart).toHaveBeenCalledTimes(1)
  })

  it('a non-Random category fires onStart immediately with that value', () => {
    const onStart = vi.fn()
    render(<QuickMatchCategoryPicker onStart={onStart} onBack={vi.fn()} />)
    fireEvent.click(screen.getByText('Science'))
    fireEvent.click(screen.getByText(/Start Searching/i))
    expect(onStart).toHaveBeenCalledOnce()
    expect(onStart).toHaveBeenCalledWith('science')
  })

  describe('Random roulette', () => {
    beforeEach(() => { vi.useFakeTimers() })
    afterEach(() => { vi.useRealTimers() })

    it('does NOT fire onStart immediately when Random is selected', () => {
      const onStart = vi.fn()
      render(<QuickMatchCategoryPicker onStart={onStart} onBack={vi.fn()} />)
      // Random is the default selection.
      fireEvent.click(screen.getByText(/Start Searching/i))
      // No call within the first ~100ms — the roulette is animating.
      expect(onStart).not.toHaveBeenCalled()
    })

    it('shows the "Picking a topic..." header while rolling', () => {
      const onStart = vi.fn()
      render(<QuickMatchCategoryPicker onStart={onStart} onBack={vi.fn()} />)
      fireEvent.click(screen.getByText(/Start Searching/i))
      expect(screen.getByText(/Picking a topic/i)).toBeTruthy()
    })

    it('eventually calls onStart with a concrete category (NOT "surprise")', () => {
      const onStart = vi.fn()
      render(<QuickMatchCategoryPicker onStart={onStart} onBack={vi.fn()} />)
      fireEvent.click(screen.getByText(/Start Searching/i))
      // Fast-forward past the full roulette + rest pause.
      act(() => { vi.advanceTimersByTime(5000) })
      expect(onStart).toHaveBeenCalledOnce()
      const calledWith = onStart.mock.calls[0][0]
      expect(calledWith).not.toBe('surprise')
      expect(CATEGORIES.map(c => c.value)).toContain(calledWith)
    })

    it('settles on one category and shows the "Locked in!" header before starting', () => {
      const onStart = vi.fn()
      render(<QuickMatchCategoryPicker onStart={onStart} onBack={vi.fn()} />)
      fireEvent.click(screen.getByText(/Start Searching/i))
      // Advance to after the last hop but before the rest-pause completes.
      act(() => { vi.advanceTimersByTime(3200) })
      expect(screen.getByText(/Locked in/i)).toBeTruthy()
      expect(onStart).not.toHaveBeenCalled()
    })
  })
})
