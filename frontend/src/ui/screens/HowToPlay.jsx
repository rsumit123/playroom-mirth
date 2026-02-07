export default function HowToPlay({ onClose }) {
  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm flex items-end sm:items-center justify-center p-4 sm:p-6 z-50">
      <div className="card p-6 w-full max-w-xl space-y-5 rounded-t-3xl sm:rounded-xl">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-2xl">How to Play</h2>
          <button className="text-sm text-slate/70" onClick={onClose}>Close</button>
        </div>
        <div className="space-y-4 text-sm text-slate/80">
          <div>
            <div className="font-semibold text-ink">1. Describe</div>
            <div>Each turn, one player describes the word without saying it.</div>
          </div>
          <div>
            <div className="font-semibold text-ink">2. Guess</div>
            <div>Everyone else guesses in chat. First correct guess wins points.</div>
          </div>
          <div>
            <div className="font-semibold text-ink">3. Rotate</div>
            <div>Turns rotate so everyone gets a chance to describe.</div>
          </div>
        </div>
        <button className="btn-primary w-full" onClick={onClose}>Got it</button>
      </div>
    </div>
  )
}
