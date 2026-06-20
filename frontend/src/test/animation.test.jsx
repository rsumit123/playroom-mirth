import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import ConfettiBurst from '../ui/components/ConfettiBurst.jsx'
import Welcome from '../ui/screens/Welcome.jsx'
import { formatError } from '../lib/errors.js'

describe('animation components', () => {
  it('renders ConfettiBurst when triggered', () => {
    const { container, rerender } = render(<ConfettiBurst trigger={0} />)
    expect(container.querySelectorAll('span').length).toBe(0)
    rerender(<ConfettiBurst trigger={1} />)
    expect(container.querySelectorAll('span').length).toBeGreaterThan(0)
  })

  it('renders Welcome with Mirth branding', () => {
    const { getByText } = render(<Welcome onGuest={() => {}} onGoogleLogin={() => {}} onHowTo={() => {}} />)
    expect(getByText('Play as Guest')).toBeInTheDocument()
  })

  it('formats known errors', () => {
    expect(formatError('Room is full')).toMatch('Room is full')
    expect(formatError('Authentication required')).toMatch('sign in')
  })
})
