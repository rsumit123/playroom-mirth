import PlayerAvatar from './PlayerAvatar.jsx'

export default function ChatBubble({ playerName, message, isCorrect, isSelf }) {
  if (isCorrect) {
    return (
      <div className="flex items-start gap-2 animate-slide-up">
        <PlayerAvatar name={playerName} size="sm" />
        <div className="chat-bubble-correct">
          <span className="mr-1">&#10003;</span>
          <strong>{playerName}</strong> guessed it!
        </div>
      </div>
    )
  }

  return (
    <div className={`flex items-start gap-2 animate-slide-up ${isSelf ? 'flex-row-reverse' : ''}`}>
      <PlayerAvatar name={playerName} size="sm" />
      <div className={isSelf ? 'chat-bubble-self' : 'chat-bubble-other'}>
        {!isSelf && <div className="text-[10px] text-slate/50 font-medium mb-0.5">{playerName}</div>}
        <span>{message}</span>
      </div>
    </div>
  )
}
