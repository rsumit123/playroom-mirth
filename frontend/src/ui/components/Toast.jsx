export default function Toast({ message, onClose }) {
  if (!message) return null
  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
      <div className="card px-4 py-3 flex items-center gap-3 animate-pop">
        <div className="text-sm text-slate/80">{message}</div>
        <button className="text-xs text-slate/60" onClick={onClose}>Dismiss</button>
      </div>
    </div>
  )
}
