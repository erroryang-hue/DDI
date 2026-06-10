import { useMemo, useState } from 'react'
import ReactFlow, { Background, Controls } from 'reactflow'
import 'reactflow/dist/style.css'
import { getGraphForPair } from '../api/search'
import Card from '../components/Card'
import Loader from '../components/Loader'
import EmptyState from '../components/EmptyState'

export default function GraphExplorer() {
  const [drug1, setDrug1] = useState('DB001')
  const [drug2, setDrug2] = useState('DB002')
  const [graphData, setGraphData] = useState<any | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const elements = useMemo(() => {
    if (!graphData) return []
    const nodes = graphData.nodes.map((node: any, index: number) => ({
      id: node.id,
      data: { label: node.attrs?.name || node.id },
      position: { x: (index % 4) * 180, y: Math.floor(index / 4) * 120 },
      style: { border: '1px solid #0b5fff', padding: 12, borderRadius: 10, background: '#fff' },
    }))
    const edges = graphData.edges.map((edge: any, index: number) => ({
      id: `edge-${index}`,
      source: edge.source,
      target: edge.target,
      label: edge.relation || '',
      animated: true,
      style: { stroke: '#0b5fff' },
      labelStyle: { fill: '#0b5fff', fontWeight: 600 },
    }))
    return [...nodes, ...edges]
  }, [graphData])

  async function handleLoad(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const response = await getGraphForPair(drug1, drug2)
      setGraphData(response)
    } catch (err: any) {
      setError(err?.message || 'Unable to load graph')
      setGraphData(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-grid">
      <Card>
        <h2>Graph explorer</h2>
        <form className="form-grid" onSubmit={handleLoad}>
          <label>
            Drug 1
            <input value={drug1} onChange={(e) => setDrug1(e.target.value)} />
          </label>
          <label>
            Drug 2
            <input value={drug2} onChange={(e) => setDrug2(e.target.value)} />
          </label>
          <div className="form-actions">
            <button type="submit" disabled={loading} className="button primary">
              {loading ? 'Loading…' : 'Explore Graph'}
            </button>
          </div>
        </form>
      </Card>

      <Card>
        <h2>Graph visualization</h2>
        {loading && <Loader />}
        {error && <p className="section-error">{error}</p>}
        {graphData ? (
          <div className="graph-canvas">
            <ReactFlow nodes={elements.filter((el) => el.id && el.position)} edges={elements.filter((el) => el.source)} fitView />
            <Background gap={16} />
            <Controls />
          </div>
        ) : (
          <EmptyState title="No graph loaded" description="Run a graph search to visualize the drug relationship." />
        )}
      </Card>
    </div>
  )
}
