import { useRef, useEffect, useCallback } from 'react'

const DEFAULT_BRUSH_RATIO = 0.005
const DEFAULT_ERASER_RATIO = 0.025

export default function CanvasViewer({ strokes = [], replayGen = 0 }) {
  const canvasRef = useRef(null)
  const lastDrawnRef = useRef(0)
  const lastGenRef = useRef(0)

  const resizeCanvas = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const parent = canvas.parentElement
    const w = parent.clientWidth
    const h = parent.clientHeight
    if (w === 0 || h === 0) return
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w
      canvas.height = h
      // Redraw all strokes after resize
      lastDrawnRef.current = 0
      drawStrokes(canvas, strokes, 0)
      lastDrawnRef.current = strokes.length
    }
  }, [strokes])

  // Use ResizeObserver to detect all size changes (including mobile keyboard)
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const parent = canvas.parentElement
    resizeCanvas()
    const ro = new ResizeObserver(() => resizeCanvas())
    ro.observe(parent)
    return () => ro.disconnect()
  }, [resizeCanvas])

  // Draw new strokes incrementally
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    if (strokes.length === 0) {
      // Canvas was cleared
      const ctx = canvas.getContext('2d')
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      lastDrawnRef.current = 0
      return
    }

    if (replayGen !== lastGenRef.current) {
      // Full replay (reconnection) — redraw everything from scratch
      const ctx = canvas.getContext('2d')
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      drawStrokes(canvas, strokes, 0)
      lastDrawnRef.current = strokes.length
      lastGenRef.current = replayGen
    } else if (strokes.length < lastDrawnRef.current) {
      // Undo — redraw from scratch
      const ctx = canvas.getContext('2d')
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      drawStrokes(canvas, strokes, 0)
      lastDrawnRef.current = strokes.length
    } else if (strokes.length > lastDrawnRef.current) {
      drawStrokes(canvas, strokes, lastDrawnRef.current)
      lastDrawnRef.current = strokes.length
    }
  }, [strokes, replayGen])

  return (
    <div className="h-full flex items-center justify-center">
      <div className="bg-white rounded-xl border border-black/10 overflow-hidden relative" style={{ aspectRatio: '4/3', maxWidth: '100%', maxHeight: '100%', width: '100%' }}>
        <canvas
          ref={canvasRef}
          className="absolute inset-0 w-full h-full"
        />
      </div>
    </div>
  )
}

function drawStrokes(canvas, strokes, fromIndex) {
  const ctx = canvas.getContext('2d')
  const w = canvas.width
  const h = canvas.height

  for (let i = fromIndex; i < strokes.length; i++) {
    const s = strokes[i]
    const pts = s.points || []
    if (pts.length < 2) continue

    ctx.beginPath()
    ctx.strokeStyle = s.eraser ? '#FFFFFF' : (s.color || '#000000')
    // Width is a normalized ratio — scale to this canvas width
    ctx.lineWidth = (s.width || DEFAULT_BRUSH_RATIO) * w
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.moveTo(pts[0].x * w, pts[0].y * h)
    for (let j = 1; j < pts.length; j++) {
      ctx.lineTo(pts[j].x * w, pts[j].y * h)
    }
    ctx.stroke()
  }
}
