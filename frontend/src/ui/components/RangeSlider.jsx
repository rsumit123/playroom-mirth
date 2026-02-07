export default function RangeSlider({ label, value, min, max, step = 1, unit = '', onChange }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-slate/60 font-medium">{label}</span>
        <span className="text-sm font-semibold text-ink">{value}{unit}</span>
      </div>
      <input
        type="range"
        min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  )
}
