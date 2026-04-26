import axios from 'axios'

export function getStoredAuth() {
  try {
    return JSON.parse(localStorage.getItem('chronomind-auth') || '{}')?.state || {}
  } catch {
    return {}
  }
}

export function isDemoMode() {
  const { token, user } = getStoredAuth()
  return token === 'mock-token-123' || user?.email?.includes('@demo.chronomind.ai')
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Response interceptor — handle 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      // Clear auth and redirect to login
      localStorage.removeItem('chronomind-auth')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
