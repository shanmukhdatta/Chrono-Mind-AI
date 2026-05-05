import { useCallback } from 'react'
import { useAssistantStore } from '../store/assistantStore'
import { useTaskStore } from '../store/taskStore'
import api from '../lib/api'
import toast from 'react-hot-toast'

export function useAssistant() {
  const { addMessage, setLoading } = useAssistantStore()
  const { addTask } = useTaskStore()

  const sendMessage = useCallback(async (text, currentMessages) => {
    setLoading(true)
    try {
      const history = currentMessages
        .filter(m => (m.role === 'user' || m.role === 'assistant') && m.content)
        .slice(-10)
        .map(m => ({ role: m.role, content: m.content }))

      const response = await api.post('/api/assistant/chat', {
        message: text,
        conversation_history: history,
      })

      if (response.data.success) {
        const { reply, action, action_result } = response.data.data
        addMessage({
          role: 'assistant',
          content: reply,
          timestamp: new Date().toISOString(),
        })
        return { reply, action, action_result }
      } else {
        const fallback = "I'm having trouble right now. Please try again."
        addMessage({ role: 'assistant', content: fallback, timestamp: new Date().toISOString() })
        return { reply: fallback, action: null, action_result: null }
      }
    } catch (error) {
      const fallback = "Connection error. Please check your network."
      addMessage({ role: 'assistant', content: fallback, timestamp: new Date().toISOString() })
      return { reply: fallback, action: null, action_result: null }
    } finally {
      setLoading(false)
    }
  }, [addMessage, setLoading])

  const executeAction = useCallback(async (action, action_result) => {
    if (!action_result) return null

    if (action_result.type === 'task_created' && action_result.task) {
      addTask(action_result.task)
      toast.success(`Task "${action_result.task.title}" added!`)
      return action_result.task
    }

    if (action_result.type === 'tasks_list') {
      return action_result  // Return for display in panel
    }

    if (action_result.type === 'error') {
      toast.error(action_result.message || 'Action failed')
      return null
    }

    return null
  }, [addTask])

  return { sendMessage, executeAction }
}
