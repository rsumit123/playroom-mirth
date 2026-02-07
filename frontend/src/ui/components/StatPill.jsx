export default function StatPill({ label, value }) {
  return (
    <div className="px-3 py-2 rounded-full bg-mist text-slate text-xs font-semibold uppercase tracking-wider">
      {label}: <span className="text-ink">{value}</span>
    </div>
  )
}
