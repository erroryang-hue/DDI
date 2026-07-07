import { useState } from 'react'
import { analyzePolypharmacy } from '../api/polypharmacy'
import Card from '../components/Card'
import Loader from '../components/Loader'
import EmptyState from '../components/EmptyState'

export default function Polypharmacy() {
  const [drugs, setDrugs] = useState('Aspirin,Warfarin,Metformin')
  const [result, setResult] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const drugList = drugs.split(',').map((drug) => drug.trim()).filter(Boolean)
      const data = await analyzePolypharmacy(drugList)
      setResult(data)
    } catch (err: any) {
      setError(err?.message || 'Unable to fetch polypharmacy results')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-grid">
      <Card>
        <h2>Polypharmacy analysis</h2>
        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            Drug list (comma-separated)
            <input value={drugs} onChange={(e) => setDrugs(e.target.value)} placeholder="Aspirin,Warfarin,Metformin" />
          </label>
          <div className="form-actions">
            <button type="submit" disabled={loading} className="button primary">
              {loading ? 'Running…' : 'Run Polypharmacy'}
            </button>
          </div>
        </form>
      </Card>

      <Card>
        <h2>Results</h2>
        {loading && <Loader />}
        {error && <p className="section-error">{error}</p>}
        {result ? (
          <div className="result-panel">
            <p><strong>Highest risk:</strong> {result.highest_risk?.drug1} / {result.highest_risk?.drug2} ({result.highest_risk?.risk.toFixed(3)})</p>
            <p><strong>Average risk:</strong> {result.average_risk.toFixed(3)}</p>
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Drug 1</th>
                    <th>Drug 2</th>
                    <th>Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {result.results?.map((item: any, ix: number) => (
                    <tr key={ix}>
                      <td>{item.drug1}</td>
                      <td>{item.drug2}</td>
                      <td>{item.risk.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <EmptyState title="No results yet" description="Enter a drug list to run polypharmacy analysis." />
        )}
      </Card>
    </div>
  )
}
