import { api, handleError } from './client'
import type { AlternativesResponse } from './types'

export async function getAlternatives(drug: string): Promise<AlternativesResponse> {
  try {
    const res = await api.get<AlternativesResponse>(`/alternatives/${encodeURIComponent(drug)}`)
    return res.data
  } catch (e) {
    handleError(e)
    throw e
  }
}
