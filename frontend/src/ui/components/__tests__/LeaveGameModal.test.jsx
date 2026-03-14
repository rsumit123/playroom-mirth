import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import LeaveGameModal from '../LeaveGameModal.jsx'

describe('LeaveGameModal', () => {
  it('renders nothing when open is false', () => {
    const { container } = render(
      <LeaveGameModal open={false} onConfirm={vi.fn()} onCancel={vi.fn()} />
    )
    expect(container.innerHTML).toBe('')
  })

  it('renders modal when open is true', () => {
    render(<LeaveGameModal open={true} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText('Leave game?')).toBeTruthy()
    expect(screen.getByText(/lose your progress/)).toBeTruthy()
  })

  it('renders Stay and Leave buttons', () => {
    render(<LeaveGameModal open={true} onConfirm={vi.fn()} onCancel={vi.fn()} />)
    expect(screen.getByText('Stay')).toBeTruthy()
    expect(screen.getByText('Leave')).toBeTruthy()
  })

  it('calls onCancel when Stay is clicked', () => {
    const onCancel = vi.fn()
    render(<LeaveGameModal open={true} onConfirm={vi.fn()} onCancel={onCancel} />)
    fireEvent.click(screen.getByText('Stay'))
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('calls onConfirm when Leave is clicked', () => {
    const onConfirm = vi.fn()
    render(<LeaveGameModal open={true} onConfirm={onConfirm} onCancel={vi.fn()} />)
    fireEvent.click(screen.getByText('Leave'))
    expect(onConfirm).toHaveBeenCalledOnce()
  })

  it('calls onCancel when backdrop is clicked', () => {
    const onCancel = vi.fn()
    const { container } = render(
      <LeaveGameModal open={true} onConfirm={vi.fn()} onCancel={onCancel} />
    )
    // Click the backdrop (outermost div)
    fireEvent.click(container.firstChild)
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('does NOT call onCancel when card content is clicked', () => {
    const onCancel = vi.fn()
    render(<LeaveGameModal open={true} onConfirm={vi.fn()} onCancel={onCancel} />)
    // Click the card (inner content) -- should not propagate
    fireEvent.click(screen.getByText('Leave game?'))
    expect(onCancel).not.toHaveBeenCalled()
  })
})
