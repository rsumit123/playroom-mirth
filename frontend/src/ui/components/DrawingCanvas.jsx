import { useRef, useEffect, useState, useCallback } from 'react'

const COLORS = ['#000000', '#e74c3c', '#3498db', '#27ae60', '#f39c12']
// Normalized width ratios (relative to canvas width)
const BRUSH_RATIO = 0.005   // ~4px on a 800px canvas
const ERASER_RATIO = 0.025  // ~20px on a 800px canvas

export default function DrawingCanvas({ onStroke, onClear, onUndo }) {
  const canvasRef = useRef(null)
  const [color, setColor] = useState(COLORS[0])
  const [isErasing, setIsErasing] = useState(false)
  const drawing = useRef(false)
  const points = useRef([])
  const strokesRef = useRef([])

  const getPos = useCallback((e) => {
    const canvas = canvasRef.current
    if (!canvas) return null
    const rect = canvas.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const y = (e.clientY - rect.top) / rect.height
    return { x, y }
  }, [])

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
      redrawAll()
    }
  }, [])

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

  function redrawAll() {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    for (const s of strokesRef.current) {
      drawStroke(ctx, s, canvas.width, canvas.height)
    }
  }

  function drawStroke(ctx, stroke, w, h) {
    if (!stroke.points || stroke.points.length < 2) return
    ctx.beginPath()
    ctx.strokeStyle = stroke.eraser ? '#FFFFFF' : stroke.color
    // Width is stored as a normalized ratio — scale to canvas width
    ctx.lineWidth = (stroke.width || BRUSH_RATIO) * w
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.moveTo(stroke.points[0].x * w, stroke.points[0].y * h)
    for (let i = 1; i < stroke.points.length; i++) {
      ctx.lineTo(stroke.points[i].x * w, stroke.points[i].y * h)
    }
    ctx.stroke()
  }

  function handlePointerDown(e) {
    e.preventDefault()
    const canvas = canvasRef.current
    if (!canvas) return
    canvas.setPointerCapture(e.pointerId)
    drawing.current = true
    const pos = getPos(e)
    if (pos) points.current = [pos]
  }

  function handlePointerMove(e) {
    if (!drawing.current) return
    e.preventDefault()
    const pos = getPos(e)
    if (!pos) return
    points.current.push(pos)
    // Draw live
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const pts = points.current
    if (pts.length < 2) return
    const prev = pts[pts.length - 2]
    const curr = pts[pts.length - 1]
    ctx.beginPath()
    ctx.strokeStyle = isErasing ? '#FFFFFF' : color
    ctx.lineWidth = (isErasing ? ERASER_RATIO : BRUSH_RATIO) * canvas.width
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.moveTo(prev.x * canvas.width, prev.y * canvas.height)
    ctx.lineTo(curr.x * canvas.width, curr.y * canvas.height)
    ctx.stroke()
  }

  function handlePointerUp(e) {
    if (!drawing.current) return
    drawing.current = false
    const stroke = {
      points: points.current,
      color: color,
      width: isErasing ? ERASER_RATIO : BRUSH_RATIO,
      eraser: isErasing,
    }
    strokesRef.current.push(stroke)
    onStroke?.(stroke)
    points.current = []
  }

  function handleClear() {
    strokesRef.current = []
    const canvas = canvasRef.current
    if (canvas) {
      const ctx = canvas.getContext('2d')
      ctx.clearRect(0, 0, canvas.width, canvas.height)
    }
    onClear?.()
  }

  function handleUndo() {
    if (strokesRef.current.length === 0) return
    strokesRef.current.pop()
    redrawAll()
    onUndo?.()
  }

  return (
    <div className="flex flex-col h-full">
      {/* Canvas area — fixed 4:3 aspect ratio for cross-platform consistency */}
      <div className="flex-1 flex items-center justify-center min-h-0">
        <div className="bg-white rounded-xl border border-black/10 overflow-hidden relative touch-none" style={{ aspectRatio: '4/3', maxWidth: '100%', maxHeight: '100%', width: '100%' }}>
          <canvas
            ref={canvasRef}
            className="absolute inset-0 w-full h-full cursor-crosshair"
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
          />
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center flex-wrap gap-2 pt-2 px-1">
        <div className="flex items-center gap-1">
          {COLORS.map((c) => (
            <button
              key={c}
              type="button"
              className={`h-7 w-7 rounded-full border-2 transition ${
                !isErasing && color === c ? 'border-accent scale-110' : 'border-transparent'
              }`}
              style={{ backgroundColor: c }}
              onClick={() => { setColor(c); setIsErasing(false) }}
            />
          ))}
        </div>
        <div className="flex items-center gap-1 ml-auto">
          <button
            type="button"
            className={`h-7 px-2 rounded-lg text-[11px] font-medium border transition ${
              isErasing ? 'bg-accent text-white border-accent' : 'bg-white border-black/10 text-slate/70'
            }`}
            onClick={() => setIsErasing(!isErasing)}
          >
            Eraser
          </button>
          <button
            type="button"
            className="h-7 px-2 rounded-lg text-[11px] font-medium border border-black/10 bg-white text-slate/70"
            onClick={handleUndo}
          >
            Undo
          </button>
          <button
            type="button"
            className="h-7 px-2 rounded-lg text-[11px] font-medium border border-danger/20 bg-white text-danger/70"
            onClick={handleClear}
          >
            Clear
          </button>
        </div>
      </div>
    </div>
  )
}
