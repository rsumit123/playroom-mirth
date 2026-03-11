const CATEGORIES = [
  { value: 'general_knowledge', label: 'General Knowledge', icon: '🧠', desc: 'All topics' },
  { value: 'science', label: 'Science', icon: '🔬' },
  { value: 'general', label: 'General', icon: '💡' },
  { value: 'history', label: 'History', icon: '📜' },
  { value: 'geography', label: 'Geography', icon: '🌍' },
  { value: 'sports', label: 'Sports', icon: '⚽' },
  { value: 'entertainment', label: 'Entertainment', icon: '🎬' },
  { value: 'mythology', label: 'Mythology', icon: '🛕' },
  { value: 'food', label: 'Food & Cuisine', icon: '🍛' },
  { value: 'politics', label: 'Politics', icon: '🏛️' },
  { value: 'math', label: 'Math', icon: '🔢' },
]

export default function TriviaCategorySelector({ value, onChange, readOnly = false }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
      {CATEGORIES.map((cat) => {
        const selected = value === cat.value
        return (
          <button
            key={cat.value}
            type="button"
            disabled={readOnly}
            className={`relative rounded-xl border-2 px-3 py-3 text-center transition-all select-none ${
              selected
                ? 'border-accent bg-accent/10 ring-1 ring-accent shadow-sm'
                : readOnly
                  ? 'border-black/5 bg-white/60 opacity-60'
                  : 'border-black/5 bg-white/60 hover:border-accent/30 hover:shadow-sm cursor-pointer active:scale-[0.97]'
            }`}
            onClick={() => !readOnly && onChange(cat.value)}
          >
            <div className="text-2xl mb-1">{cat.icon}</div>
            <div className={`text-xs font-semibold leading-tight ${selected ? 'text-accent' : 'text-ink'}`}>
              {cat.label}
            </div>
            {cat.desc && <div className="text-[10px] text-slate/50 mt-0.5">{cat.desc}</div>}
          </button>
        )
      })}
    </div>
  )
}
