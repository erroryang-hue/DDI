import { api, handleError } from './client'

export interface ExportReportRequest {
  drug1: string
  drug2: string
  risk_score: number
  severity: string
  mechanisms: string[]
  graph_paths: Array<Record<string, any>>
  recommendations: string[]
}

export async function exportReport(request: ExportReportRequest): Promise<Blob> {
  try {
    const res = await api.post('/export-report', request, {
      responseType: 'blob',
    })
    return res.data
  } catch (e) {
    handleError(e)
    throw e
  }
}
