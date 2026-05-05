import React, { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useAuthStore } from '../store/authStore'
import { useTaskStore } from '../store/taskStore'
import { Clock, Calendar, Sparkles, Target, Repeat, Upload, ArrowRight, CheckCircle, Github } from 'lucide-react'
import { Button } from '../components/ui/Button'

export default function Landing() {
  const { signIn } = useAuth()
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const heroRef = useRef(null)

  useEffect(() => {
    if (user) navigate('/dashboard')
  }, [user, navigate])

  const handleDemoMode = () => {
    useAuthStore.getState().enterDemoMode()
    useTaskStore.getState().seedDemoTasks()
    navigate('/dashboard')
  }

  const features = [
    { icon: Sparkles, title: 'Auto-Rescheduling', desc: 'Missed important tasks automatically move to tomorrow. Never lose a commitment again.' },
    { icon: Calendar, title: '24-Hour Calendar', desc: 'Full day view from midnight to midnight. Click any slot to add tasks instantly.' },
    { icon: Target, title: 'Smart Priority', desc: 'Important tasks get rescheduled. Not important ones get cleaned up. Smart clutter-free planning.' },
    { icon: Sparkles, title: 'AI Assistant', desc: 'Voice and text scheduling. Just say "Practice DSA for 1 hour from now" and it is done.' },
    { icon: Repeat, title: 'Recurring Tasks', desc: 'Set up daily, weekly, or custom recurring schedules. Let the pattern handle the repetition.' },
    { icon: Upload, title: 'Timetable Import', desc: 'Upload your college timetable (Phase 2 preview). OCR integration coming soon.' },
  ]

  const steps = [
    { num: '01', title: 'Add Your Tasks', desc: 'Manually or via AI voice assistant' },
    { num: '02', title: 'Focus on Your Day', desc: 'Work with a clean 24-hour calendar view' },
    { num: '03', title: 'ChronoMind Handles Rest', desc: 'Auto-reschedule what you missed overnight' },
  ]

  return (
    <div className="min-h-screen bg-cream overflow-x-hidden">
      {/* Skip Link */}
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-peach text-white px-4 py-2 rounded-lg z-50">
        Skip to content
      </a>

      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-40 bg-cream/90 backdrop-blur-md border-b border-gray-100/50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-peach rounded-lg flex items-center justify-center">
              <Clock className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold">
              <span className="text-peach">Chrono</span><span className="text-dark">Mind</span>
            </span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-dark-muted">
            <a href="#features" className="hover:text-peach transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-peach transition-colors">How It Works</a>
            <a href="#about" className="hover:text-peach transition-colors">About</a>
          </div>
          <Button onClick={signIn} className="text-sm">Sign In</Button>
        </div>
      </nav>

      <main id="main">
        {/* Hero */}
        <section ref={heroRef} className="relative min-h-screen flex items-center pt-16 overflow-hidden">
          {/* Background blobs */}
          <div className="absolute top-20 right-0 w-[600px] h-[600px] bg-peach/20 rounded-full blur-[120px] -z-10" />
          <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-peach-light/30 rounded-full blur-[100px] -z-10" />

          <div className="max-w-7xl mx-auto px-6 py-20 grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8 animate-fade-in">
              <div className="inline-flex items-center gap-2 bg-peach/10 border border-peach/20 rounded-full px-4 py-2">
                <Sparkles className="w-4 h-4 text-peach" />
                <span className="text-sm font-medium text-peach-dark">AI-Powered Day Planner</span>
              </div>

              <h1 className="font-display text-5xl md:text-6xl lg:text-7xl font-bold text-dark leading-tight">
                Plan Less.<br />
                <span className="text-gradient">Achieve More.</span>
              </h1>

              <p className="text-xl text-dark-muted max-w-lg leading-relaxed">
                ChronoMind AI automatically reschedules your missed tasks — so you wake up to a plan, not a mess. Built for Indian engineering students.
              </p>

              <div className="flex flex-wrap gap-4">
                <Button onClick={signIn} className="text-lg px-8 py-4">
                  Start for Free <ArrowRight className="w-5 h-5 ml-2 inline" />
                </Button>
                <Button variant="outline" onClick={handleDemoMode} className="text-lg px-8 py-4">
                  Try Demo →
                </Button>
              </div>

              <div className="flex items-center gap-6 text-sm text-dark-muted">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-peach" />
                  <span>Google Sign-In</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-peach" />
                  <span>Free Forever</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-peach" />
                  <span>No Credit Card</span>
                </div>
              </div>
            </div>

            {/* Mockup */}
            <div className="relative lg:h-[600px] flex items-center justify-center">
              <div className="relative w-full max-w-md animate-float">
                <div className="glass-card p-6 shadow-2xl">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="w-10 h-10 bg-peach/20 rounded-full flex items-center justify-center">
                      <Clock className="w-5 h-5 text-peach" />
                    </div>
                    <div>
                      <p className="font-semibold text-dark">Today's Tasks</p>
                      <p className="text-xs text-dark-muted">Monday, 5 May 2026</p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {[
                      { title: 'Fluid Mechanics Revision', time: '10:00 - 11:30', important: true },
                      { title: 'DSA Practice', time: '14:00 - 15:30', important: true },
                      { title: 'Coffee Break', time: '16:00 - 16:30', important: false },
                    ].map((task, i) => (
                      <div key={i} className={`p-3 rounded-xl border ${task.important ? 'bg-peach/10 border-peach/20' : 'bg-gray-50 border-gray-100'}`}>
                        <div className="flex items-center gap-3">
                          <div className={`w-5 h-5 rounded-md border-2 ${task.important ? 'border-peach' : 'border-gray-300'}`} />
                          <div className="flex-1">
                            <p className="text-sm font-medium text-dark">{task.title}</p>
                            <p className="text-xs text-dark-muted">{task.time}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 p-3 bg-blue-50 border border-blue-100 rounded-xl">
                    <p className="text-xs text-blue-700 font-medium">
                      2 tasks from yesterday were rescheduled to today
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section id="features" className="py-24 relative">
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-peach/5 to-transparent -z-10" />
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="section-title mb-4">Everything your college schedule needs</h2>
              <p className="text-dark-muted max-w-2xl mx-auto">Built specifically for Indian engineering students who juggle lectures, labs, assignments, and self-study.</p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feature, i) => (
                <div 
                  key={i} 
                  className="glass-card p-6 card-hover group"
                >
                  <div className="w-12 h-12 bg-peach/15 rounded-xl flex items-center justify-center mb-4 group-hover:bg-peach/25 transition-colors">
                    <feature.icon className="w-6 h-6 text-peach-dark" />
                  </div>
                  <h3 className="text-lg font-semibold text-dark mb-2">{feature.title}</h3>
                  <p className="text-sm text-dark-muted leading-relaxed">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section id="how-it-works" className="py-24">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="section-title mb-4">How It Works</h2>
              <p className="text-dark-muted">Three simple steps to smarter scheduling</p>
            </div>

            <div className="grid md:grid-cols-3 gap-8 relative">
              {/* Connecting line */}
              <div className="hidden md:block absolute top-12 left-[20%] right-[20%] h-0.5 border-t-2 border-dashed border-peach/30" />

              {steps.map((step, i) => (
                <div key={i} className="relative text-center">
                  <div className="w-24 h-24 bg-peach/10 rounded-2xl flex items-center justify-center mx-auto mb-6 relative z-10 border-2 border-peach/20">
                    <span className="text-2xl font-bold text-peach">{step.num}</span>
                  </div>
                  <h3 className="text-lg font-semibold text-dark mb-2">{step.title}</h3>
                  <p className="text-sm text-dark-muted">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Banner */}
        <section className="py-24">
          <div className="max-w-7xl mx-auto px-6">
            <div className="peach-gradient rounded-3xl p-12 md:p-16 text-center relative overflow-hidden">
              <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iMSIgZmlsbD0id2hpdGUiIG9wYWNpdHk9IjAuMiIvPjwvc3ZnPg==')] opacity-30" />
              <h2 className="font-display text-3xl md:text-4xl font-bold text-dark mb-6 relative">
                Start planning smarter today.
              </h2>
              <p className="text-dark/70 mb-8 max-w-lg mx-auto relative">
                Join thousands of engineering students who never miss a task again.
              </p>
              <Button 
                onClick={signIn}
                className="bg-white text-dark hover:bg-gray-100 text-lg px-8 py-4 relative"
              >
                Sign in with Google
              </Button>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-100 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-peach rounded-lg flex items-center justify-center">
                <Clock className="w-4 h-4 text-white" />
              </div>
              <div>
                <span className="font-bold text-dark">ChronoMind AI</span>
                <p className="text-xs text-dark-muted">Plan Smarter. Study Better. Never Miss Again.</p>
              </div>
            </div>

            <div className="flex items-center gap-6 text-sm text-dark-muted">
              <a href="https://github.com/shanmukhdatta" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-peach transition-colors">
                <Github className="w-4 h-4" /> GitHub
              </a>
              <span>Built by Datta</span>
              <span>© 2026 Nerds Room — NIT Jalandhar</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
