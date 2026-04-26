import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, useScroll, useTransform, useMotionValue, useSpring } from 'framer-motion'
import {
  Clock, Zap, Calendar, Mic, ArrowRight, CheckCircle,
  Star, Upload, Brain, BarChart3, ChevronDown, Check, Plus, MessageSquare, Menu, FileText
} from 'lucide-react'
import { useAuthStore } from '../../store'
import { MagneticButton, WordReveal, CountUp, GlassCard, RevealOnScroll } from '../ui'
import api from '../../api'
import toast from 'react-hot-toast'

const TESTIMONIALS = [
  { name: 'Arjun Sharma', role: '3rd Year, IIT Bombay', text: 'ChronoMind found free slots I never knew existed. My study schedule is actually realistic now.', stars: 5 },
  { name: 'Priya Nair', role: '2nd Year, NIT Trichy', text: 'The voice feature is insane. I schedule tasks while walking to class. Game changer.', stars: 5 },
  { name: 'Rohan Kumar', role: '2nd Year, IIT Delhi', text: 'AI placed my DSA assignment prep perfectly around my lab. Passed with 89%!', stars: 5 },
  { name: 'Sneha Gupta', role: '1st Year, BITS Pilani', text: 'Finally a planner that actually understands a college schedule. No more missed deadlines.', stars: 5 },
  { name: 'Vikram Singh', role: '4th Year, VIT', text: 'Onboarded in under 5 minutes. The timetable OCR was accurate first try.', stars: 5 },
  { name: 'Ananya Patel', role: '3rd Year, IIIT Hyderabad', text: 'The 24-hour calendar view is beautiful. I can see exactly where my free time is.', stars: 5 },
]

export default function Landing() {
  const { isAuthenticated, setAuth } = useAuthStore()
  const navigate = useNavigate()
  
  // Parallax + Tilt logic for Hero mockup
  const heroRef = useRef(null)
  const mx = useMotionValue(0)
  const my = useMotionValue(0)
  const tiltX = useSpring(useTransform(my, [-500, 500], [5, -5]), { stiffness: 200, damping: 30 })
  const tiltY = useSpring(useTransform(mx, [-500, 500], [-5, 5]), { stiffness: 200, damping: 30 })
  const px = useSpring(useTransform(mx, [-500, 500], [-10, 10]), { stiffness: 200, damping: 30 })
  const py = useSpring(useTransform(my, [-500, 500], [-10, 10]), { stiffness: 200, damping: 30 })

  const { scrollY } = useScroll()
  const chevronOpacity = useTransform(scrollY, [0, 200], [1, 0])

  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard')
    const handleMouseMove = (e) => {
      mx.set(e.clientX - window.innerWidth / 2)
      my.set(e.clientY - window.innerHeight / 2)
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [isAuthenticated, mx, my])

  const handleDemoLogin = async () => {
    try {
      const { data } = await api.post('/auth/demo')
      setAuth(data.user, data.access_token)
      navigate('/dashboard')
    } catch {
      toast.success('UI Showcase Mode (Backend is currently installing)')
      setAuth({ name: 'Demo User', email: 'demo@chronomind.ai' }, 'mock-token-123')
      navigate('/dashboard')
    }
  }

  // Demo Voice State
  const [voiceActive, setVoiceActive] = useState(false)

  return (
    <div className="relative overflow-hidden w-full">
      {/* HERO SECTION */}
      <section ref={heroRef} className="min-h-screen relative flex items-center justify-center px-6 pt-24 pb-16">
        <div className="max-w-7xl mx-auto w-full grid md:grid-cols-2 gap-12 items-center relative">
          
          <div className="text-left z-10">
            <motion.div
              className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full text-sm font-medium mb-8"
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
              style={{ color: 'var(--deep-peach)' }}
            >
              <Zap size={13} /> Powered by LangGraph AI + Groq LLM
            </motion.div>
            <h1 className="text-5xl md:text-7xl font-black leading-[1.1] mb-6" style={{ fontFamily: 'Inter' }}>
              <div><WordReveal text="Plan Smarter." className="gradient-text" /></div>
              <div><WordReveal text="Live Fuller." delay={0.25} className="text-gradient-peach" /></div>
            </h1>
            <motion.p className="text-lg md:text-xl max-w-lg mb-10 leading-relaxed"
              style={{ color: 'var(--text-2)' }} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.6 }}>
              The AI-powered day planner that reads your timetable, finds your free slots,
              and schedules tasks automatically — by voice or text.
            </motion.p>
            <motion.div className="flex flex-col sm:flex-row items-center gap-4"
              initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.8 }}>
              <MagneticButton className="btn-primary flex items-center gap-2 text-base" onClick={handleDemoLogin}>
                Try Demo Free <ArrowRight size={16} />
              </MagneticButton>
              <Link to="/register"><MagneticButton className="btn-ghost flex items-center gap-2 text-base">Create Account</MagneticButton></Link>
            </motion.div>
          </div>

          <div className="relative h-[600px] hidden md:flex items-center justify-center perspective-[1000px]">
            {/* Phone Mockup glass card */}
            <motion.div 
              className="glass absolute w-[300px] h-[600px] flex flex-col p-4 shadow-2xl"
              style={{ 
                borderRadius: 40,
                rotateX: tiltX, rotateY: tiltY, x: px, y: py,
                background: 'rgba(255,255,255,0.1)'
              }}
              initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: [0, -12, 0] }}
              transition={{ opacity: { delay: 0.6, duration: 1 }, y: { delay: 0.6, duration: 4, repeat: Infinity, ease: 'easeInOut' } }}
            >
              <div className="w-full flex-1 rounded-3xl bg-white/5 border border-white/10 p-3 overflow-hidden flex flex-col gap-3">
                <div className="h-6 w-1/3 rounded-md bg-white/20 mb-2"></div>
                <div className="flex-1 rounded-xl bg-[#2A9D8F]/20 border border-[#2A9D8F]/40 p-3"><div className="h-4 w-1/2 rounded bg-white/30 mb-2"></div></div>
                <div className="flex-1 rounded-xl bg-[#F4A261]/20 border border-[#F4A261]/40 p-3"><div className="h-4 w-1/2 rounded bg-white/30 mb-2"></div></div>
                <div className="flex-1 rounded-xl bg-[#E9C46A]/20 border border-[#E9C46A]/40 p-3"><div className="h-4 w-1/2 rounded bg-white/30 mb-2"></div></div>
              </div>
            </motion.div>

            {/* Stat Pills */}
            <motion.div className="glass absolute -left-12 top-20 px-5 py-3 rounded-full font-bold flex items-center gap-2"
              initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1, y: [0, -10, 0] }} transition={{ opacity: { delay: 1 }, scale: { delay: 1 }, y: { duration: 3.5, repeat: Infinity, ease: 'easeInOut' } }}>
              🎯 847 slots found
            </motion.div>
            <motion.div className="glass absolute -right-8 bottom-32 px-5 py-3 rounded-full font-bold flex items-center gap-2"
              initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1, y: [0, -15, 0] }} transition={{ opacity: { delay: 1.2 }, scale: { delay: 1.2 }, y: { duration: 4.5, repeat: Infinity, ease: 'easeInOut' } }}>
              ✅ 94% completion
            </motion.div>
            <motion.div className="glass absolute -right-6 top-40 px-5 py-3 rounded-full font-bold flex items-center gap-2"
              initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1, y: [0, -12, 0] }} transition={{ opacity: { delay: 1.4 }, scale: { delay: 1.4 }, y: { duration: 5, repeat: Infinity, ease: 'easeInOut' } }}>
              🤖 23 AI tasks
            </motion.div>
          </div>
        </div>

        {/* Scroll Indicator */}
        <motion.div className="absolute bottom-6 left-1/2 -translate-x-1/2" style={{ opacity: chevronOpacity }}>
          <motion.div animate={{ y: [0, 8, 0] }} transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}>
            <ChevronDown size={24} style={{ color: 'var(--text-3)' }} />
          </motion.div>
        </motion.div>
      </section>

      {/* SECTION 1: OCR */}
      <section className="min-h-[80vh] flex items-center px-6 py-24 relative overflow-hidden">
        <div className="max-w-6xl mx-auto w-full grid md:grid-cols-2 gap-16 items-center">
          <div className="relative h-[600px] flex items-center justify-center">
            <GlassCard className="w-[300px] h-[550px] p-4 relative overflow-hidden flex flex-col" style={{ borderRadius: 32 }}>
              <motion.div className="w-16 h-16 rounded-2xl bg-[#E9C46A]/20 flex items-center justify-center mx-auto mt-10 mb-4 z-10"
                initial={{ y: -50, opacity: 0 }} whileInView={{ y: 0, opacity: 1 }} transition={{ type: 'spring' }} viewport={{ once: false, amount: 0.5 }}>
                <FileText size={24} color="#E9C46A" />
              </motion.div>
              <div className="flex flex-col gap-3 w-full mt-4 flex-1">
                {Array.from({ length: 6 }).map((_, i) => (
                  <motion.div key={i} className="h-8 bg-white/10 rounded-lg w-full"
                    initial={{ x: -20, opacity: 0 }} whileInView={{ x: 0, opacity: 1 }} transition={{ delay: 0.4 + i * 0.1 }} viewport={{ once: false }} />
                ))}
              </div>
              <motion.div className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-[#E9C46A] to-transparent shadow-[0_0_15px_#E9C46A] z-20 pointer-events-none"
                animate={{ top: ['10%', '90%', '10%'] }} transition={{ duration: 3, repeat: Infinity, ease: "linear" }} />
            </GlassCard>
          </div>
          <div>
            <h2 className="text-4xl md:text-5xl font-black mb-6" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}><WordReveal text="OCR Timetable Import" /></h2>
            <RevealOnScroll><p className="text-lg mb-8" style={{ color: 'var(--text-2)' }}>Drag and drop your class timetable image. Our AI instantly extracts your schedule and builds your weekly grid.</p></RevealOnScroll>
            <div className="flex flex-col gap-4">
              {['Lightning fast extraction', 'Works with irregular grids', 'Creates uneditable class blocks'].map((f, i) => (
                <motion.div key={f} className="glass px-4 py-3 rounded-xl flex items-center gap-3 font-semibold" initial={{ x: 30, opacity: 0 }} whileInView={{ x: 0, opacity: 1 }} transition={{ delay: i * 0.1 }}>
                  <CheckCircle size={18} color="var(--peach)" /> {f}
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 2: AI Calendar Placement */}
      <section className="min-h-[80vh] flex items-center px-6 py-24 relative overflow-hidden bg-white/5">
        <div className="max-w-6xl mx-auto w-full grid md:grid-cols-2 gap-16 items-center">
          <div className="order-2 md:order-1">
            <h2 className="text-4xl md:text-5xl font-black mb-6" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}><WordReveal text="AI Finds Your Slot" /></h2>
            <RevealOnScroll><p className="text-lg mb-8" style={{ color: 'var(--text-2)' }}>Just say what needs to be done. The LangGraph agent scans your calendar and places tasks in the perfect free slot.</p></RevealOnScroll>
            <div className="flex flex-col gap-4">
              <motion.div className="glass px-5 py-4 rounded-2xl rounded-bl-sm max-w-[80%] text-sm" initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }}>
                Find me 2 hours for DSA practice today.
              </motion.div>
              <motion.div className="glass px-5 py-4 rounded-2xl rounded-br-sm max-w-[80%] self-end text-sm text-right" style={{ background: 'var(--peach)', color: 'white' }} initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
                Done! Placed DSA practice from 4 PM - 6 PM before your dinner. ✅
              </motion.div>
            </div>
          </div>
          <div className="order-1 md:order-2 relative h-[500px] flex items-center justify-center">
            <GlassCard className="w-full max-w-[360px] p-6 !rounded-3xl relative">
              <div className="flex flex-col gap-2 relative">
                <div className="h-16 rounded-xl bg-white/10" />
                <motion.div className="absolute top-[72px] inset-x-0 h-16 rounded-xl border border-dashed border-[#2A9D8F]/50 bg-[#2A9D8F]/10 z-0"
                  animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 1.5, repeat: Infinity }} />
                <motion.div className="h-16 rounded-xl bg-[#2A9D8F] shadow-[0_4px_20px_rgba(42,157,143,0.3)] z-10 relative flex items-center px-4"
                  initial={{ y: -40, opacity: 0 }} whileInView={{ y: 0, opacity: 1 }} transition={{ type: 'spring', delay: 1, bounce: 0.5 }}>
                  <span className="text-white font-bold text-sm">DSA Practice</span>
                  <motion.div className="ml-auto glass px-2 py-1 !rounded-full text-[10px] text-white font-bold" initial={{ scale: 0 }} whileInView={{ scale: [0, 1.2, 1] }} transition={{ delay: 1.5 }}>
                    Placed! ✦
                  </motion.div>
                </motion.div>
                <div className="h-16 rounded-xl bg-white/10" />
                <div className="h-16 rounded-xl bg-[#E76F51]/80" />
              </div>
            </GlassCard>
          </div>
        </div>
      </section>

      {/* SECTION 3: Voice */}
      <section className="min-h-[80vh] flex flex-col items-center justify-center px-6 py-24 text-center">
        <RevealOnScroll className="max-w-2xl mb-12">
          <h2 className="text-4xl md:text-5xl font-black mb-6" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}><WordReveal text="Voice-First Planning" /></h2>
          <p className="text-lg" style={{ color: 'var(--text-2)' }}>Speak naturally — "study for 2 hours before exam" — and watch ChronoMind schedule it instantly.</p>
        </RevealOnScroll>
        
        <div className="relative w-full h-[200px] flex flex-col items-center justify-center my-8">
          <div className="relative flex items-center justify-center w-32 h-32">
            <motion.div className="absolute w-full h-full rounded-full border-2 border-[#2A9D8F]" animate={{ scale: [1, 2], opacity: [0.6, 0] }} transition={{ duration: 2, repeat: Infinity }} />
            <motion.div className="absolute w-full h-full rounded-full border-2 border-[#2A9D8F]" animate={{ scale: [1, 2.5], opacity: [0.4, 0] }} transition={{ duration: 2, delay: 0.6, repeat: Infinity }} />
            <motion.button className="w-24 h-24 rounded-full flex items-center justify-center z-10 text-white"
              style={{ background: 'linear-gradient(135deg, #2A9D8F, #264653)' }}
              animate={{ boxShadow: ['0 0 0px rgba(42,157,143,0)', '0 0 30px rgba(42,157,143,0.5)', '0 0 0px rgba(42,157,143,0)'] }}
              transition={{ duration: 2, repeat: Infinity }}
              onPointerDown={() => setVoiceActive(true)} onPointerUp={() => setVoiceActive(false)}>
              <Mic size={36} />
            </motion.button>
          </div>
          
          <div className="h-20 mt-8 flex items-center">
            {voiceActive ? (
              <motion.div className="flex items-end gap-1 h-16 justify-center">
                {Array.from({ length: 30 }).map((_, i) => (
                  <motion.div key={i} className="waveform-bar w-1.5 rounded-full" style={{ background: '#2A9D8F' }}
                    animate={{ height: [`${Math.random() * 20 + 10}px`, `${Math.random() * 50 + 20}px`, `${Math.random() * 20 + 10}px`] }}
                    transition={{ duration: 0.4 + Math.random() * 0.2, repeat: Infinity }} />
                ))}
              </motion.div>
            ) : (
              <motion.div className="glass px-6 py-4 rounded-full text-sm font-semibold" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                "Morning run scheduled for 6:30 AM ✅"
              </motion.div>
            )}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="py-24 px-6 bg-white/5">
        <div className="max-w-4xl mx-auto">
          <RevealOnScroll className="text-center mb-16">
            <h2 className="text-4xl font-black mb-4" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>
              Up and running in <span className="text-gradient-peach">3 minutes</span>
            </h2>
          </RevealOnScroll>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { step: '01', title: 'Upload your timetable', desc: 'Drag and drop your class schedule image.', icon: Upload },
              { step: '02', title: 'Review and confirm', desc: 'Check the extracted schedule, edit if needed.', icon: CheckCircle },
              { step: '03', title: 'Let AI plan your day', desc: 'Say what you need done and watch it find a slot.', icon: Brain },
            ].map((item, i) => (
              <RevealOnScroll key={item.step} delay={i * 0.12}>
                <GlassCard className="p-6 h-full flex flex-col items-center justify-center text-center">
                  <div className="w-14 h-14 rounded-full flex items-center justify-center mb-4 font-black" style={{ background: 'var(--peach)', color: 'white' }}>{item.step}</div>
                  <h3 className="font-bold mb-2" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>{item.title}</h3>
                  <p className="text-sm" style={{ color: 'var(--text-2)' }}>{item.desc}</p>
                </GlassCard>
              </RevealOnScroll>
            ))}
          </div>
        </div>
      </section>

      {/* TESTIMONIALS */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <RevealOnScroll className="text-center mb-16">
            <h2 className="text-4xl font-black" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>Loved by students across India</h2>
          </RevealOnScroll>
          <div className="grid md:grid-cols-3 gap-4">
            {TESTIMONIALS.map((t, i) => (
              <RevealOnScroll key={t.name} delay={i * 0.08}>
                <GlassCard className="p-5 h-full">
                  <div className="flex gap-0.5 mb-3">
                    {Array(t.stars).fill(0).map((_, j) => <Star key={j} size={13} fill="#E9C46A" stroke="none" />)}
                  </div>
                  <p className="text-sm leading-relaxed mb-4" style={{ color: 'var(--text-1)' }}>"{t.text}"</p>
                  <div className="flex items-center gap-2.5 mt-auto">
                    <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white" style={{ background: 'linear-gradient(135deg, #F4A261, #E76F51)' }}>
                      {t.name[0]}
                    </div>
                    <div>
                      <p className="text-sm font-semibold" style={{ color: 'var(--text-1)' }}>{t.name}</p>
                      <p className="text-xs" style={{ color: 'var(--text-3)' }}>{t.role}</p>
                    </div>
                  </div>
                </GlassCard>
              </RevealOnScroll>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6">
        <RevealOnScroll>
          <GlassCard className="max-w-2xl mx-auto p-12 text-center !rounded-[40px]">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6" style={{ background: 'linear-gradient(135deg, #F4A261, #E76F51)' }}>
              <Clock size={28} color="white" />
            </div>
            <h2 className="text-4xl font-black mb-4" style={{ fontFamily: 'Inter', color: 'var(--text-1)' }}>Start planning smarter</h2>
            <p className="text-lg mb-8" style={{ color: 'var(--text-2)' }}>No credit card required. Get started in seconds.</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <MagneticButton className="btn-primary" onClick={handleDemoLogin}>Try Demo <ArrowRight size={15} /></MagneticButton>
              <Link to="/register"><MagneticButton className="btn-ghost">Create Free Account</MagneticButton></Link>
            </div>
          </GlassCard>
        </RevealOnScroll>
      </section>
    </div>
  )
}
