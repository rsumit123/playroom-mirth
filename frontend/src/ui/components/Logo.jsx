export default function Logo() {
  return (
    <div className="flex items-center gap-3">
      <div className="h-11 w-11 rounded-xl bg-accent text-white flex items-center justify-center font-display text-xl shadow-soft">
        CC
      </div>
      <div>
        <div className="font-display text-2xl">Charade Chat</div>
        <div className="text-xs uppercase tracking-[0.25em] text-slate/60">Play. Guess. Repeat.</div>
      </div>
    </div>
  )
}
