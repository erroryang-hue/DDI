import { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts'
import { getTimeline } from '../api/timeline'
import Card from '../components/Card'
import Loader from '../components/Loader'
import EmptyState from '../components/EmptyState'

export default function TimelineSimulator() {
  const [drug1, setDrug1] = useState('DB001')
  const [drug2, setDrug2] = useState('DB002')
  const [start1, setStart1] = useState(0)
  const [start2, setStart2] = useState(2)
  const [interval1, setInterval1] = useState(24)
  const [interval2, setInterval2] = useState(24)
  const [halfLife1, setHalfLife1] = useState(24)
  const [halfLife2, setHalfLife2] = useState(12)
  const [data, setData] = useState<any[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const timeline = await getTimeline({
        drug1,
        drug2,
        start1,
        start2,
        interval1,
        interval2,
        half_life1: halfLife1,
        half_life2: halfLife2,
      })
      setData(timeline)
    } catch (err: any) {
      setError(err?.message || 'Unable to load timeline')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-grid">
      <Card>
        <h2>Timeline simulator</h2>
        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            Drug 1
            <input value={drug1} onChange={(e) => setDrug1(e.target.value)} />
          </label>
          <label>
            Drug 2
            <input value={drug2} onChange={(e) => setDrug2(e.target.value)} />
          </label>
          <label>
            Start 1
            <input type="number" value={start1} min={0} onChange={(e) => setStart1(Number(e.target.value))} />
          </label>
          <label>
            Start 2
            <input type="number" value={start2} min={0} onChange={(e) => setStart2(Number(e.target.value))} />
          </label>
          <label>
            Half-life 1
            <input type="number" value={halfLife1} min={1} onChange={(e) => setHalfLife1(Number(e.target.value))} />
          </label>
          <label>
            Half-life 2
            <input type="number" value={halfLife2} min={1} onChange={(e) => setHalfLife2(Number(e.target.value))} />
          </label>
          <div className="form-actions">
            <button type="submit" disabled={loading} className="button primary">
              {loading ? 'Simulating…' : 'Simulate Timeline'}
            </button>
          </div>
        </form>
      </Card>

      <Card>
        <h2>Risk over time</h2>
        {loading && <Loader />}
        {error && <p className="section-error">{error}</p>}
        {data ? (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={data} margin={{ top: 16, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" label={{ value: 'Hour', position: 'insideBottomRight', offset: -8 }} />
              <YAxis domain={[0, 'dataMax + 0.2']} />
              <Tooltip />
              <Line type="monotone" dataKey="risk" stroke="#0b5fff" strokeWidth={3} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <EmptyState title="No timeline data" description="Run a simulation to see risk over time." />
        )}
      </Card>
    </div>
  )
}
