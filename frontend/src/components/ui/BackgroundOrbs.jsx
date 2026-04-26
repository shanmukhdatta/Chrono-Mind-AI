import { motion, useScroll, useTransform } from 'framer-motion'

export default function BackgroundOrbs() {
  const { scrollY } = useScroll()
  const y1 = useTransform(scrollY, [0, 1000], [0, -100])
  const y2 = useTransform(scrollY, [0, 1000], [0, 60])

  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      <motion.div style={{ y: y1 }}>
        <motion.div
          className="orb"
          style={{
            width: 500, height: 500,
            background: 'radial-gradient(circle, rgba(244,162,97,0.25) 0%, transparent 70%)',
            top: '-100px', left: '-100px',
          }}
          animate={{ x: [0, 40, -20, 0] }}
          transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
        />
      </motion.div>
      <motion.div style={{ y: y2 }}>
        <motion.div
          className="orb"
          style={{
            width: 400, height: 400,
            background: 'radial-gradient(circle, rgba(42,157,143,0.15) 0%, transparent 70%)',
            bottom: '-80px', right: '-60px',
          }}
          animate={{ x: [0, -50, 30, 0] }}
          transition={{ duration: 22, repeat: Infinity, ease: 'easeInOut' }}
        />
      </motion.div>
      <motion.div>
        <motion.div
          className="orb"
          style={{
            width: 300, height: 300,
            background: 'radial-gradient(circle, rgba(233,196,106,0.15) 0%, transparent 70%)',
            top: '40%', right: '20%',
          }}
          animate={{ x: [0, 30, -15, 0], y: [0, -20, 35, 0] }}
          transition={{ duration: 25, repeat: Infinity, ease: 'easeInOut' }}
        />
      </motion.div>
    </div>
  )
}
