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

type Campaign = {
  id: string
  name: string
  end_date: string
}

type TeamSummaryCampaign = {
  id: string
  name: string
}

type TeamSummaryTeam = {
  id: string
  name: string
}

type TeamCampaignChildSummary = {
  id: string
  name: string
  target_units: number
  total_units_sold: number
  progress_percent: string
}

type TeamCampaignSummary = {
  campaign: TeamSummaryCampaign
  team: TeamSummaryTeam
  children: TeamCampaignChildSummary[]
  team_total_units_sold: number
  team_target_units: number
  team_progress_percent: string
}

export default function CoachDashboardPage() {
  const navigate = useNavigate()

  const [campaign, setCampaign] = useState<Campaign | null>(null)
  const [summary, setSummary] = useState<TeamCampaignSummary | null>(null)

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const teamProgressValue = useMemo(() => {
    if (!summary) return 0
    const asNum = Number(summary.team_progress_percent)
    return Number.isFinite(asNum) ? asNum : 0
  }, [summary])

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
          setCampaign(null)
          setSummary(null)
          return
        }

        const campRes = await apiClient.get<Campaign>('/v1/campaigns/active/')
        if (!isMounted) return

        setCampaign({
          id: campRes.data.id,
          name: campRes.data.name,
          end_date: campRes.data.end_date,
        })

        const summaryRes = await apiClient.get<TeamCampaignSummary>(
          `/v1/team/campaigns/${campRes.data.id}/summary/`,
        )
        if (!isMounted) return
        setSummary(summaryRes.data)
      } catch (err: any) {
        if (!isMounted) return
        const status = err?.response?.status
        if (status === 401) {
          clearAccessToken()
          navigate('/login', { replace: true })
          return
        }
        if (status === 404) {
          setError('No active campaign found for your team.')
          setCampaign(null)
          setSummary(null)
          return
        }
        setError('Failed to load coach dashboard. Please try again.')
        setSummary(null)
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    void load()
    return () => {
      isMounted = false
    }
  }, [navigate])

  if (isLoading) {
    return (
      <main style={{ maxWidth: 900, margin: '2rem auto', padding: '0 1rem' }}>
        <h1>Coach Dashboard</h1>
        <p>Loading…</p>
      </main>
    )
  }

  return (
    <main style={{ maxWidth: 900, margin: '2rem auto', padding: '0 1rem' }}>
      <h1>Coach Dashboard</h1>

      {error ? (
        <section style={{ border: '1px solid #ddd', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
          <p style={{ color: 'crimson', marginTop: 0 }}>{error}</p>
          <button type="button" onClick={() => navigate('/home')}>
            Go to Home
          </button>
        </section>
      ) : null}

      <section style={{ marginBottom: '1rem' }}>
        <a href="/admin/" target="_blank" rel="noreferrer">
          Open Django Admin
        </a>
      </section>

      {campaign ? (
        <section style={{ border: '1px solid #ddd', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
          <h2 style={{ marginTop: 0 }}>Campaign</h2>
          <p style={{ marginBottom: 0 }}>Name: {campaign.name}</p>
          <p style={{ marginBottom: 0 }}>End date: {campaign.end_date}</p>
        </section>
      ) : null}

      {summary ? (
        <>
          <section style={{ border: '1px solid #ddd', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
            <h2 style={{ marginTop: 0 }}>{summary.team.name}</h2>
            <p>
              Team total: {summary.team_total_units_sold} / {summary.team_target_units}
            </p>
            <progress value={teamProgressValue} max={100} style={{ width: '100%', height: 20 }} />
            <p>{summary.team_progress_percent}%</p>
          </section>

          <section style={{ textAlign: 'left' }}>
            <h2>Children</h2>
            {summary.children.length === 0 ? <p>No active children in team.</p> : null}
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '0.5rem', borderBottom: '1px solid #ddd' }}>Name</th>
                    <th style={{ textAlign: 'right', padding: '0.5rem', borderBottom: '1px solid #ddd' }}>Sold</th>
                    <th style={{ textAlign: 'right', padding: '0.5rem', borderBottom: '1px solid #ddd' }}>Target</th>
                    <th style={{ textAlign: 'right', padding: '0.5rem', borderBottom: '1px solid #ddd' }}>%</th>
                    <th style={{ textAlign: 'right', padding: '0.5rem', borderBottom: '1px solid #ddd' }}>Remaining</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.children.map((c) => (
                    <tr key={c.id}>
                      <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee' }}>{c.name}</td>
                      <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                        {c.total_units_sold}
                      </td>
                      <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                        {c.target_units}
                      </td>
                      <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                        {c.progress_percent}%
                      </td>
                      <td style={{ padding: '0.5rem', borderBottom: '1px solid #eee', textAlign: 'right' }}>
                        {Math.max(0, c.target_units - c.total_units_sold)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      ) : null}
    </main>
  )
}
