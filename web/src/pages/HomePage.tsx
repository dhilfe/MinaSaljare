import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { apiClient, clearAccessToken } from '../api/client'

type Child = {
  id: string
  first_name: string
  last_initial: string
}

type Campaign = {
  id: string
  name: string
}

type ChildCampaignSummary = {
  child_id: string
  campaign_id: string
  target_units: number
  total_units_sold: number
  total_sales_amount: string
  remaining_units_to_target: number
  progress_percent: string
}

function childShortName(child: Child) {
  return child.last_initial ? `${child.first_name} ${child.last_initial}` : child.first_name
}

export default function HomePage() {
  const navigate = useNavigate()

  const [campaign, setCampaign] = useState<Campaign | null>(null)
  const [children, setChildren] = useState<Child[]>([])
  const [selectedChildId, setSelectedChildId] = useState<string>('')
  const [summary, setSummary] = useState<ChildCampaignSummary | null>(null)

  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingSummary, setIsLoadingSummary] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const selectedChild = useMemo(() => {
    return children.find((c) => c.id === selectedChildId) ?? null
  }, [children, selectedChildId])

  useEffect(() => {
    let isMounted = true

    async function load() {
      setIsLoading(true)
      setError(null)
      try {
        const [campRes, childrenRes] = await Promise.all([
          apiClient.get<Campaign>('/v1/campaigns/active/'),
          apiClient.get<Child[]>('/v1/children/'),
        ])
        if (!isMounted) return

        setCampaign({ id: campRes.data.id, name: campRes.data.name })
        setChildren(childrenRes.data)

        if (childrenRes.data.length > 0) {
          setSelectedChildId((prev) => prev || childrenRes.data[0].id)
        }
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
          setChildren([])
          setSelectedChildId('')
          return
        }
        setError('Failed to load data. Please try again.')
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    void load()
    return () => {
      isMounted = false
    }
  }, [navigate])

  useEffect(() => {
    let isMounted = true
    async function loadSummary() {
      if (!campaign || !selectedChildId) {
        setSummary(null)
        return
      }

      setIsLoadingSummary(true)
      setError(null)
      try {
        const res = await apiClient.get<ChildCampaignSummary>(
          `/v1/children/${selectedChildId}/campaigns/${campaign.id}/summary/`,
        )
        if (!isMounted) return
        setSummary(res.data)
      } catch (err: any) {
        if (!isMounted) return
        const status = err?.response?.status
        if (status === 401) {
          clearAccessToken()
          navigate('/login', { replace: true })
          return
        }
        setError('Failed to load child summary. Please try again.')
        setSummary(null)
      } finally {
        if (isMounted) setIsLoadingSummary(false)
      }
    }
    void loadSummary()
    return () => {
      isMounted = false
    }
  }, [campaign, navigate, selectedChildId])

  if (isLoading) {
    return (
      <main style={{ maxWidth: 720, margin: '2rem auto', padding: '0 1rem' }}>
        <h1>Home</h1>
        <p>Loading…</p>
      </main>
    )
  }

  return (
    <main style={{ maxWidth: 720, margin: '2rem auto', padding: '0 1rem' }}>
      <h1>Home</h1>

      {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}

      {campaign ? <p>Active campaign: {campaign.name}</p> : null}

      {children.length > 1 ? (
        <label style={{ display: 'block', marginBottom: '1rem' }}>
          Child
          <select
            value={selectedChildId}
            onChange={(e) => setSelectedChildId(e.target.value)}
            style={{ marginLeft: '0.5rem' }}
          >
            {children.map((c) => (
              <option key={c.id} value={c.id}>
                {childShortName(c)}
              </option>
            ))}
          </select>
        </label>
      ) : null}

      {children.length === 1 ? <p>Child: {childShortName(children[0])}</p> : null}

      {isLoadingSummary ? <p>Loading summary…</p> : null}

      {summary && selectedChild ? (
        <section style={{ border: '1px solid #ddd', borderRadius: 8, padding: '1rem' }}>
          <h2 style={{ marginTop: 0 }}>{childShortName(selectedChild)}</h2>
          <p>
            Sold: {summary.total_units_sold} / {summary.target_units} (Remaining:{' '}
            {summary.remaining_units_to_target})
          </p>
          <p>Sales amount: {summary.total_sales_amount}</p>
          <progress
            value={Number(summary.progress_percent)}
            max={100}
            style={{ width: '100%', height: 20 }}
          />
          <p>{summary.progress_percent}%</p>
        </section>
      ) : null}

      {campaign && children.length === 0 ? <p>No children linked to this account.</p> : null}
    </main>
  )
}
