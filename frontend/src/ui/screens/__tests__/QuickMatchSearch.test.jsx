import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import QuickMatchSearch from '../QuickMatchSearch.jsx'

describe('QuickMatchSearch', () => {
  it('renders countdown starting at 15 seconds', () => {
    render(<QuickMatchSearch waitSeconds={15} category="science" onCancel={vi.fn()} />)
    expect(screen.getByText('15')).toBeTruthy()
  })

  it('shows the category label', () => {
    render(<QuickMatchSearch waitSeconds={15} category="science" onCancel={vi.fn()} />)
    expect(screen.getByText(/science/i)).toBeTruthy()
  })

  it('shows "Random" label and 🎲 when category is the default surprise', () => {
    render(<QuickMatchSearch waitSeconds={15} category="surprise" onCancel={vi.fn()} />)
    expect(screen.getByText(/Random/i)).toBeTruthy()
  })

  it('opens the topic sheet when the gear chip is tapped, and onChangeCategory fires on selection', () => {
    const onChangeCategory = vi.fn()
    const { container } = render(
      <QuickMatchSearch
        waitSeconds={15} category="surprise"
        onCancel={vi.fn()} onChangeCategory={onChangeCategory}
      />
    )
    fireEvent.click(screen.getByLabelText(/change topic/i))
    // Sheet is open — heading visible
    expect(screen.getByText(/Choose topic/i)).toBeTruthy()
    // Pick a non-Random topic from the rendered selector (Science).
    const scienceBtn = [...container.querySelectorAll('button')].find(b => /science/i.test(b.textContent))
    fireEvent.click(scienceBtn)
    expect(onChangeCategory).toHaveBeenCalledWith('science')
  })

  it('does NOT call onChangeCategory when the same category is re-selected (no spurious re-queue)', () => {
    const onChangeCategory = vi.fn()
    render(
      <QuickMatchSearch
        waitSeconds={15} category="surprise"
        onCancel={vi.fn()} onChangeCategory={onChangeCategory}
      />
    )
    fireEvent.click(screen.getByLabelText(/change topic/i))
    // Tap the Random tile in the sheet — same as current category.
    const randomBtn = [...screen.getAllByRole('button')].find(b => /Random/.test(b.textContent) && b.querySelector('.text-2xl'))
    fireEvent.click(randomBtn)
    expect(onChangeCategory).not.toHaveBeenCalled()
  })

  it('calls onCancel when cancel button is clicked', () => {
    const onCancel = vi.fn()
    render(<QuickMatchSearch waitSeconds={15} category="science" onCancel={onCancel} />)
    fireEvent.click(screen.getByLabelText(/cancel/i))
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('countdown decrements over time', () => {
    vi.useFakeTimers()
    render(<QuickMatchSearch waitSeconds={15} category="science" onCancel={vi.fn()} />)
    act(() => { vi.advanceTimersByTime(2000) })
    expect(screen.getByText('13')).toBeTruthy()
    vi.useRealTimers()
  })

  it('countdown CLAMPS at 0 — does not go negative when waitSeconds elapses (regression: user saw -10 when bot fallback was slow)', () => {
    vi.useFakeTimers()
    render(<QuickMatchSearch waitSeconds={15} category="science" onCancel={vi.fn()} />)
    // Run 30 seconds — well past the 15s wait window. The legitimate countdown
    // should hit 0 and stop, not display -15.
    act(() => { vi.advanceTimersByTime(30000) })
    expect(screen.getByText('0')).toBeTruthy()
    expect(screen.queryByText(/-1/)).toBeNull()
    expect(screen.queryByText(/-10/)).toBeNull()
    vi.useRealTimers()
  })
})
