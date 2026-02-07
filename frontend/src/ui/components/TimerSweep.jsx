export default function TimerSweep({ remaining, total }) {
  const fraction = total > 0 ? Math.max(0, Math.min(1, remaining / total)) : 0
  const urgent = total > 0 && remaining <= 10

  return (
    <div className="relative h-2 w-full overflow-hidden rounded-full bg-mist">
      <span
        className={`absolute inset-y-0 left-0 rounded-full transition-all duration-1000 ease-linear ${urgent ? 'bg-red-400' : 'bg-accent/60'}`}
        style={{ width: `${fraction * 100}%` }}
      />
    </div>
  )
}
