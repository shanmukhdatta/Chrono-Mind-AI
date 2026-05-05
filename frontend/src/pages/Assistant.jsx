import React from 'react'
import { Sparkles } from 'lucide-react'
import { useAssistantStore } from '../store/assistantStore'
import { AssistantPanel } from '../components/AssistantPanel'

export default function Assistant() {
  const { setOpen } = useAssistantStore()

  React.useEffect(() => {
    // Auto-open the assistant panel when navigating to /assistant
    setOpen(true)
  }, [])

  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 text-center">
      <div className="w-20 h-20 bg-peach/15 rounded-3xl flex items-center justify-center">
        <Sparkles className="w-10 h-10 text-peach" />
      </div>
      <div>
        <h1 className="text-2xl font-bold text-dark mb-2">AI Scheduling Assistant</h1>
        <p className="text-dark-muted max-w-sm">
          The assistant panel is open on the right. Type or use voice to schedule tasks, query your day, or set up recurring reminders.
        </p>
      </div>
      <div className="bg-peach/5 border border-peach/20 rounded-xl p-5 max-w-sm text-left space-y-3">
        <p className="text-sm font-semibold text-dark">Try saying:</p>
        {[
          '"Schedule DSA practice for 2 hours from now"',
          '"What tasks did I not finish today?"',
          '"Remind me to read every day at 9 PM"',
          '"Schedule fluid mechanics for tomorrow 10 AM"',
        ].map((s, i) => (
          <p key={i} className="text-sm text-dark-muted italic">{s}</p>
        ))}
      </div>
    </div>
  )
}
