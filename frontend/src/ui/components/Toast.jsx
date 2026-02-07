import { useEffect } from 'react'

export default function Toast({ message, onClose }) {
  useEffect(() => {
    if (!message) return
    const timer = setTimeout(() => onClose?.(), 4000)
    return () => clearTimeout(timer)
  }, [message, onClose])

  if (!message) return null

  return (
    <div className="fixed bottom-6 left-4 right-4 sm:left-1/2 sm:-translate-x-1/2 sm:right-auto sm:w-auto z-50 animate-slide-up">
      <div className="card px-4 py-3 flex items-center justify-between gap-4 shadow-hover">
        <div className="text-sm text-slate/80">{message}</div>
        <button className="text-xs text-slate/50 shrink-0 touch-target" onClick={onClose}>
          Dismiss
        </button>
      </div>
    </div>
  )
}
