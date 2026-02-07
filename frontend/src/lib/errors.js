export function formatError(message) {
  if (!message) return 'Something went wrong'
  if (typeof message !== 'string') return 'Something went wrong'
  if (message.includes('Room is full')) return 'Room is full. Try another code.'
  if (message.includes('Authentication required')) return 'Please sign in or play as guest.'
  if (message.includes('Guest limit')) return 'Guest limit reached. Please sign in.'
  if (message.includes('Active game limit')) return 'Active game limit reached. Leave a room from the home screen first.'
  if (message.includes('Hint contains target')) return 'Hint blocked: avoid using the word or partials.'
  if (message.includes('Room already in game')) return 'Game already started. Please wait for the next one.'
  return message
}
