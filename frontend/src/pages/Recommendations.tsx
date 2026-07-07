import { useState } from 'react'
import { getAlternatives } from '../api/alternatives'
import Card from '../components/Card'
import Loader from '../components/Loader'
import EmptyState from '../components/EmptyState'

export default function Recommendations() {
  const [drugId, setDrugId] = useState('Aspirin')
  const [alternatives, setAlternatives] = useState<any[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleLookup(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await getAlternatives(drugId)
      setAlternatives(response)
    } catch (err: any) {
      setError(err?.message || 'Unable to load alternatives')
      setAlternatives(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-grid">
      <Card>
        <h2>Recommendations</h2>
        <form className="form-grid" onSubmit={handleLookup}>
          <label>
            Drug ID
            <input value={drugId} onChange={(e) => setDrugId(e.target.value)} placeholder="e.g., Aspirin, Warfarin" />
          </label>
          <div className="form-actions">
            <button type="submit" disabled={loading} className="button primary">
              {loading ? 'Loading…' : 'Get alternatives'}
            </button>
          </div>
        </form>
      </Card>

      <Card>
        <h2>Alternative drugs</h2>
        {loading && <Loader />}
        {error && <p className="section-error">{error}</p>}
        {alternatives?.length ? (
          <ul className="list-card">
            {alternatives.map((item: any, idx: number) => (
              <li key={idx}>
                <strong>{item.drug_id || item.drug}</strong> · score {item.score?.toFixed?.(3) ?? item.score}
                {item.reason ? <p className="small-text">{item.reason}</p> : null}
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title="No recommendations" description="Search a drug to see safe alternatives." />
        )}
      </Card>
    </div>
  )
}
