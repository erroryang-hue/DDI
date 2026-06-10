import { useState } from 'react'
import { analyzeInteraction } from '../api/analysis'
import { saveRecentAnalysis } from '../utils/storage'
import Card from '../components/Card'
import Loader from '../components/Loader'
import EmptyState from '../components/EmptyState'
import type { AnalyzeResponse } from '../api/types'

const initialForm = {
  drug1: 'DrugA',
  drug2: 'DrugB',
  age: 45,
  weight: 70,
  dose1: 100,
  dose2: 100,
  start1: '2024-01-01',
  start2: '2024-01-02',
  interval1: 24,
  interval2: 24,
  half_life1: 24,
  half_life2: 12,
  poor_metabolizer: false,
}

export default function InteractionAnalysis() {
  const [form, setForm] = useState(initialForm)
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const data = await analyzeInteraction(form)
      setResult(data)
      saveRecentAnalysis(data, form.drug1, form.drug2)
    } catch (err: any) {
      setError(err?.message || 'Unable to analyze interaction')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-grid">
      <Card>
        <h2>Interaction analysis</h2>
        <form className="form-grid" onSubmit={handleSubmit}>
          <label>
            Drug 1
            <input value={form.drug1} onChange={(e) => setForm({ ...form, drug1: e.target.value })} />
          </label>
          <label>
            Drug 2
            <input value={form.drug2} onChange={(e) => setForm({ ...form, drug2: e.target.value })} />
          </label>
          <label>
            Age
            <input type="number" value={form.age} min={0} onChange={(e) => setForm({ ...form, age: Number(e.target.value) })} />
          </label>
          <label>
            Weight (kg)
            <input type="number" value={form.weight} min={1} onChange={(e) => setForm({ ...form, weight: Number(e.target.value) })} />
          </label>
          <label>
            Dose 1
            <input type="number" value={form.dose1} min={1} onChange={(e) => setForm({ ...form, dose1: Number(e.target.value) })} />
          </label>
          <label>
            Dose 2
            <input type="number" value={form.dose2} min={1} onChange={(e) => setForm({ ...form, dose2: Number(e.target.value) })} />
          </label>
          <label>
            Start date 1
            <input type="date" value={form.start1} onChange={(e) => setForm({ ...form, start1: e.target.value })} />
          </label>
          <label>
            Start date 2
            <input type="date" value={form.start2} onChange={(e) => setForm({ ...form, start2: e.target.value })} />
          </label>
          <label>
            Interval 1 (hrs)
            <input type="number" value={form.interval1} min={1} onChange={(e) => setForm({ ...form, interval1: Number(e.target.value) })} />
          </label>
          <label>
            Interval 2 (hrs)
            <input type="number" value={form.interval2} min={1} onChange={(e) => setForm({ ...form, interval2: Number(e.target.value) })} />
          </label>
          <label>
            Half-life 1 (hrs)
            <input type="number" value={form.half_life1} min={1} onChange={(e) => setForm({ ...form, half_life1: Number(e.target.value) })} />
          </label>
          <label>
            Half-life 2 (hrs)
            <input type="number" value={form.half_life2} min={1} onChange={(e) => setForm({ ...form, half_life2: Number(e.target.value) })} />
          </label>
          <label className="checkbox-label">
            <input type="checkbox" checked={form.poor_metabolizer} onChange={(e) => setForm({ ...form, poor_metabolizer: e.target.checked })} />
            Poor metabolizer
          </label>
          <div className="form-actions">
            <button type="submit" disabled={loading} className="button primary">
              {loading ? 'Analyzing…' : 'Run analysis'}
            </button>
          </div>
        </form>
      </Card>

      <Card>
        <h2>Interaction summary</h2>
        {loading && <Loader />}
        {error && <p className="section-error">{error}</p>}
        {result ? (
          <div className="result-panel">
            <p><strong>Interaction:</strong> {result.interaction ? 'Yes' : 'No'}</p>
            <p><strong>Risk score:</strong> {result.risk_score.toFixed(3)}</p>
            <p><strong>Severity:</strong> {result.severity}</p>
            <p><strong>Mechanisms:</strong></p>
            <ul>{result.mechanisms.map((item, index) => <li key={index}>{item}</li>)}</ul>
            <p><strong>Recommendations:</strong></p>
            <ul>{result.recommendations.map((item, index) => <li key={index}>{item}</li>)}</ul>
          </div>
        ) : (
          <EmptyState title="No analysis results" description="Submit the form to run an interaction analysis." />
        )}
      </Card>
    </div>
  )
}
