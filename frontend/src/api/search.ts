import { api, handleError } from './client'
import type { GraphResponse } from './types'

export async function searchDrug(drug: string): Promise<any> {
  try {
    const res = await api.get(`/search/${encodeURIComponent(drug)}`)
    return res.data
  } catch (e) {
    handleError(e)
    throw e
  }
}

export async function getGraphForPair(drug1: string, drug2: string): Promise<GraphResponse> {
  try {
    const res = await api.get<GraphResponse>(`/graph/${encodeURIComponent(drug1)}/${encodeURIComponent(drug2)}`)
    return res.data
  } catch (e) {
    handleError(e)
    throw e
  }
}
