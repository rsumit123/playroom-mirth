import { useState, useCallback, useRef, useEffect } from 'react'

const ALERT_STYLES = {
  accent: 'bg-accent text-white',
  success: 'bg-correct text-white',
  warning: 'bg-gold text-ink',
  info: 'bg-ink/80 text-white',
}

function AlertItem({ alert, onDone }) {
  const [exiting, setExiting] = useState(false)

  useEffect(() => {
    const fadeTimer = setTimeout(() => setExiting(true), alert.duration - 300)
    const removeTimer = setTimeout(() => onDone(alert.id), alert.duration)
    return () => {
      clearTimeout(fadeTimer)
      clearTimeout(removeTimer)
    }
  }, [alert.id, alert.duration, onDone])

  return (
    <div
      className={`px-4 py-2 rounded-xl shadow-soft text-sm font-semibold ${ALERT_STYLES[alert.type] || ALERT_STYLES.info} ${exiting ? 'animate-alert-out' : 'animate-alert-in'}`}
    >
      {alert.icon && <span className="mr-1.5">{alert.icon}</span>}
      {alert.text}
    </div>
  )
}

export function useGameAlerts() {
  const [alerts, setAlerts] = useState([])
  const idRef = useRef(0)

  const addAlert = useCallback((text, type = 'info', icon = null, duration = 3000) => {
    const id = ++idRef.current
    setAlerts((prev) => [...prev.slice(-4), { id, text, type, icon, duration }])
  }, [])

  const removeAlert = useCallback((id) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id))
  }, [])

  return { alerts, addAlert, removeAlert }
}

export default function GameAlerts({ alerts, onRemove }) {
  if (alerts.length === 0) return null

  return (
    <div className="shrink-0 flex flex-col items-center gap-1.5 px-4 py-1.5">
      {alerts.map((alert) => (
        <AlertItem key={alert.id} alert={alert} onDone={onRemove} />
      ))}
    </div>
  )
}
