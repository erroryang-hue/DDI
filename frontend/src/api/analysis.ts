import { api, handleError } from './client'
import type { AnalyzeResponse } from './types'

export interface AnalyzeRequest {
  drug1: string
  drug2: string
  age?: number
  weight?: number
  dose1?: number
  dose2?: number
  // time between drug1 and drug2 in hours
  time_between?: number
  interval1?: number
  interval2?: number
  poor_metabolizer?: boolean
}

export async function analyzeInteraction(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  try {
    const hoursOffset = request.time_between || 0
    const payload = {
      drug1: request.drug1,
      drug2: request.drug2,
      age: request.age || 65,
      weight: request.weight || 75,
      dose1: request.dose1 || 500,
      dose2: request.dose2 || 5,
      start1: 0, // First drug starts at time 0
      start2: hoursOffset, // Second drug offset from first (hours)
      interval1: request.interval1 || 24,
      interval2: request.interval2 || 24,
      // half_life values will be looked up server-side from the dataset
      poor_metabolizer: request.poor_metabolizer || false,
    }
    
    const res = await api.post<AnalyzeResponse>('/analyze', payload)
    return res.data
  } catch (e) {
    handleError(e)
    throw e
  }
}
