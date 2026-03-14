export default function LeaveGameModal({ open, onConfirm, onCancel }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" onClick={onCancel}>
      <div className="card p-6 mx-4 max-w-sm w-full space-y-4" onClick={(e) => e.stopPropagation()}>
        <h3 className="font-display text-lg">Leave game?</h3>
        <p className="text-sm text-slate/60">You'll lose your progress in this game.</p>
        <div className="flex gap-3 pt-1">
          <button className="btn-ghost flex-1 touch-target" onClick={onCancel}>Stay</button>
          <button className="flex-1 touch-target rounded-xl px-4 py-2.5 text-sm font-semibold bg-danger/10 text-danger hover:bg-danger/20 transition-colors" onClick={onConfirm}>Leave</button>
        </div>
      </div>
    </div>
  )
}
