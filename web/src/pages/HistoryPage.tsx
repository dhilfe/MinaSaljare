import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { apiClient, clearAccessToken } from '../api/client'

type Child = {
  id: string
  first_name: string
  last_initial: string
}

type ChildRef = {
  id: string
  first_name: string
  last_initial: string
}

type YearlyCampaignBreakdown = {
  campaign_id: string
  campaign_name: string
  total_units_sold: number
  total_sales_amount: string
}

type ChildYearlyStats = {
  child: ChildRef
  year: number
  total_units_sold: number
  total_sales_amount: string
  campaigns: YearlyCampaignBreakdown[]
}

function childShortName(child: { first_name: string; last_initial: string }) {
  return child.last_initial ? `${child.first_name} ${child.last_initial}` : child.first_name
}

export default function HistoryPage() {
  const navigate = useNavigate()

  const defaultYear = useMemo(() => new Date().getFullYear(), [])

  const [year, setYear] = useState<number>(defaultYear)
  const [children, setChildren] = useState<Child[]>([])
  const [statsByChildId, setStatsByChildId] = useState<Record<string, ChildYearlyStats>>({})

  const [isLoadingChildren, setIsLoadingChildren] = useState(true)
  const [isLoadingStats, setIsLoadingStats] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    async function loadChildren() {
      setIsLoadingChildren(true)
      setError(null)
      try {
        const res = await apiClient.get<Child[]>('/v1/children/')
        if (!isMounted) return
        setChildren(res.data)
      } catch (err: any) {
        if (!isMounted) return
        const status = err?.response?.status
        if (status === 401) {
          clearAccessToken()
          navigate('/login', { replace: true })
          return
        }
        setError('Kunde inte hämta barn. Försök igen.')
        setChildren([])
      } finally {
        if (isMounted) setIsLoadingChildren(false)
      }
    }

    void loadChildren()
    return () => {
      isMounted = false
    }
  }, [navigate])

  useEffect(() => {
    let isMounted = true

    async function loadStats() {
      if (children.length === 0) {
        setStatsByChildId({})
        return
      }

      setIsLoadingStats(true)
      setError(null)
      try {
        const results = await Promise.all(
          children.map(async (child) => {
            const res = await apiClient.get<ChildYearlyStats>(
              `/v1/stats/child/${child.id}/year/`,
              { params: { year } },
            )
            return [child.id, res.data] as const
          }),
        )

        if (!isMounted) return
        const next: Record<string, ChildYearlyStats> = {}
        for (const [childId, stats] of results) {
          next[childId] = stats
        }
        setStatsByChildId(next)
      } catch (err: any) {
        if (!isMounted) return
        const status = err?.response?.status
        if (status === 401) {
          clearAccessToken()
          navigate('/login', { replace: true })
          return
        }
        if (status === 404) {
          setError('Viss årsstatistik kunde inte hämtas för detta år.')
          setStatsByChildId({})
          return
        }
        setError('Kunde inte hämta årsstatistik. Försök igen.')
        setStatsByChildId({})
      } finally {
        if (isMounted) setIsLoadingStats(false)
      }
    }

    void loadStats()
    return () => {
      isMounted = false
    }
  }, [children, navigate, year])

  if (isLoadingChildren) {
    return (
      <main style={{ maxWidth: 720, margin: '2rem auto', padding: '0 1rem' }}>
        <h1>Historik</h1>
        <p>Laddar…</p>
      </main>
    )
  }

  return (
    <main style={{ maxWidth: 720, margin: '2rem auto', padding: '0 1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
        <h1 style={{ marginTop: 0 }}>Historik</h1>
        <button type="button" onClick={() => navigate('/home')}>
          Tillbaka
        </button>
      </div>

      {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}

      <section style={{ border: '1px solid #ddd', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
        <label style={{ display: 'block' }}>
            År
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            min={2000}
            max={9999}
            style={{ marginLeft: '0.5rem', width: 120 }}
          />
        </label>
      </section>

      {children.length === 0 ? <p>Inga barn kopplade till det här kontot.</p> : null}

      {isLoadingStats ? <p>Laddar årsstatistik…</p> : null}

      <div style={{ display: 'grid', gap: '0.75rem' }}>
        {children.map((child) => {
          const stats = statsByChildId[child.id] ?? null

          return (
            <section key={child.id} style={{ border: '1px solid #ddd', borderRadius: 8, padding: '1rem' }}>
              <h2 style={{ marginTop: 0 }}>{childShortName(child)}</h2>

              {stats ? (
                <>
                  <p style={{ marginBottom: 6 }}>
                      Totalt sålda enheter: <strong>{stats.total_units_sold}</strong>
                  </p>
                  <p style={{ marginTop: 0, marginBottom: 12 }}>
                      Totalt försäljningsbelopp: <strong>{stats.total_sales_amount}</strong>
                  </p>

                    <h3 style={{ margin: '0 0 0.5rem 0' }}>Per kampanj</h3>
                    {stats.campaigns.length === 0 ? <p>Inga kampanjer för detta år.</p> : null}

                  {stats.campaigns.length > 0 ? (
                    <div style={{ display: 'grid', gap: 10 }}>
                      {stats.campaigns.map((c) => (
                        <div
                          key={c.campaign_id}
                          style={{
                            border: '1px solid #eee',
                            borderRadius: 8,
                            padding: '0.75rem',
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
                            <strong>{c.campaign_name}</strong>
                              <span>{c.total_units_sold} st</span>
                          </div>
                          <div style={{ marginTop: 6, fontSize: 14 }}>
                              Försäljningsbelopp: {c.total_sales_amount}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </>
              ) : (
                  <p style={{ marginBottom: 0 }}>Ingen statistik hämtad för detta barn.</p>
              )}
            </section>
          )
        })}
      </div>
    </main>
  )
}
