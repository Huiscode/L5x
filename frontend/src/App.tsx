import { useEffect, useState } from 'react'

type HealthResponse = {
  status: string
  service: string
  timestamp: string
  mode: string
}

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/health')
        if (!response.ok) {
          throw new Error(`Backend health failed: ${response.status}`)
        }
        const data = (await response.json()) as HealthResponse
        setHealth(data)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown backend error'
        setError(message)
      }
    }

    void fetchHealth()
  }, [])

  return (
    <main className="shell">
      <section className="card">
        <h1>app-L5x</h1>
        <p className="subtitle">Offline L5X engineering workspace</p>

        <div className="status-block">
          <h2>Backend Status</h2>
          {health ? (
            <ul>
              <li>
                <strong>Status:</strong> {health.status}
              </li>
              <li>
                <strong>Service:</strong> {health.service}
              </li>
              <li>
                <strong>Mode:</strong> {health.mode}
              </li>
              <li>
                <strong>Timestamp:</strong> {health.timestamp}
              </li>
            </ul>
          ) : (
            <p>{error ?? 'Connecting to local backend...'}</p>
          )}
        </div>
      </section>
    </main>
  )
}
