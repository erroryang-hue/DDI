import { useEffect, useState } from 'react'
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, BarChart, CartesianGrid, XAxis, YAxis, Bar } from 'recharts'
import { getAnalytics } from '../api/analytics'
import Card from '../components/Card'
import MetricCard from '../components/MetricCard'
import Loader from '../components/Loader'
import EmptyState from '../components/EmptyState'

const COLORS = ['#0b5fff', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

export default function Analytics() {
  const [analytics, setAnalytics] = useState<any | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    getAnalytics()
      .then(setAnalytics)
      .catch((err) => setError(err?.message || 'Unable to load analytics'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loader />
  if (error) return <Card><p className="section-error">{error}</p></Card>

  const enzymeSeries = analytics?.top_enzymes?.slice(0, 5).map((name: string, index: number) => ({ name, value: 1 + index })) ?? []
  const pathwaySeries = analytics?.top_pathways?.slice(0, 5).map((name: string, index: number) => ({ name, value: 1 + index })) ?? []

  return (
    <div className="page-grid">
      <div className="dashboard-top">
        <MetricCard label="Total drugs" value={analytics?.total_drugs ?? '—'} />
        <MetricCard label="Total enzymes" value={analytics?.total_enzymes ?? '—'} />
        <MetricCard label="Total pathways" value={analytics?.total_pathways ?? '—'} />
        <MetricCard label="Total side effects" value={analytics?.total_side_effects ?? '—'} />
      </div>

      <Card>
        <h2>Key metrics</h2>
        <div className="analytics-grid">
          <div className="analytics-item">
            <p className="metric-label">Top drugs</p>
            <ul>
              {analytics?.top_drugs?.slice(0, 6).map((item: string) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
          <div className="analytics-item">
            <p className="metric-label">Top side effects</p>
            <ul>
              {analytics?.top_side_effects?.slice(0, 6).map((item: string) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      </Card>

      <div className="dashboard-row">
        <Card>
          <h2>Top enzymes</h2>
          {enzymeSeries.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={enzymeSeries} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#0b5fff" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState title="No enzyme data" description="Analytics API returned no enzyme metrics." />
          )}
        </Card>

        <Card>
          <h2>Top pathways</h2>
          {pathwaySeries.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={pathwaySeries} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100}>
                  {pathwaySeries.map((entry: any, index: number) => (
                    <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyState title="No pathway data" description="Analytics API returned no pathway metrics." />
          )}
        </Card>
      </div>
    </div>
  )
}
