export interface AnalyzeResponse {
  interaction: boolean
  risk_score: number
  severity: string
  mechanisms: string[]
  graph_paths: Array<Record<string, any>>
  explanation: string
  recommendations: string[]
}

export interface ExportReportRequest {
  drug1: string
  drug2: string
  risk_score: number
  severity: string
  mechanisms: string[]
  graph_paths: Array<Record<string, any>>
  recommendations: string[]
}

export interface PolypharmacyResponse {
  highest_risk: { drug1: string; drug2: string; risk: number }
  average_risk: number
  results: Array<{ drug1: string; drug2: string; risk: number }>
}

export interface TimelinePoint {
  hour: number
  risk: number
  temporal_overlap?: number
}

export interface GraphNode { id: string; label: string; type: string }
export interface GraphEdge { source: string; target: string; label?: string }

export interface GraphResponse { nodes: GraphNode[]; edges: GraphEdge[] }

export interface AlternativesItem {
  drug_id: string
  score: number
}

export type AlternativesResponse = AlternativesItem[]

export interface AnalyticsResponse {
  total_drugs: number
  total_enzymes: number
  total_pathways: number
  total_side_effects: number
  top_drugs: string[]
  top_enzymes: string[]
  top_pathways: string[]
  top_side_effects: string[]
}
