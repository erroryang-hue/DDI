import { api, handleError } from './client'
import type { GraphResponse } from './types'

export async function getNeighborhood(drugId: string, depth = 2): Promise<GraphResponse> {
  try {
    const res = await api.get<GraphResponse>(`/graph/neighborhood/${encodeURIComponent(drugId)}?depth=${depth}`)
    return res.data
  } catch (e) {
    handleError(e)
    throw e
  }
}

export async function getPairGraph(drugA: string, drugB: string): Promise<GraphResponse> {
  try {
    const res = await api.get<GraphResponse>(`/graph/${encodeURIComponent(drugA)}/${encodeURIComponent(drugB)}`)
    return res.data
  } catch (e) {
    handleError(e)
    throw e
  }
}
