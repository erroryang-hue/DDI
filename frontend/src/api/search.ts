import { api, handleError } from './client'
import type { GraphResponse } from './types'

export async function getDrugsList(): Promise<any> {
  try {
    const res = await api.get(`/drugs`)
    return res.data
  } catch (e) {
    handleError(e)
    throw e
  }
}

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

export async function getNeighborhood(drugId: string, depth = 2): Promise<GraphResponse> {
  try {
    const res = await api.get<GraphResponse>(`/graph/neighborhood/${encodeURIComponent(drugId)}?depth=${depth}`)
    return res.data
  } catch (e) {
    handleError(e)
    throw e
  }
}
