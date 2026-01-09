import { useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { apiClient, getAccessToken, setAccessToken } from '../api/client'

type LoginResponse = {
  access_token: string
}

export default function LoginPage() {
  const navigate = useNavigate()
  const existingToken = getAccessToken()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canSubmit = useMemo(() => {
    return email.trim().length > 0 && password.length > 0 && !isSubmitting
  }, [email, password, isSubmitting])

  if (existingToken) {
    return <Navigate to="/home" replace />
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!canSubmit) return

    setIsSubmitting(true)
    setError(null)
    try {
      const res = await apiClient.post<LoginResponse>('/v1/auth/login/', {
        email: email.trim(),
        password,
      })
      setAccessToken(res.data.access_token)
      navigate('/home', { replace: true })
    } catch (err: unknown) {
      setError('Invalid credentials or server error.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main style={{ maxWidth: 420, margin: '2rem auto', padding: '0 1rem' }}>
      <h1>Log in</h1>
      <form onSubmit={onSubmit}>
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
              style={{ width: '100%' }}
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              style={{ width: '100%' }}
            />
          </label>

          <button type="submit" disabled={!canSubmit}>
            {isSubmitting ? 'Logging in…' : 'Log in'}
          </button>

          {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}
        </div>
      </form>
    </main>
  )
}
