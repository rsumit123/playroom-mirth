import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import TriviaGame from '../TriviaGame.jsx'

function makeTrivia(overrides = {}) {
  return {
    question_index: 0,
    total_questions: 10,
    question_text: 'What is the capital of India?',
    options: ['Mumbai', 'New Delhi', 'Kolkata', 'Chennai'],
    time_seconds: 15,
    round_index: 1,
    ...overrides,
  }
}

function baseGame(overrides = {}) {
  return {
    trivia: makeTrivia(),
    triviaResult: null,
    triviaAnswered: false,
    triviaAnswerCount: { answered_count: 0, total_players: 2 },
    scores: {},
    selfPlayerId: 1,
    ...overrides,
  }
}

describe('TriviaGame', () => {
  it('renders waiting state when no question is present', () => {
    render(
      <TriviaGame
        game={{ trivia: null, triviaResult: null, scores: {} }}
        onAnswer={vi.fn()}
        onLeave={vi.fn()}
      />
    )
    expect(screen.getByText(/Waiting for question/i)).toBeTruthy()
  })

  it('renders the question text and all four options', () => {
    render(<TriviaGame game={baseGame()} onAnswer={vi.fn()} onLeave={vi.fn()} />)
    expect(screen.getByText('What is the capital of India?')).toBeTruthy()
    expect(screen.getByText('Mumbai')).toBeTruthy()
    expect(screen.getByText('New Delhi')).toBeTruthy()
    expect(screen.getByText('Kolkata')).toBeTruthy()
    expect(screen.getByText('Chennai')).toBeTruthy()
  })

  it('renders round and question progress indicators', () => {
    render(
      <TriviaGame
        game={baseGame({ trivia: makeTrivia({ question_index: 3, round_index: 2 }) })}
        onAnswer={vi.fn()}
        onLeave={vi.fn()}
      />
    )
    expect(screen.getByText(/Round 2/)).toBeTruthy()
    expect(screen.getByText(/Question 4 of 10/)).toBeTruthy()
  })

  it('calls onAnswer with the clicked option index', () => {
    const onAnswer = vi.fn()
    render(<TriviaGame game={baseGame()} onAnswer={onAnswer} onLeave={vi.fn()} />)
    fireEvent.click(screen.getByText('New Delhi'))
    expect(onAnswer).toHaveBeenCalledWith(1)
  })

  it('does NOT call onAnswer when already answered', () => {
    const onAnswer = vi.fn()
    render(
      <TriviaGame
        game={baseGame({ triviaAnswered: true })}
        onAnswer={onAnswer}
        onLeave={vi.fn()}
      />
    )
    fireEvent.click(screen.getByText('Mumbai'))
    expect(onAnswer).not.toHaveBeenCalled()
  })

  it('does NOT call onAnswer once the result has arrived', () => {
    const onAnswer = vi.fn()
    render(
      <TriviaGame
        game={baseGame({
          triviaResult: {
            question_index: 0,
            correct_index: 1,
            player_results: [
              { player_id: 1, answer_index: 1, correct: true, points: 150, time_taken: 2.5 },
            ],
            scores: { 1: 150 },
          },
        })}
        onAnswer={onAnswer}
        onLeave={vi.fn()}
      />
    )
    fireEvent.click(screen.getByText('Mumbai'))
    expect(onAnswer).not.toHaveBeenCalled()
  })

  it('shows answered count while players are still answering', () => {
    render(
      <TriviaGame
        game={baseGame({ triviaAnswerCount: { answered_count: 1, total_players: 3 } })}
        onAnswer={vi.fn()}
        onLeave={vi.fn()}
      />
    )
    expect(screen.getByText(/1 of 3 answered/i)).toBeTruthy()
  })

  it('shows the Results heading and player scores in result phase', () => {
    render(
      <TriviaGame
        game={baseGame({
          triviaResult: {
            question_index: 0,
            correct_index: 1,
            player_results: [
              { player_id: 1, answer_index: 1, correct: true, points: 175, time_taken: 1.2 },
              { player_id: 2, answer_index: 2, correct: false, points: 0, time_taken: null },
            ],
            scores: { 1: 175, 2: 0 },
          },
        })}
        playerNames={{ 1: 'Alice', 2: 'Bob' }}
        onAnswer={vi.fn()}
        onLeave={vi.fn()}
      />
    )
    // Results header
    expect(screen.getAllByText(/Results/i).length).toBeGreaterThan(0)
    // Player names appear (Alice also shows on her picked option as a chip, hence getAll)
    expect(screen.getAllByText(/Alice/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Bob/).length).toBeGreaterThan(0)
    // Correct answerer shows their points in the result list
    expect(screen.getByText('+175')).toBeTruthy()
  })

  it('marks self with the "(You)" suffix in result rows', () => {
    render(
      <TriviaGame
        game={baseGame({
          selfPlayerId: 1,
          triviaResult: {
            question_index: 0,
            correct_index: 1,
            player_results: [
              { player_id: 1, answer_index: 1, correct: true, points: 100, time_taken: 5 },
            ],
            scores: { 1: 100 },
          },
        })}
        playerNames={{ 1: 'Alice' }}
        onAnswer={vi.fn()}
        onLeave={vi.fn()}
      />
    )
    expect(screen.getByText(/\(You\)/)).toBeTruthy()
  })

  it('opens the leave modal when the leave button is clicked', () => {
    render(<TriviaGame game={baseGame()} onAnswer={vi.fn()} onLeave={vi.fn()} />)
    fireEvent.click(screen.getByLabelText(/Leave game/i))
    expect(screen.getByText(/Leave game\?/)).toBeTruthy()
  })

  it('calls onLeave when leave is confirmed in the modal', () => {
    const onLeave = vi.fn()
    render(<TriviaGame game={baseGame()} onAnswer={vi.fn()} onLeave={onLeave} />)
    fireEvent.click(screen.getByLabelText(/Leave game/i))
    fireEvent.click(screen.getByText('Leave'))
    expect(onLeave).toHaveBeenCalledOnce()
  })
})
