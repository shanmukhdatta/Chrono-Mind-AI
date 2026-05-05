import { useCallback } from 'react'
import { useTaskStore } from '../store/taskStore'
import api from '../lib/api'
import toast from 'react-hot-toast'

export function useTasks() {
  const { setTasks, addTask, updateTask, removeTask, setLoading, setError } = useTaskStore()

  const fetchTasks = useCallback(async (date = null, status = 'all') => {
    setLoading(true)
    try {
      const params = {}
      if (date) params.date = date
      if (status !== 'all') params.status = status
      const response = await api.get('/api/tasks', { params })
      if (response.data.success) {
        setTasks(response.data.data)
      } else {
        setError(response.data.error)
      }
    } catch (error) {
      setError('Failed to load tasks')
      console.error('fetchTasks error:', error)
    }
  }, [setTasks, setLoading, setError])

  const createTask = useCallback(async (taskData) => {
    try {
      const response = await api.post('/api/tasks', taskData)
      if (response.data.success) {
        addTask(response.data.data)
        toast.success('Task created!')
        return response.data.data
      } else {
        toast.error(response.data.error || 'Failed to create task')
        return null
      }
    } catch (error) {
      if (error.response?.status === 409) {
        toast.error(error.response.data.error || 'Time conflict with existing task')
      } else if (error.response?.status === 400) {
        toast.error(error.response.data.error || 'Invalid task data')
      } else {
        toast.error('Failed to create task')
      }
      return null
    }
  }, [addTask])

  const updateTaskById = useCallback(async (taskId, updates) => {
    try {
      const response = await api.patch(`/api/tasks/${taskId}`, updates)
      if (response.data.success) {
        updateTask(response.data.data)
        toast.success('Task updated!')
        return response.data.data
      } else {
        toast.error(response.data.error || 'Failed to update task')
        return null
      }
    } catch (error) {
      if (error.response?.status === 409) {
        toast.error(error.response.data.error || 'Time conflict')
      } else {
        toast.error('Failed to update task')
      }
      return null
    }
  }, [updateTask])

  const deleteTask = useCallback(async (taskId) => {
    try {
      const response = await api.delete(`/api/tasks/${taskId}`)
      if (response.data.success) {
        removeTask(taskId)
        toast.success('Task deleted')
        return true
      }
      return false
    } catch (error) {
      toast.error('Failed to delete task')
      return false
    }
  }, [removeTask])

  const completeTask = useCallback(async (taskId) => {
    try {
      const response = await api.post(`/api/tasks/${taskId}/complete`)
      if (response.data.success) {
        updateTask(response.data.data)
        toast.success('Task completed! 🎉')
        return response.data.data
      }
      return null
    } catch (error) {
      toast.error('Failed to mark task complete')
      return null
    }
  }, [updateTask])

  return { fetchTasks, createTask, updateTaskById, deleteTask, completeTask }
}
