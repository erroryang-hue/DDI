import { useState } from 'react'
import { searchDrug } from '../api/search'
import Card from '../components/Card'
import Loader from '../components/Loader'
import EmptyState from '../components/EmptyState'

export default function DrugSearch() {
  const [query, setQuery] = useState('DrugA')
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

  return (
    <div className="page-grid">
      <Card>
        <h2>Drug search</h2>
        <form className="form-grid" onSubmit={handleSearch}>
          <label>
            Drug name or ID
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="DB001 or DrugA" />
          </label>
          <div className="form-actions">
            <button type="submit" disabled={loading} className="button primary">
              {loading ? 'Searching…' : 'Search'}
            </button>
          </div>
        </form>
      </Card>

      <Card>
        <h2>Search results</h2>
        {loading && <Loader />}
        {error && <p className="section-error">{error}</p>}
        {results ? (
          <div className="result-panel">
            <pre className="code-block">{JSON.stringify(results, null, 2)}</pre>
          </div>
        ) : (
          <EmptyState title="No search results" description="Search for a drug to review its details." />
        )}
      </Card>
    </div>
  )
}
