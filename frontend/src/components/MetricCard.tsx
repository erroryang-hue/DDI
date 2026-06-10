import React from 'react'

interface MetricCardProps {
  label: string
  value: string | number
  subtitle?: string
}

export default function MetricCard({ label, value, subtitle }: MetricCardProps) {
  return (
    <div className="metric-card">
      <p className="metric-label">{label}</p>
      <h3 className="metric-value">{value}</h3>
      {subtitle && <p className="metric-subtitle">{subtitle}</p>}
    </div>
  )
}
