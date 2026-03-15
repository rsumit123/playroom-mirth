import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render } from '@testing-library/react'
import CanvasViewer from '../CanvasViewer.jsx'

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
})

describe('CanvasViewer', () => {
  it('renders the canvas element', () => {
    const { container } = render(<CanvasViewer strokes={[]} />)
    expect(container.querySelector('canvas')).toBeTruthy()
  })

  it('renders without crashing when strokes are provided', () => {
    const strokes = [
      {
        points: [{ x: 0.1, y: 0.1 }, { x: 0.5, y: 0.5 }],
        color: '#000000',
        width: 4,
        eraser: false,
      },
    ]
    const { container } = render(<CanvasViewer strokes={strokes} />)
    expect(container.querySelector('canvas')).toBeTruthy()
  })

  it('renders without crashing when no strokes prop is passed', () => {
    const { container } = render(<CanvasViewer />)
    expect(container.querySelector('canvas')).toBeTruthy()
  })

  it('calls clearRect when strokes go from non-empty to empty (clear)', () => {
    const clearRect = vi.fn()
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
      clearRect, beginPath: vi.fn(), moveTo: vi.fn(), lineTo: vi.fn(), stroke: vi.fn(),
      strokeStyle: '', lineWidth: 0, lineCap: '', lineJoin: '',
    }))

    const stroke = { points: [{ x: 0.1, y: 0.1 }, { x: 0.5, y: 0.5 }], color: '#000', width: 4, eraser: false }
    const { rerender } = render(<CanvasViewer strokes={[stroke]} />)
    rerender(<CanvasViewer strokes={[]} />)
    expect(clearRect).toHaveBeenCalled()
  })

  it('handles undo (fewer strokes) without crashing', () => {
    const stroke1 = { points: [{ x: 0.1, y: 0.1 }, { x: 0.3, y: 0.3 }], color: '#FF0000', width: 4, eraser: false }
    const stroke2 = { points: [{ x: 0.4, y: 0.4 }, { x: 0.6, y: 0.6 }], color: '#00FF00', width: 4, eraser: false }
    const { rerender, container } = render(<CanvasViewer strokes={[stroke1, stroke2]} />)
    // Undo: remove last stroke
    rerender(<CanvasViewer strokes={[stroke1]} />)
    expect(container.querySelector('canvas')).toBeTruthy()
  })

  it('handles replayGen change (full redraw on reconnect)', () => {
    const clearRect = vi.fn()
    HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
      clearRect, beginPath: vi.fn(), moveTo: vi.fn(), lineTo: vi.fn(), stroke: vi.fn(),
      strokeStyle: '', lineWidth: 0, lineCap: '', lineJoin: '',
    }))

    const stroke = { points: [{ x: 0.1, y: 0.1 }, { x: 0.5, y: 0.5 }], color: '#000', width: 4, eraser: false }
    const { rerender } = render(<CanvasViewer strokes={[stroke]} replayGen={0} />)
    // Same strokes, different replayGen → should trigger full redraw
    rerender(<CanvasViewer strokes={[stroke]} replayGen={1} />)
    // clearRect should be called for the full redraw
    expect(clearRect).toHaveBeenCalled()
  })

  it('renders eraser strokes without crashing', () => {
    const strokes = [
      { points: [{ x: 0.1, y: 0.1 }, { x: 0.5, y: 0.5 }], color: '#FF0000', width: 4, eraser: false },
      { points: [{ x: 0.2, y: 0.2 }, { x: 0.4, y: 0.4 }], color: '#000000', width: 4, eraser: true },
    ]
    const { container } = render(<CanvasViewer strokes={strokes} />)
    expect(container.querySelector('canvas')).toBeTruthy()
  })
})
