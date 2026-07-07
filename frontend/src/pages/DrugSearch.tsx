import { useState } from 'react'
import { searchDrug, getDrugsList } from '../api/search'
import Card from '../components/Card'
import Loader from '../components/Loader'
import EmptyState from '../components/EmptyState'

export default function DrugSearch() {
  const [query, setQuery] = useState('Aspirin')
  const [results, setResults] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setError(null)

    try {
      const data = await searchDrug(query)
      setResults(data)
    } catch (err: any) {
      setError(err?.message || 'Search failed')
      setResults(null)
    } finally {
      setLoading(false)
    }
  }

  async function handleListAll() {
    setLoading(true)
    setError(null)
    try {
      const data = await getDrugsList()
      setResults({ all: data.drugs })
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch drug list')
      setResults(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-grid">
      <Card>
        <h2>Drug search</h2>
        <form className="form-grid" onSubmit={handleSearch}>
          <label>
            Drug name
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="e.g., Aspirin, Warfarin, Metformin" />
          </label>
          <div className="form-actions">
            <button type="submit" disabled={loading} className="button primary">
              {loading ? 'Searching…' : 'Search'}
            </button>
            <button type="button" onClick={handleListAll} className="button">
              Browse All Drugs
            </button>
          </div>
        </form>
      </Card>

      <Card>
        <h2>Search results</h2>
        {loading && <Loader />}
        {error && <p className="section-error">{error}</p>}
        {results && Object.keys(results).length > 0 ? (
          <div className="result-panel">
            {results.all ? (
              <div className="all-drugs-list">
                <h3>All Drugs</h3>
                <div className="node-list">
                  {Array.isArray(results.all) && results.all.map((d: any, idx: number) => (
                    <div key={idx} className="node-card">
                      <strong>{d.name}</strong>
                      <div className="node-attrs">
                        <div className="attr-row"><span className="attr-label">Generic:</span> <span className="attr-value">{d.generic_name || '—'}</span></div>
                        <div className="attr-row"><span className="attr-label">Class:</span> <span className="attr-value">{d.drug_class || d.atc_class || '—'}</span></div>
                        <div className="attr-row"><span className="attr-label">Half-life:</span> <span className="attr-value">{d.half_life ?? '—'}</span></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <>
                <h3>Drug: {results.center}</h3>
                {results.groups && Object.entries(results.groups).map(([type, nodes]: [string, any]) => (
                  <div key={type} className="search-result-group">
                    <h4>{type}</h4>
                    <div className="node-list">
                      {Array.isArray(nodes) && nodes.map((node: any, idx: number) => (
                        <div key={idx} className="node-card">
                          <strong>{node.id}</strong>
                          <div className="node-attrs">
                            {Object.entries(node.attrs || {}).map(([key, value]: [string, any]) => (
                              <div key={key} className="attr-row">
                                <span className="attr-label">{key}:</span>
                                <span className="attr-value">{String(value)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
                {results.edges && results.edges.length > 0 && (
                  <div className="search-result-group">
                    <h4>Relations</h4>
                    <div className="edges-list">
                      {results.edges.map((edge: any, idx: number) => (
                        <div key={idx} className="edge-item">
                          <span>{edge.source}</span>
                          <span className="edge-relation">{edge.relation}</span>
                          <span>{edge.target}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        ) : (
          <EmptyState title="No search results" description="Search for a drug to review its details." />
        )}
      </Card>
    </div>
  )
}
