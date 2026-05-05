import axios from 'axios'
import { getAuth } from 'firebase/auth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// Attach Firebase ID token to every request
api.interceptors.request.use(async (config) => {
  const { useAuthStore } = await import('../store/authStore')
  const storeUser = useAuthStore.getState().user
  if (storeUser?.uid === 'demo') {
    return config // skip token for demo mode
  }

  const auth = getAuth()
  const user = auth.currentUser
  if (user) {
    try {
      const token = await user.getIdToken(false) // false = use cached token
      config.headers.Authorization = `Bearer ${token}`
    } catch (err) {
      console.error('Failed to get ID token:', err)
    }
  }
  return config
}, (error) => Promise.reject(error))

// On 401, force token refresh once and retry
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    // Demo Mode Bypass
    const { useAuthStore } = await import('../store/authStore')
    const storeUser = useAuthStore.getState().user
    if (storeUser?.uid === 'demo' && error.response?.status === 401) {
      const method = originalRequest.method
      const url = originalRequest.url || ''
      const { useTaskStore } = await import('../store/taskStore')
      const tasks = useTaskStore.getState().tasks
      
      if (method === 'get' && url.includes('/api/tasks')) {
        return Promise.resolve({ data: { success: true, data: tasks } })
      } else if (method === 'get' && url.includes('/api/notifications')) {
        return Promise.resolve({ data: { success: true, data: [] } })
      } else if (method === 'post' && url.includes('/complete')) {
        const taskId = url.split('/')[3]
        const task = tasks.find(t => t.task_id === taskId)
        return Promise.resolve({ data: { success: true, data: { ...task, completed: true } } })
      } else if (method === 'post' && url.endsWith('/api/tasks')) {
        const body = JSON.parse(originalRequest.data)
        return Promise.resolve({ data: { success: true, data: { ...body, task_id: 'demo-' + Date.now(), completed: false, rescheduled: false } } })
      } else if (method === 'patch' && url.includes('/api/tasks/')) {
        const taskId = url.split('/').pop()
        const body = JSON.parse(originalRequest.data)
        const task = tasks.find(t => t.task_id === taskId)
        return Promise.resolve({ data: { success: true, data: { ...task, ...body } } })
      } else if (method === 'delete') {
        return Promise.resolve({ data: { success: true } })
      }
      return Promise.resolve({ data: { success: true, data: {} } })
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const auth = getAuth()
      const user = auth.currentUser
      if (user) {
        try {
          const freshToken = await user.getIdToken(true) // force refresh
          originalRequest.headers.Authorization = `Bearer ${freshToken}`
          return api(originalRequest)
        } catch (refreshErr) {
          console.error('Token refresh failed:', refreshErr)
          window.location.href = '/'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api
