export default function TimerSweep() {
  return (
    <div className="relative h-1 w-full overflow-hidden rounded-full bg-mist">
      <span className="absolute inset-y-0 left-0 w-1/3 bg-accent/40 animate-sweep" />
    </div>
  )
}
