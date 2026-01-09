import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { apiClient, clearAccessToken } from '../api/client'

type MeResponse = {
  id: string
  email: string
  role: 'guardian' | 'coach' | string | null
  first_name: string
  last_name: string
}

type TeamRef = {
  id: string
  name: string
}

type TeamYearlyCampaignItem = {
  campaign_id: string
  campaign_name: string
  units_sold: number
  sales_amount: string
}

type TeamYearlyChildItem = {
  child_id: string
  name: string
  total_units_sold: number
  total_sales_amount: string
  campaigns: TeamYearlyCampaignItem[]
}

type TeamYearlyStatsResponse = {
  team: TeamRef
  year: number
  total_units_sold: number
  total_sales_amount: string
  children: TeamYearlyChildItem[]
}

type SortKey = 'name' | 'units' | 'amount' | 'campaigns'

type SortState = {
  key: SortKey
  direction: 'asc' | 'desc'
}

function toNumber(value: string) {
  const asNum = Number(value)
  return Number.isFinite(asNum) ? asNum : 0
}

export default function CoachYearlyStatsPage() {
  const navigate = useNavigate()

  const defaultYear = useMemo(() => new Date().getFullYear(), [])

  const [year, setYear] = useState<number>(defaultYear)
  const [data, setData] = useState<TeamYearlyStatsResponse | null>(null)
  const [selectedChildId, setSelectedChildId] = useState<string | null>(null)

  const [sort, setSort] = useState<SortState>({ key: 'units', direction: 'desc' })

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true

    async function load() {
      setIsLoading(true)
      setError(null)
      try {
        const meRes = await apiClient.get<MeResponse>('/v1/me/')
        if (!isMounted) return

        if (meRes.data.role !== 'coach') {
          setError('Forbidden: coach access only.')
          setData(null)
          setSelectedChildId(null)
          return
        }

        const res = await apiClient.get<TeamYearlyStatsResponse>('/v1/stats/team/year/', {
          params: { year },
        })
        if (!isMounted) return
        setData(res.data)
        setSelectedChildId(null)
      } catch (err: any) {
        if (!isMounted) return
        const status = err?.response?.status
        if (status === 401) {
          clearAccessToken()
          navigate('/login', { replace: true })
          return
        }
        if (status === 403) {
          setError('Forbidden: coach access only.')
          setData(null)
          setSelectedChildId(null)
          return
        }
        setError('Failed to load yearly statistics. Please try again.')
        setData(null)
        setSelectedChildId(null)
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    void load()
    return () => {
      isMounted = false
    }
  }, [navigate, year])

  const sortedChildren = useMemo(() => {
    const children = data?.children ?? []
    const direction = sort.direction === 'asc' ? 1 : -1

    return [...children].sort((a, b) => {
      if (sort.key === 'name') {
        return direction * a.name.localeCompare(b.name)
      }
      if (sort.key === 'units') {
        return direction * (a.total_units_sold - b.total_units_sold)
      }
      if (sort.key === 'amount') {
        return direction * (toNumber(a.total_sales_amount) - toNumber(b.total_sales_amount))
      }
      // campaigns
      return direction * (a.campaigns.length - b.campaigns.length)
    })
  }, [data?.children, sort.direction, sort.key])

  const selectedChild = useMemo(() => {
    if (!data || !selectedChildId) return null
    return data.children.find((c) => c.child_id === selectedChildId) ?? null
  }, [data, selectedChildId])

  function toggleSort(key: SortKey) {
    setSort((prev) => {
      if (prev.key !== key) return { key, direction: 'asc' }
      return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' }
    })
  }

  if (isLoading) {
    return (
      <main style={{ maxWidth: 920, margin: '2rem auto', padding: '0 1rem' }}>
        <h1>Yearly stats</h1>
        <p>Loading…</p>
      </main>
    )
  }

  return (
    <main style={{ maxWidth: 920, margin: '2rem auto', padding: '0 1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
        <h1 style={{ marginTop: 0 }}>Yearly stats</h1>
        <button type="button" onClick={() => navigate('/coach/dashboard')}>
          Back
        </button>
      </div>

      {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}

      <section style={{ border: '1px solid #ddd', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
        <label>
          Year
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            min={1970}
            max={2100}
            style={{ marginLeft: '0.5rem', width: 120 }}
          />
        </label>

        {data ? (
          <div style={{ marginTop: '0.75rem' }}>
            <p style={{ margin: 0 }}>
              Team: <strong>{data.team.name}</strong>
            </p>
            <p style={{ margin: 0 }}>
              Totals: <strong>{data.total_units_sold}</strong> units,{' '}
              <strong>{data.total_sales_amount}</strong> amount
            </p>
          </div>
        ) : null}
      </section>

      {data ? (
        <section style={{ textAlign: 'left' }}>
          <h2>Children</h2>

          <div style={{ marginBottom: '0.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button type="button" onClick={() => toggleSort('name')}>
              Sort: Name
            </button>
            <button type="button" onClick={() => toggleSort('units')}>
              Sort: Units
            </button>
            <button type="button" onClick={() => toggleSort('amount')}>
              Sort: Amount
            </button>
            <button type="button" onClick={() => toggleSort('campaigns')}>
              Sort: Campaigns
            </button>
          </div>

          {sortedChildren.length === 0 ? <p>No sales recorded for this year.</p> : null}

          {sortedChildren.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd', padding: '8px' }}>Child</th>
                    <th style={{ textAlign: 'right', borderBottom: '1px solid #ddd', padding: '8px' }}>Units</th>
                    <th style={{ textAlign: 'right', borderBottom: '1px solid #ddd', padding: '8px' }}>Amount</th>
                    <th style={{ textAlign: 'right', borderBottom: '1px solid #ddd', padding: '8px' }}>Campaigns</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedChildren.map((c) => {
                    const isSelected = c.child_id === selectedChildId
                    return (
                      <tr
                        key={c.child_id}
                        onClick={() => setSelectedChildId((prev) => (prev === c.child_id ? null : c.child_id))}
                        style={{ cursor: 'pointer', background: isSelected ? '#f6f6f6' : 'transparent' }}
                      >
                        <td style={{ padding: '8px', borderBottom: '1px solid #eee' }}>
                          <strong>{c.name}</strong>
                        </td>
                        <td style={{ padding: '8px', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                          {c.total_units_sold}
                        </td>
                        <td style={{ padding: '8px', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                          {c.total_sales_amount}
                        </td>
                        <td style={{ padding: '8px', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                          {c.campaigns.length}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : null}

          {selectedChild ? (
            <section style={{ marginTop: '1rem', border: '1px solid #ddd', borderRadius: 8, padding: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
                <h3 style={{ marginTop: 0, marginBottom: 0 }}>{selectedChild.name}</h3>
                <button type="button" onClick={() => setSelectedChildId(null)}>
                  Close
                </button>
              </div>

              <p style={{ marginTop: 8, marginBottom: 12 }}>
                Totals: {selectedChild.total_units_sold} units, {selectedChild.total_sales_amount} amount
              </p>

              <h4 style={{ marginTop: 0 }}>Campaign breakdown</h4>
              {selectedChild.campaigns.length === 0 ? <p>No campaigns.</p> : null}

              {selectedChild.campaigns.length > 0 ? (
                <div style={{ display: 'grid', gap: 10 }}>
                  {selectedChild.campaigns.map((camp) => (
                    <div
                      key={camp.campaign_id}
                      style={{ border: '1px solid #eee', borderRadius: 8, padding: '0.75rem' }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
                        <strong>{camp.campaign_name}</strong>
                        <span>{camp.units_sold} units</span>
                      </div>
                      <div style={{ marginTop: 6, fontSize: 14 }}>Amount: {camp.sales_amount}</div>
                    </div>
                  ))}
                </div>
              ) : null}
            </section>
          ) : null}
        </section>
      ) : null}
    </main>
  )
}
