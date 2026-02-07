import { useEffect, useState } from 'react'

const COLORS = ['#f59e0b', '#ef4444', '#3b82f6', '#10b981', '#8b5cf6', '#ec4899', '#06b6d4']

export default function ConfettiBurst({ trigger }) {
  const [bursts, setBursts] = useState([])

  useEffect(() => {
    if (!trigger) return
    const id = Date.now()
    const pieces = Array.from({ length: 24 }).map((_, idx) => ({
      id: `${id}-${idx}`,
      x: Math.random() * 300 - 150,
      y: Math.random() * -200 - 60,
      r: Math.random() * 720 - 360,
      d: Math.random() * 0.4 + 0.6,
      color: COLORS[idx % COLORS.length],
      size: Math.random() * 6 + 4,
      delay: Math.random() * 0.15
    }))
    setBursts((prev) => [...prev, { id, pieces }])
    const t = setTimeout(() => {
      setBursts((prev) => prev.filter((b) => b.id !== id))
    }, 1500)
    return () => clearTimeout(t)
  }, [trigger])

  return (
    <div className="pointer-events-none fixed inset-0 z-40 flex items-center justify-center">
      <style>{`
        @keyframes confetti-burst {
          0% {
            transform: translate(0, 0) rotate(0deg) scale(1);
            opacity: 1;
          }
          100% {
            transform: translate(var(--cx), var(--cy)) rotate(var(--cr)) scale(0.3);
            opacity: 0;
          }
        }
      `}</style>
      {bursts.map((burst) => (
        <div key={burst.id} className="relative h-1 w-1">
          {burst.pieces.map((p) => (
            <span
              key={p.id}
              style={{
                position: 'absolute',
                width: `${p.size}px`,
                height: `${p.size}px`,
                borderRadius: p.size > 7 ? '50%' : '2px',
                backgroundColor: p.color,
                '--cx': `${p.x}px`,
                '--cy': `${p.y}px`,
                '--cr': `${p.r}deg`,
                animation: `confetti-burst ${p.d}s ease-out ${p.delay}s forwards`
              }}
            />
          ))}
        </div>
      ))}
    </div>
  )
}
