import { api, handleError } from './client'
import type { PolypharmacyResponse } from './types'

export async function analyzePolypharmacy(drugs: string[]): Promise<PolypharmacyResponse> {
  try {
    const res = await api.post<PolypharmacyResponse>('/polypharmacy', { drugs })
    return res.data
  } catch (e) {
    handleError(e)
    throw e
  }
}
