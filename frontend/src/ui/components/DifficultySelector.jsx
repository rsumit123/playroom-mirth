const LEVELS = [
  { value: 0, label: 'Mixed' },
  { value: 1, label: 'Easy' },
  { value: 2, label: 'Medium' },
  { value: 3, label: 'Hard' },
]

export default function DifficultySelector({ value, onChange, hideMixed = false }) {
  const levels = hideMixed ? LEVELS.filter((l) => l.value !== 0) : LEVELS
  return (
    <div className="segmented">
      {levels.map((lvl) => (
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
