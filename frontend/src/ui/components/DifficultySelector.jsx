const LEVELS = [
  { value: 0, label: 'Mixed' },
  { value: 1, label: 'Easy' },
  { value: 2, label: 'Medium' },
  { value: 3, label: 'Hard' },
]

export default function DifficultySelector({ value, onChange }) {
  return (
    <div className="segmented">
      {LEVELS.map((lvl) => (
        <button
          key={lvl.value}
          type="button"
          className={value === lvl.value ? 'segmented-option-active' : 'segmented-option'}
          onClick={() => onChange(lvl.value)}
        >
          {lvl.label}
        </button>
      ))}
    </div>
  )
}
