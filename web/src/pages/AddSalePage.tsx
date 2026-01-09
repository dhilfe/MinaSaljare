import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { apiClient } from '../api/client'

type Child = {
  id: string
  first_name: string
  last_initial: string
}

type Campaign = {
  id: string
  name: string
}

type Product = {
  id: string
  name: string
  unit_price: string
}

function childShortName(child: Child) {
  return child.last_initial ? `${child.first_name} ${child.last_initial}` : child.first_name
}

type Toast = { message: string } | null

export default function AddSalePage() {
  const navigate = useNavigate()

  const [campaign, setCampaign] = useState<Campaign | null>(null)
  const [children, setChildren] = useState<Child[]>([])
  const [products, setProducts] = useState<Product[]>([])

  const [childId, setChildId] = useState('')
  const [productId, setProductId] = useState('')
  const [quantity, setQuantity] = useState(1)
  const [buyerName, setBuyerName] = useState('')
  const [isPaid, setIsPaid] = useState(false)
  const [isDelivered, setIsDelivered] = useState(false)

  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [toast, setToast] = useState<Toast>(null)

  const canSubmit = useMemo(() => {
    return Boolean(campaign?.id) && Boolean(childId) && Boolean(productId) && quantity > 0 && !isSubmitting
  }, [campaign?.id, childId, productId, quantity, isSubmitting])

  useEffect(() => {
    let isMounted = true

    async function load() {
      setIsLoading(true)
      setError(null)
      try {
        const campRes = await apiClient.get<Campaign>('/v1/campaigns/active/')
        if (!isMounted) return
        setCampaign({ id: campRes.data.id, name: campRes.data.name })

        const [childrenRes, productsRes] = await Promise.all([
          apiClient.get<Child[]>('/v1/children/'),
          apiClient.get<Product[]>(`/v1/campaigns/${campRes.data.id}/products/`),
        ])
        if (!isMounted) return

        setChildren(childrenRes.data)
        setProducts(productsRes.data)

        if (childrenRes.data.length > 0) setChildId(childrenRes.data[0].id)
        if (productsRes.data.length > 0) setProductId(productsRes.data[0].id)
      } catch {
        if (!isMounted) return
        setError('Failed to load campaign/products. Please try again.')
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    void load()
    return () => {
      isMounted = false
    }
  }, [])

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!canSubmit || !campaign) return

    setIsSubmitting(true)
    setError(null)
    try {
      await apiClient.post(`/v1/campaigns/${campaign.id}/sales/`, {
        child_id: childId,
        product_id: productId,
        quantity,
        buyer_name: buyerName,
        is_paid: isPaid,
        is_delivered: isDelivered,
      })

      setToast({ message: 'Sale saved.' })
      setTimeout(() => {
        navigate('/home', { replace: true })
      }, 600)
    } catch {
      setError('Failed to save sale. Please check inputs and try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <main style={{ maxWidth: 720, margin: '2rem auto', padding: '0 1rem' }}>
        <h1>Add Sale</h1>
        <p>Loading…</p>
      </main>
    )
  }

  return (
    <main style={{ maxWidth: 720, margin: '2rem auto', padding: '0 1rem' }}>
      <h1>Add Sale</h1>

      {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}

      {campaign ? <p>Campaign: {campaign.name}</p> : null}

      <form onSubmit={onSubmit}>
        <div style={{ display: 'grid', gap: '0.75rem' }}>
          <label>
            Child
            <select value={childId} onChange={(e) => setChildId(e.target.value)} style={{ marginLeft: '0.5rem' }}>
              {children.map((c) => (
                <option key={c.id} value={c.id}>
                  {childShortName(c)}
                </option>
              ))}
            </select>
          </label>

          <label>
            Product
            <select value={productId} onChange={(e) => setProductId(e.target.value)} style={{ marginLeft: '0.5rem' }}>
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>

          <label>
            Quantity
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <button type="button" onClick={() => setQuantity((q) => Math.max(1, q - 1))}>
                -
              </button>
              <input
                type="number"
                min={1}
                value={quantity}
                onChange={(e) => setQuantity(Math.max(1, Number(e.target.value || 1)))}
                style={{ width: 80 }}
              />
              <button type="button" onClick={() => setQuantity((q) => q + 1)}>
                +
              </button>
            </div>
          </label>

          <label>
            Buyer name (optional)
            <input value={buyerName} onChange={(e) => setBuyerName(e.target.value)} style={{ width: '100%' }} />
          </label>

          <label>
            <input type="checkbox" checked={isPaid} onChange={(e) => setIsPaid(e.target.checked)} /> Paid
          </label>

          <label>
            <input type="checkbox" checked={isDelivered} onChange={(e) => setIsDelivered(e.target.checked)} /> Delivered
          </label>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button type="button" onClick={() => navigate('/home')} disabled={isSubmitting}>
              Cancel
            </button>
            <button type="submit" disabled={!canSubmit}>
              {isSubmitting ? 'Saving…' : 'Save Sale'}
            </button>
          </div>
        </div>
      </form>

      {toast ? (
        <div
          style={{
            position: 'fixed',
            left: 16,
            right: 16,
            bottom: 16,
            maxWidth: 520,
            margin: '0 auto',
            background: '#222',
            color: '#fff',
            padding: '12px 14px',
            borderRadius: 8,
          }}
        >
          {toast.message}
        </div>
      ) : null}
    </main>
  )
}
