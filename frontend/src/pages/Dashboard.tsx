import { useEffect, useMemo, useState } from 'react'
import { Bar, Pie, ResponsiveContainer, ComposedChart, XAxis, YAxis, Tooltip, CartesianGrid, Legend, BarChart, PieChart, Cell } from 'recharts'
import { getAnalytics } from '../api/analytics'
import { getRecentAnalyses, RecentAnalysisItem } from '../utils/storage'
import Card from '../components/Card'
import MetricCard from '../components/MetricCard'
import EmptyState from '../components/EmptyState'
import Loader from '../components/Loader'

const COLORS = ['#0b5fff', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#14b8a6']

export default function Dashboard() {
  const [analytics, setAnalytics] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    getAnalytics()
      .then(setAnalytics)
      .catch((err) => setError(err?.message || 'Unable to load analytics'))
      .finally(() => setLoading(false))
  }, [])

  const recentAnalyses = useMemo(() => getRecentAnalyses(), [])

  const severitySeries = useMemo(() => {
    const counts = recentAnalyses.reduce((acc, item) => {
      acc[item.severity] = (acc[item.severity] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    return Object.entries(counts).map(([name, value]) => ({ name, value }))
  }, [recentAnalyses])

  const categorySeries = useMemo(() => {
    const counts = recentAnalyses.reduce(
      (acc, item) => {
        const key = item.interaction ? 'Interactions' : 'No interaction'
        acc[key] += 1
        return acc
      },
      { Interactions: 0, 'No interaction': 0 }
    )
    return Object.entries(counts).map(([name, value]) => ({ name, value }))
  }, [recentAnalyses])

  if (loading) return <Loader />
  if (error) return <Card><p className="section-error">{error}</p></Card>

  return (
    <div className="page-grid">
      <div className="dashboard-top">
        <MetricCard label="Total Drugs" value={analytics?.total_drugs ?? '—'} />
        <MetricCard label="Total Enzymes" value={analytics?.total_enzymes ?? '—'} />
        <MetricCard label="Total Pathways" value={analytics?.total_pathways ?? '—'} />
        <MetricCard label="Total Side Effects" value={analytics?.total_side_effects ?? '—'} />
      </div>

      <div className="dashboard-row">
        <Card>
          <h2>Recent analyses</h2>
          {recentAnalyses.length ? (
            <div className="table-responsive">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Drug Pair</th>
                    <th>Risk Score</th>
                    <th>Severity</th>
                    <th>Interaction</th>
                    <th>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {recentAnalyses.map((item) => (
                    <tr key={item.id}>
                      <td>{item.drug1} / {item.drug2}</td>
                      <td>{item.risk_score.toFixed(3)}</td>
                      <td>{item.severity}</td>
                      <td>{item.interaction ? 'Yes' : 'No'}</td>
                      <td>{new Date(item.timestamp).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState title="No recent analyses" description="Run an interaction analysis to see recent reports appear here." />
          )}
        </Card>

        <Card>
          <h2>Risk distribution</h2>
          {severitySeries.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={severitySeries} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100} paddingAngle={4}>
                  {severitySeries.map((entry, index) => (
                    <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState title="No risk data" description="Complete an interaction analysis to populate risk charts." />
          )}
        </Card>
      </div>

      <div className="dashboard-row">
        <Card>
          <h2>Interaction category</h2>
          {categorySeries.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={categorySeries} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#0b5fff" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState title="No category data" description="Interaction results will generate category insights." />
          )}
        </Card>

        <Card>
          <h2>Popular actions</h2>
          <div className="analytics-list">
            <div>
              <strong>Top drugs</strong>
              <ul>
                {analytics?.top_drugs?.slice(0, 4).map((item: string) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
            <div>
              <strong>Top enzymes</strong>
              <ul>
                {analytics?.top_enzymes?.slice(0, 4).map((item: string) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
