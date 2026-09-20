/** What each game is called, in one place rather than a chain per screen. */
export const GAME_LABELS = {
  charades: 'Charades',
  scribble: 'Scribble',
  trivia: 'Trivia',
  poker: 'Poker',
}

export function gameLabel(gameType) {
  return GAME_LABELS[gameType] || GAME_LABELS.charades
}
