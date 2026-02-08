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
})
