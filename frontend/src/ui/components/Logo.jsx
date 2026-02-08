export default function Logo({ compact = false, onClick, className = '' }) {
  const Wrapper = onClick ? 'button' : 'div'
  const sizeClasses = compact ? 'h-9 w-9 text-lg' : 'h-11 w-11 text-xl'
  const titleClasses = compact ? 'text-lg' : 'text-2xl'
  return (
    <Wrapper
      type={onClick ? 'button' : undefined}
      className={`flex items-center gap-3 text-left ${className}`}
      onClick={onClick}
    >
      <div className={`${sizeClasses} rounded-xl bg-accent text-white flex items-center justify-center font-display shadow-soft`}>
        PR
      </div>
      <div className={compact ? 'hidden sm:block' : ''}>
        <div className={`font-display ${titleClasses}`}>PlayRoom</div>
        <div className="text-xs uppercase tracking-[0.25em] text-slate/60">Party Games</div>
      </div>
    </Wrapper>
  )
}
