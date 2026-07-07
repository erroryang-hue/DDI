import { useState } from 'react'
import { analyzeInteraction } from '../api/analysis'
import { saveRecentAnalysis } from '../utils/storage'
import Card from '../components/Card'
import Loader from '../components/Loader'
import EmptyState from '../components/EmptyState'
import DrugAutocomplete from '../components/DrugAutocomplete'
import type { AnalyzeResponse } from '../api/types'

const initialForm = {
  drug1: 'Aspirin',
  drug2: 'Warfarin',
  age: 65,
  weight: 75,
  dose1: 500,
  dose2: 5,
  // time between drug1 and drug2 in hours
  time_between: 24,
  interval1: 24,
  interval2: 24,
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
        <h2>Interaction Analysis</h2>
        <form className="form-grid" onSubmit={handleSubmit}>
          <DrugAutocomplete 
            value={form.drug1} 
            onChange={(value) => setForm({ ...form, drug1: value })}
            label="Drug 1"
            placeholder="Search and select first drug"
          />
          <DrugAutocomplete 
            value={form.drug2} 
            onChange={(value) => setForm({ ...form, drug2: value })}
            label="Drug 2"
            placeholder="Search and select second drug"
          />
          <label>
            Age
            <input type="number" value={form.age} min={0} max={120} onChange={(e) => setForm({ ...form, age: Number(e.target.value) })} />
          </label>
          <label>
            Weight (kg)
            <input type="number" value={form.weight} min={1} onChange={(e) => setForm({ ...form, weight: Number(e.target.value) })} />
          </label>
          <label>
            Dose 1 (mg)
            <input
              type="number"
              value={form.dose1}
              min={1}
              onChange={(e) => {
                const s = String(e.target.value).replace(/^0+(?=\d)/, '')
                setForm({ ...form, dose1: Number(s) || 0 })
              }}
            />
          </label>
          <label>
            Dose 2 (mg)
            <input
              type="number"
              value={form.dose2}
              min={1}
              onChange={(e) => {
                const s = String(e.target.value).replace(/^0+(?=\d)/, '')
                setForm({ ...form, dose2: Number(s) || 0 })
              }}
            />
          </label>
          {/* removed start date inputs to simplify analysis; use Time between instead */}
          <label>
            Time between drugs (hours)
            <input type="number" value={form.time_between} min={0} step={0.5} onChange={(e) => setForm({ ...form, time_between: Number(String(e.target.value).replace(/^0+(?=\d)/, '')) || 0 })} />
          </label>
          <label>
            Interval 1 (hours)
            <input type="number" value={form.interval1} min={1} step={0.5} onChange={(e) => setForm({ ...form, interval1: Number(String(e.target.value).replace(/^0+(?=\d)/, '')) || 0 })} />
          </label>
          <label>
            Interval 2 (hours)
            <input type="number" value={form.interval2} min={1} step={0.5} onChange={(e) => setForm({ ...form, interval2: Number(String(e.target.value).replace(/^0+(?=\d)/, '')) || 0 })} />
          </label>
          {/* Half-life removed from UI: it's taken from the dataset automatically */}
          <label className="checkbox-label">
            <input type="checkbox" checked={form.poor_metabolizer} onChange={(e) => setForm({ ...form, poor_metabolizer: e.target.checked })} />
            Poor metabolizer (CYP2D6)
          </label>
          <div className="form-actions">
            <button type="submit" disabled={loading} className="button primary">
              {loading ? 'Analyzing…' : 'Run Analysis'}
            </button>
          </div>
        </form>
      </Card>

      <Card>
        <h2>Interaction Results</h2>
        {loading && <Loader />}
        {error && <p className="section-error">{error}</p>}
        {result ? (
          <div className="result-panel">
            <div className={`severity-badge severity-${result.severity.toLowerCase()}`}>
              {result.severity}
            </div>
            <div className="result-grid">
              <div className="result-item">
                <span className="label">Risk Score:</span>
                <span className="value">{(result.risk_score * 100).toFixed(1)}%</span>
              </div>
              <div className="result-item">
                <span className="label">Interaction:</span>
                <span className="value">{result.interaction ? '✓ Yes' : '✗ No'}</span>
              </div>
            </div>
            {result.mechanisms && result.mechanisms.length > 0 && (
              <div className="result-section">
                <h3>Mechanisms</h3>
                <ul className="mechanism-list">
                  {result.mechanisms.map((item, index) => <li key={index}>{item}</li>)}
                </ul>
              </div>
            )}
            {result.recommendations && result.recommendations.length > 0 && (
              <div className="result-section">
                <h3>Clinical Recommendations</h3>
                <ul className="recommendation-list">
                  {result.recommendations.map((item, index) => <li key={index}>• {item}</li>)}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <EmptyState title="No results yet" description="Fill in the form and click Run Analysis to check for drug interactions." />
        )}
      </Card>
    </div>
  )
}
