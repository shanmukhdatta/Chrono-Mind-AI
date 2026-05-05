import React, { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useAuthStore } from '../store/authStore'
import { useTaskStore } from '../store/taskStore'
import { Clock, Calendar, Sparkles, Target, Repeat, Upload, ArrowRight, CheckCircle, Github } from 'lucide-react'
import { Button } from '../components/ui/Button'
import { motion, useScroll, useTransform } from 'framer-motion'

export default function Landing() {
  const { signIn } = useAuth()
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const heroRef = useRef(null)
  const { scrollYProgress } = useScroll()
  const opacity = useTransform(scrollYProgress, [0, 0.2], [1, 0])
  const scale = useTransform(scrollYProgress, [0, 0.2], [1, 0.95])

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

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 100 } }
  }

  return (
    <div className="min-h-screen bg-cream overflow-x-hidden font-sans">
      {/* Skip Link */}
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-peach text-white px-4 py-2 rounded-lg z-50">
        Skip to content
      </a>

      {/* Navbar */}
      <motion.nav 
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ type: "spring", stiffness: 100, damping: 20 }}
        className="fixed top-0 left-0 right-0 z-50 bg-white/40 backdrop-blur-xl border-b border-white/40 shadow-sm"
      >
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <motion.div 
            whileHover={{ scale: 1.05 }}
            className="flex items-center gap-2 cursor-pointer"
          >
            <div className="w-8 h-8 bg-gradient-to-tr from-peach to-peach-light rounded-lg flex items-center justify-center shadow-lg">
              <Clock className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold tracking-tight">
              <span className="text-peach">Chrono</span><span className="text-dark">Mind</span>
            </span>
          </motion.div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-dark-muted">
            <a href="#features" className="hover:text-peach transition-colors relative group">
              Features
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-peach transition-all group-hover:w-full"></span>
            </a>
            <a href="#how-it-works" className="hover:text-peach transition-colors relative group">
              How It Works
              <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-peach transition-all group-hover:w-full"></span>
            </a>
          </div>
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Button onClick={signIn} className="text-sm shadow-md shadow-peach/20 bg-peach hover:bg-peach-dark">Sign In</Button>
          </motion.div>
        </div>
      </motion.nav>

      <main id="main">
        {/* Hero */}
        <section ref={heroRef} className="relative min-h-screen flex items-center pt-16 overflow-hidden">
          {/* Animated Background blobs */}
          <motion.div 
            animate={{ 
              scale: [1, 1.2, 1],
              rotate: [0, 90, 0],
              opacity: [0.3, 0.5, 0.3]
            }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="absolute top-0 right-0 w-[800px] h-[800px] bg-gradient-to-bl from-peach/30 to-purple-300/30 rounded-full blur-[120px] -z-10" 
          />
          <motion.div 
            animate={{ 
              scale: [1, 1.5, 1],
              rotate: [0, -90, 0],
              opacity: [0.2, 0.4, 0.2]
            }}
            transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
            className="absolute -bottom-40 -left-40 w-[600px] h-[600px] bg-gradient-to-tr from-blue-300/30 to-peach-light/30 rounded-full blur-[100px] -z-10" 
          />

          <motion.div 
            style={{ opacity, scale }}
            className="max-w-7xl mx-auto px-6 py-20 grid lg:grid-cols-2 gap-12 items-center z-10"
          >
            <motion.div 
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="space-y-8"
            >
              <motion.div variants={itemVariants} className="inline-flex items-center gap-2 bg-white/60 backdrop-blur-md border border-white/50 shadow-sm rounded-full px-4 py-2">
                <Sparkles className="w-4 h-4 text-peach" />
                <span className="text-sm font-medium text-peach-dark">AI-Powered Day Planner</span>
              </motion.div>

              <motion.h1 variants={itemVariants} className="font-display text-5xl md:text-6xl lg:text-7xl font-bold text-dark leading-tight tracking-tight">
                Plan Less.<br />
                <span className="bg-gradient-to-r from-peach via-peach-dark to-orange-500 bg-clip-text text-transparent">Achieve More.</span>
              </motion.h1>

              <motion.p variants={itemVariants} className="text-xl text-dark-muted max-w-lg leading-relaxed">
                ChronoMind AI automatically reschedules your missed tasks — so you wake up to a plan, not a mess. Built for Indian engineering students.
              </motion.p>

              <motion.div variants={itemVariants} className="flex flex-wrap gap-4">
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button onClick={signIn} className="text-lg px-8 py-4 shadow-xl shadow-peach/30 bg-peach hover:bg-peach-dark">
                    Start for Free <ArrowRight className="w-5 h-5 ml-2 inline group-hover:translate-x-1 transition-transform" />
                  </Button>
                </motion.div>
                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button variant="outline" onClick={handleDemoMode} className="text-lg px-8 py-4 bg-white/40 backdrop-blur-md border-white/60 shadow-lg hover:bg-white/60 text-dark">
                    Try Demo →
                  </Button>
                </motion.div>
              </motion.div>

              <motion.div variants={itemVariants} className="flex items-center gap-6 text-sm text-dark-muted font-medium">
                {[
                  { text: 'Google Sign-In' },
                  { text: 'Free Forever' },
                  { text: 'No Credit Card' }
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-peach drop-shadow-sm" />
                    <span>{item.text}</span>
                  </div>
                ))}
              </motion.div>
            </motion.div>

            {/* Mockup */}
            <motion.div 
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 1, type: "spring", stiffness: 50 }}
              className="relative lg:h-[600px] flex items-center justify-center"
            >
              <motion.div 
                animate={{ y: [-10, 10, -10] }}
                transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                className="relative w-full max-w-md"
              >
                {/* Decorative element behind card */}
                <div className="absolute -inset-1 bg-gradient-to-r from-peach to-orange-300 rounded-3xl blur-xl opacity-30" />
                
                <div className="bg-white/40 backdrop-blur-xl border border-white/60 p-6 rounded-3xl shadow-2xl relative overflow-hidden">
                  {/* Inner shine */}
                  <div className="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-white/40 to-transparent pointer-events-none" />
                  
                  <div className="flex items-center gap-3 mb-6 relative z-10">
                    <div className="w-10 h-10 bg-gradient-to-br from-peach/30 to-peach/10 rounded-full flex items-center justify-center border border-white/50 shadow-inner">
                      <Clock className="w-5 h-5 text-peach-dark" />
                    </div>
                    <div>
                      <p className="font-semibold text-dark">Today's Tasks</p>
                      <p className="text-xs text-dark-muted">Monday, 5 May 2026</p>
                    </div>
                  </div>

                  <div className="space-y-3 relative z-10">
                    {[
                      { title: 'Fluid Mechanics Revision', time: '10:00 - 11:30', important: true },
                      { title: 'DSA Practice', time: '14:00 - 15:30', important: true },
                      { title: 'Coffee Break', time: '16:00 - 16:30', important: false },
                    ].map((task, i) => (
                      <motion.div 
                        whileHover={{ scale: 1.02, x: 5 }}
                        key={i} 
                        className={`p-3 rounded-xl border backdrop-blur-md transition-all cursor-pointer shadow-sm ${task.important ? 'bg-peach/10 border-peach/30' : 'bg-white/50 border-white/60'}`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-5 h-5 rounded-md border-2 ${task.important ? 'border-peach shadow-sm shadow-peach/20' : 'border-gray-300'}`} />
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-dark">{task.title}</p>
                            <p className="text-xs text-dark-muted font-medium">{task.time}</p>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>

                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 1 }}
                    className="mt-6 p-4 bg-blue-50/60 backdrop-blur-md border border-blue-200/50 rounded-xl shadow-sm relative z-10"
                  >
                    <p className="text-xs text-blue-800 font-medium flex items-center gap-2">
                      <Sparkles className="w-3 h-3" />
                      2 tasks from yesterday were rescheduled to today
                    </p>
                  </motion.div>
                </div>
              </motion.div>
            </motion.div>
          </motion.div>
        </section>

        {/* Features */}
        <section id="features" className="py-24 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-peach/5 to-transparent -z-10" />
          
          <div className="max-w-7xl mx-auto px-6">
            <motion.div 
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-100px" }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl md:text-5xl font-bold text-dark mb-4 tracking-tight">Everything your college schedule needs</h2>
              <p className="text-lg text-dark-muted max-w-2xl mx-auto">Built specifically for Indian engineering students who juggle lectures, labs, assignments, and self-study.</p>
            </motion.div>

            <motion.div 
              variants={containerVariants}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
              className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {features.map((feature, i) => (
                <motion.div 
                  variants={itemVariants}
                  whileHover={{ y: -5, scale: 1.02 }}
                  key={i} 
                  className="bg-white/40 backdrop-blur-xl border border-white/60 p-8 rounded-3xl shadow-lg hover:shadow-xl transition-all group"
                >
                  <div className="w-14 h-14 bg-gradient-to-br from-peach/20 to-peach/5 border border-white/50 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform shadow-inner">
                    <feature.icon className="w-7 h-7 text-peach-dark drop-shadow-sm" />
                  </div>
                  <h3 className="text-xl font-bold text-dark mb-3">{feature.title}</h3>
                  <p className="text-sm text-dark-muted leading-relaxed font-medium">{feature.desc}</p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* How It Works */}
        <section id="how-it-works" className="py-24 relative">
          <div className="max-w-7xl mx-auto px-6">
            <motion.div 
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl md:text-5xl font-bold text-dark mb-4 tracking-tight">How It Works</h2>
              <p className="text-lg text-dark-muted">Three simple steps to smarter scheduling</p>
            </motion.div>

            <div className="grid md:grid-cols-3 gap-8 relative">
              {/* Connecting line */}
              <div className="hidden md:block absolute top-12 left-[20%] right-[20%] h-0.5 bg-gradient-to-r from-peach/10 via-peach/40 to-peach/10" />

              {steps.map((step, i) => (
                <motion.div 
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.2 }}
                  key={i} 
                  className="relative text-center group"
                >
                  <motion.div 
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    className="w-24 h-24 bg-white/60 backdrop-blur-xl rounded-full flex items-center justify-center mx-auto mb-6 relative z-10 border border-white shadow-xl shadow-peach/10"
                  >
                    <span className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-br from-peach to-orange-400">{step.num}</span>
                  </motion.div>
                  <h3 className="text-xl font-bold text-dark mb-2">{step.title}</h3>
                  <p className="text-sm text-dark-muted font-medium px-4">{step.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Banner */}
        <section className="py-24 relative z-10">
          <div className="max-w-7xl mx-auto px-6">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              whileHover={{ scale: 1.01 }}
              className="bg-gradient-to-br from-peach to-orange-400 rounded-[2.5rem] p-12 md:p-16 text-center relative overflow-hidden shadow-2xl shadow-peach/30"
            >
              <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iMSIgZmlsbD0id2hpdGUiIG9wYWNpdHk9IjAuMiIvPjwvc3ZnPg==')] opacity-40 mix-blend-overlay" />
              
              <div className="absolute -top-24 -right-24 w-64 h-64 bg-white/20 rounded-full blur-3xl" />
              <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-white/20 rounded-full blur-3xl" />
              
              <h2 className="font-display text-4xl md:text-5xl font-bold text-white mb-6 relative z-10 drop-shadow-sm">
                Start planning smarter today.
              </h2>
              <p className="text-white/90 mb-10 max-w-lg mx-auto relative z-10 text-lg font-medium">
                Join thousands of engineering students who never miss a task again.
              </p>
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} className="inline-block relative z-10">
                <Button 
                  onClick={signIn}
                  className="bg-white/90 backdrop-blur-md text-peach-dark hover:bg-white text-lg px-10 py-5 rounded-2xl shadow-xl transition-all font-bold"
                >
                  Sign in with Google
                </Button>
              </motion.div>
            </motion.div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-white/60 backdrop-blur-lg border-t border-white/80 py-12 relative z-10 mt-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-tr from-peach to-orange-300 rounded-xl flex items-center justify-center shadow-md">
                <Clock className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="font-bold text-dark text-lg tracking-tight">ChronoMind AI</span>
                <p className="text-xs text-dark-muted font-medium">Plan Smarter. Study Better. Never Miss Again.</p>
              </div>
            </div>

            <div className="flex items-center gap-8 text-sm text-dark-muted font-medium">
              <a href="https://github.com/shanmukhdatta" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-peach transition-colors">
                <Github className="w-4 h-4" /> GitHub
              </a>
              <span>Built by Datta</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
