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
})
