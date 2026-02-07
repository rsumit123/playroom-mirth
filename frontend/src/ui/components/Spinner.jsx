export default function Spinner({ size = 16 }) {
  const dimension = `${size}px`
  return (
    <span
      className="inline-block animate-spin rounded-full border-2 border-slate/40 border-t-accent"
      style={{ width: dimension, height: dimension }}
    />
  )
}
