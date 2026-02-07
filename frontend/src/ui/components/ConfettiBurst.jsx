import { useEffect, useState } from 'react'

export default function ConfettiBurst({ trigger }) {
  const [bursts, setBursts] = useState([])

  useEffect(() => {
    if (!trigger) return
    const id = Date.now()
    const pieces = Array.from({ length: 16 }).map((_, idx) => ({
      id: `${id}-${idx}`,
      x: Math.random() * 200 - 100,
      y: Math.random() * -120 - 40,
      r: Math.random() * 360,
      d: Math.random() * 0.6 + 0.4
    }))
    setBursts((prev) => [...prev, { id, pieces }])
    const t = setTimeout(() => {
      setBursts((prev) => prev.filter((b) => b.id !== id))
    }, 1200)
    return () => clearTimeout(t)
  }, [trigger])

  return (
    <div className="pointer-events-none fixed inset-0 z-40 flex items-center justify-center">
      {bursts.map((burst) => (
        <div key={burst.id} className="relative h-1 w-1">
          {burst.pieces.map((p) => (
            <span
              key={p.id}
              className="absolute h-2 w-2 rounded-sm bg-accent"
              style={{
                transform: `translate(${p.x}px, ${p.y}px) rotate(${p.r}deg)`,
                opacity: p.d
              }}
            />
          ))}
        </div>
      ))}
    </div>
  )
}
