import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import DifficultySelector from '../DifficultySelector.jsx'

describe('DifficultySelector', () => {
  it('renders all four difficulty options', () => {
    render(<DifficultySelector value={0} onChange={vi.fn()} />)
    expect(screen.getByText('Mixed')).toBeInTheDocument()
    expect(screen.getByText('Easy')).toBeInTheDocument()
    expect(screen.getByText('Medium')).toBeInTheDocument()
    expect(screen.getByText('Hard')).toBeInTheDocument()
  })

  it('applies active class to the selected value', () => {
    render(<DifficultySelector value={2} onChange={vi.fn()} />)
    expect(screen.getByText('Medium').className).toContain('segmented-option-active')
    expect(screen.getByText('Easy').className).toContain('segmented-option')
    expect(screen.getByText('Easy').className).not.toContain('segmented-option-active')
  })

  it('calls onChange with 1 when Easy is clicked', () => {
    const onChange = vi.fn()
    render(<DifficultySelector value={0} onChange={onChange} />)
    fireEvent.click(screen.getByText('Easy'))
    expect(onChange).toHaveBeenCalledWith(1)
  })

  it('calls onChange with 3 when Hard is clicked', () => {
    const onChange = vi.fn()
    render(<DifficultySelector value={0} onChange={onChange} />)
    fireEvent.click(screen.getByText('Hard'))
    expect(onChange).toHaveBeenCalledWith(3)
  })

  it('calls onChange with 0 when Mixed is clicked', () => {
    const onChange = vi.fn()
    render(<DifficultySelector value={2} onChange={onChange} />)
    fireEvent.click(screen.getByText('Mixed'))
    expect(onChange).toHaveBeenCalledWith(0)
  })
})
