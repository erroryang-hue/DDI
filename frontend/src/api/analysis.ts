import { api, handleError } from './client'
import type { AnalyzeResponse } from './types'

export interface AnalyzeRequest {
  drug1: string
  drug2: string
  start1: string
  start2: string
  half_life1: number
  half_life2: number
}

export async function analyzeInteraction(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  try {
    const res = await api.post<AnalyzeResponse>('/analyze', request)
    return res.data
  } catch (e) {
    handleError(e)
    throw e
  }
}
