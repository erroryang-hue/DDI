import { api, handleError } from './client'
import type { AnalyticsResponse } from './types'

export async function getAnalytics(): Promise<AnalyticsResponse> {
  try {
    const res = await api.get<AnalyticsResponse>('/analytics')
    return res.data
  } catch (e) {
    handleError(e)
    throw e
  }
}
