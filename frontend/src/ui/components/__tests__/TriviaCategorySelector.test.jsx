import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TriviaCategorySelector from '../TriviaCategorySelector.jsx'

const ALL_CATEGORY_LABELS = [
  'General Knowledge',
  'Science',
  'General',
  'History',
  'Geography',
  'Sports',
  'Entertainment',
  'Mythology',
  'Food & Cuisine',
  'Politics',
  'War & Defense',
  'Current Affairs',
  'Math',
]

describe('TriviaCategorySelector', () => {
  it('renders every category label', () => {
    render(<TriviaCategorySelector value="math" onChange={vi.fn()} />)
    for (const label of ALL_CATEGORY_LABELS) {
      expect(screen.getByText(label)).toBeTruthy()
    }
  })

  it('renders 13 selectable buttons', () => {
    const { container } = render(<TriviaCategorySelector value="math" onChange={vi.fn()} />)
    expect(container.querySelectorAll('button').length).toBe(13)
  })

  it('calls onChange with the category value when clicked', () => {
    const onChange = vi.fn()
    render(<TriviaCategorySelector value="math" onChange={onChange} />)
    fireEvent.click(screen.getByText('Science'))
    expect(onChange).toHaveBeenCalledWith('science')
  })

  it('passes the correct value for each category', () => {
    const onChange = vi.fn()
    render(<TriviaCategorySelector value="math" onChange={onChange} />)
    fireEvent.click(screen.getByText('Current Affairs'))
    expect(onChange).toHaveBeenLastCalledWith('current_affairs')
    fireEvent.click(screen.getByText('War & Defense'))
    expect(onChange).toHaveBeenLastCalledWith('defense')
    fireEvent.click(screen.getByText('General Knowledge'))
    expect(onChange).toHaveBeenLastCalledWith('general_knowledge')
  })

  it('applies selected styling to the active category', () => {
    render(<TriviaCategorySelector value="science" onChange={vi.fn()} />)
    const science = screen.getByText('Science').closest('button')
    expect(science.className).toMatch(/border-accent/)
  })

  it('does not call onChange when readOnly is set', () => {
    const onChange = vi.fn()
    render(<TriviaCategorySelector value="math" onChange={onChange} readOnly />)
    fireEvent.click(screen.getByText('Science'))
    expect(onChange).not.toHaveBeenCalled()
  })

  it('disables all buttons when readOnly is set', () => {
    const { container } = render(
      <TriviaCategorySelector value="math" onChange={vi.fn()} readOnly />
    )
    const buttons = container.querySelectorAll('button')
    buttons.forEach((b) => expect(b.disabled).toBe(true))
  })

  it('renders the "All topics" description only for General Knowledge', () => {
    render(<TriviaCategorySelector value="math" onChange={vi.fn()} />)
    expect(screen.getByText('All topics')).toBeTruthy()
  })
})
