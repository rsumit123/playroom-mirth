export default function LoadingOverlay({ active }) {
  if (!active) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/60 backdrop-blur-sm">
      <div className="card px-5 py-4 flex items-center gap-3">
        <span className="h-5 w-5 rounded-full border-2 border-slate/40 border-t-accent animate-spin" />
        <span className="text-sm text-slate/70">Working…</span>
      </div>
    </div>
  )
}
