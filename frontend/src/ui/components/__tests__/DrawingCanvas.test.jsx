import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import DrawingCanvas from '../DrawingCanvas.jsx'

// jsdom doesn't implement canvas, so stub getContext and pointer capture
beforeEach(() => {
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
    clearRect: vi.fn(),
    beginPath: vi.fn(),
    moveTo: vi.fn(),
    lineTo: vi.fn(),
    stroke: vi.fn(),
    strokeStyle: '',
    lineWidth: 0,
    lineCap: '',
    lineJoin: '',
  }))
  HTMLCanvasElement.prototype.setPointerCapture = vi.fn()
})

describe('DrawingCanvas', () => {
  it('renders the canvas element', () => {
    const { container } = render(<DrawingCanvas onStroke={vi.fn()} onClear={vi.fn()} />)
    expect(container.querySelector('canvas')).toBeTruthy()
  })

  it('renders all five color buttons', () => {
    const { container } = render(<DrawingCanvas onStroke={vi.fn()} onClear={vi.fn()} />)
    // There are 5 color swatch circular buttons (h-8 w-8 rounded-full) with backgroundColor style
    const colorButtons = container.querySelectorAll('button[style]')
    const colorBtns = Array.from(colorButtons).filter(b => b.style.backgroundColor)
    expect(colorBtns.length).toBe(5)
  })

  it('renders Eraser, Undo, and Clear tool buttons', () => {
    render(<DrawingCanvas onStroke={vi.fn()} onClear={vi.fn()} />)
    expect(screen.getByText('Eraser')).toBeInTheDocument()
    expect(screen.getByText('Undo')).toBeInTheDocument()
    expect(screen.getByText('Clear')).toBeInTheDocument()
  })

  it('calls onClear when Clear button is clicked', () => {
    const onClear = vi.fn()
    render(<DrawingCanvas onStroke={vi.fn()} onClear={onClear} />)
    fireEvent.click(screen.getByText('Clear'))
    expect(onClear).toHaveBeenCalledTimes(1)
  })

  it('toggles eraser active state on click', () => {
    render(<DrawingCanvas onStroke={vi.fn()} onClear={vi.fn()} />)
    const eraserBtn = screen.getByText('Eraser')
    // Initially not active (class does not contain bg-accent)
    expect(eraserBtn.className).not.toContain('bg-accent')
    fireEvent.click(eraserBtn)
    // After click, eraser becomes active
    expect(eraserBtn.className).toContain('bg-accent')
  })
})
