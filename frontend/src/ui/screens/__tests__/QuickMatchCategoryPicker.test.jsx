import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import QuickMatchCategoryPicker from '../QuickMatchCategoryPicker.jsx'

describe('QuickMatchCategoryPicker', () => {
  it('renders 14 tiles (13 categories + Surprise Me)', () => {
    const { container } = render(<QuickMatchCategoryPicker onStart={vi.fn()} onBack={vi.fn()} />)
    const tiles = container.querySelectorAll('button[data-category]')
    expect(tiles.length).toBe(14)
  })

  it('Surprise Me passes "surprise" when selected and started', () => {
    const onStart = vi.fn()
    render(<QuickMatchCategoryPicker onStart={onStart} onBack={vi.fn()} />)
    fireEvent.click(screen.getByText(/Surprise me/i))
    fireEvent.click(screen.getByText(/Start Searching/i))
    expect(onStart).toHaveBeenCalledWith('surprise')
  })

  it('disables Start Searching after first tap', () => {
    const onStart = vi.fn()
    render(<QuickMatchCategoryPicker onStart={onStart} onBack={vi.fn()} />)
    fireEvent.click(screen.getByText('Science'))
    const btn = screen.getByText(/Start Searching/i)
    fireEvent.click(btn)
    fireEvent.click(btn)
    expect(onStart).toHaveBeenCalledTimes(1)
  })
})
