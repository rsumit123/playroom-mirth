const AVATAR_COLORS = [
  '#2C6E6A', '#D4A843', '#7C3AED', '#EF4444',
  '#3B82F6', '#EC4899', '#F59E0B', '#10B981',
]

export default function PlayerAvatar({ name, size = 'md', className = '' }) {
  const initial = (name || '?')[0].toUpperCase()
  const colorIndex = (name || '').split('').reduce((acc, c) => acc + c.charCodeAt(0), 0) % AVATAR_COLORS.length
  const bg = AVATAR_COLORS[colorIndex]
  const sizeMap = { xs: 'h-4 w-4 text-[8px]', sm: 'h-7 w-7 text-xs', md: 'h-9 w-9 text-sm', lg: 'h-12 w-12 text-lg' }
  return (
    <div
      className={`${sizeMap[size]} rounded-full flex items-center justify-center font-semibold text-white shrink-0 ${className}`}
      style={{ backgroundColor: bg }}
    >
      {initial}
    </div>
  )
}
