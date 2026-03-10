const CATEGORIES = [
  { value: 'math', label: 'Math' },
  { value: 'general_knowledge', label: 'General Knowledge' },
]

export default function TriviaCategorySelector({ value, onChange }) {
  return (
    <div className="segmented">
      {CATEGORIES.map((cat) => (
        <button
          key={cat.value}
          type="button"
          className={value === cat.value ? 'segmented-option-active' : 'segmented-option'}
          onClick={() => onChange(cat.value)}
        >
          {cat.label}
        </button>
      ))}
    </div>
  )
}
