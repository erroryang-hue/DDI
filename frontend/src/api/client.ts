import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
})

export function handleError(e: unknown) {
  if (axios.isAxiosError(e)) {
    if (e.response) throw new Error(e.response.data?.error || JSON.stringify(e.response.data))
    throw new Error(e.message)
  }
  throw e
}
