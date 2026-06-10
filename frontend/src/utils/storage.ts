import type { AnalyzeResponse } from '../api/types'

const STORAGE_KEY = 'ddi_recent_analyses'

export interface RecentAnalysisItem {
  id: string
  drug1: string
  drug2: string
  risk_score: number
  severity: string
  interaction: boolean
  timestamp: string
}

export function getRecentAnalyses(): RecentAnalysisItem[] {
  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (!stored) return []
  try {
    return JSON.parse(stored) as RecentAnalysisItem[]
  } catch {
    return []
  }
}

export function saveRecentAnalysis(result: AnalyzeResponse, drug1: string, drug2: string): void {
  const existing = getRecentAnalyses()
  const item: RecentAnalysisItem = {
    id: `${drug1}-${drug2}-${Date.now()}`,
    drug1,
    drug2,
    risk_score: result.risk_score,
    severity: result.severity,
    interaction: result.interaction,
    timestamp: new Date().toISOString(),
  }
  const next = [item, ...existing].slice(0, 10)
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
}
