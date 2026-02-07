export default function CircularTimer({ remaining, total, size = 48 }) {
  const fraction = total > 0 ? Math.max(0, remaining / total) : 0
  const urgent = remaining <= 10 && remaining > 0
  const radius = (size - 6) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - fraction)

  return (
    <div
      className={`relative inline-flex items-center justify-center shrink-0 ${urgent ? 'animate-countdown-shake' : ''}`}
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" strokeWidth="3"
          className="stroke-mist"
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" strokeWidth="3" strokeLinecap="round"
          strokeDasharray={circumference} strokeDashoffset={offset}
          className={`transition-all duration-1000 ease-linear ${urgent ? 'stroke-danger' : 'stroke-accent'}`}
        />
      </svg>
      <span className={`absolute font-semibold ${size >= 60 ? 'text-lg' : 'text-sm'} ${urgent ? 'text-danger' : 'text-ink'}`}>
        {remaining}
      </span>
    </div>
  )
}
