import { api, handleError } from './client'
import type { TimelinePoint } from './types'

export interface TimelineRequest {
  drug1: string
  drug2: string
  start1: number
  start2: number
  interval1: number
  interval2: number
  half_life1: number
  half_life2: number
}

export async function getTimeline(request: TimelineRequest): Promise<TimelinePoint[]> {
  try {
    const res = await api.post<TimelinePoint[]>('/timeline', request)
    return res.data
  } catch (e) {
    handleError(e)
    throw e
  }
}
