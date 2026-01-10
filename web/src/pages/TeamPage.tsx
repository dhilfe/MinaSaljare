import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { apiClient, clearAccessToken } from '../api/client'

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

export default function TeamPage() {
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
          setError('Ingen aktiv kampanj hittades för ditt lag.')
          setCampaign(null)
          setSummary(null)
          return
        }
        setError('Kunde inte hämta lagstatus. Försök igen.')
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
      <main style={{ maxWidth: 720, margin: '2rem auto', padding: '0 1rem' }}>
        <h1>Lag</h1>
        <p>Laddar…</p>
      </main>
    )
  }

  return (
    <main style={{ maxWidth: 720, margin: '2rem auto', padding: '0 1rem' }}>
      <h1>Lag</h1>

      {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}

      {campaign ? (
        <section style={{ border: '1px solid #ddd', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
          <h2 style={{ marginTop: 0 }}>Kampanj</h2>
          <p style={{ marginBottom: 0 }}>Namn: {campaign.name}</p>
          <p style={{ marginBottom: 0 }}>Slutdatum: {campaign.end_date}</p>
        </section>
      ) : null}

      {summary ? (
        <>
          <section style={{ border: '1px solid #ddd', borderRadius: 8, padding: '1rem', marginBottom: '1rem' }}>
            <h2 style={{ marginTop: 0 }}>{summary.team.name}</h2>
            <p>
              Lagets total: {summary.team_total_units_sold} / {summary.team_target_units}
            </p>
            <progress value={teamProgressValue} max={100} style={{ width: '100%', height: 20 }} />
            <p>{summary.team_progress_percent}%</p>
          </section>

          <section style={{ textAlign: 'left' }}>
            <h2>Barn</h2>
            {summary.children.length === 0 ? <p>Inga aktiva barn i laget.</p> : null}
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              {summary.children.map((c) => {
                const percentNum = Number(c.progress_percent)
                const percentValue = Number.isFinite(percentNum) ? percentNum : 0
                return (
                  <div key={c.id} style={{ border: '1px solid #ddd', borderRadius: 8, padding: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
                      <strong>{c.name}</strong>
                      <span>
                        {c.total_units_sold} / {c.target_units}
                      </span>
                    </div>
                    <progress value={percentValue} max={100} style={{ width: '100%', height: 14, marginTop: 8 }} />
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: 14 }}>
                      <span>{c.progress_percent}%</span>
                      <span>Kvar: {Math.max(0, c.target_units - c.total_units_sold)}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </section>
        </>
      ) : null}
    </main>
  )
}
