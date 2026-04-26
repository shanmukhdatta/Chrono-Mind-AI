import { useEffect, useRef } from 'react'
import { motion, useMotionValue, useSpring } from 'framer-motion'

export default function CustomCursor() {
  const cursorX = useMotionValue(-100)
  const cursorY = useMotionValue(-100)

  const springConfig = { stiffness: 120, damping: 20, mass: 0.5 }
  const ringX = useSpring(cursorX, springConfig)
  const ringY = useSpring(cursorY, springConfig)

  const ringScale = useMotionValue(1)
  const ringScaleSpring = useSpring(ringScale, { stiffness: 300, damping: 25 })
  const ringOpacity = useMotionValue(1)
  const ringWidth = useMotionValue(32)
  const ringHeight = useMotionValue(32)
  const ringRadius = useMotionValue('50%')
  const ringBg = useMotionValue('transparent')
  const ringBorder = useMotionValue('2px solid var(--peach)')

  useEffect(() => {
    if ('ontouchstart' in window) return

    const move = (e) => {
      cursorX.set(e.clientX)
      cursorY.set(e.clientY)
    }

    const handleMouseOver = (e) => {
      const el = e.target
      if (
        el.tagName === 'BUTTON' ||
        el.tagName === 'A' ||
        el.closest('button') ||
        el.closest('a') ||
        el.getAttribute('role') === 'button' ||
        el.classList.contains('interactive')
      ) {
        ringScale.set(1.6)
        ringOpacity.set(1)
        ringWidth.set(32)
        ringHeight.set(32)
        ringRadius.set('50%')
        ringBg.set('rgba(244,162,97,0.20)')
        ringBorder.set('2px solid var(--peach)')
      } else if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        ringScale.set(1)
        ringOpacity.set(0.8)
        ringWidth.set(2)
        ringHeight.set(24)
        ringRadius.set('2px')
        ringBg.set('var(--peach)')
        ringBorder.set('0px solid transparent')
      } else {
        ringScale.set(1)
        ringOpacity.set(1)
        ringWidth.set(32)
        ringHeight.set(32)
        ringRadius.set('50%')
        ringBg.set('transparent')
        ringBorder.set('2px solid var(--peach)')
      }
    }

    window.addEventListener('mousemove', move)
    document.addEventListener('mouseover', handleMouseOver)

    return () => {
      window.removeEventListener('mousemove', move)
      document.removeEventListener('mouseover', handleMouseOver)
    }
  }, [])

  if ('ontouchstart' in window) return null

  return (
    <>
      <motion.div
        className="cursor-dot"
        style={{ left: cursorX, top: cursorY }}
      />
      <motion.div
        className="cursor-ring"
        style={{
          left: ringX,
          top: ringY,
          scale: ringScaleSpring,
          opacity: ringOpacity,
          width: ringWidth,
          height: ringHeight,
          borderRadius: ringRadius,
          background: ringBg,
          border: ringBorder,
        }}
      />
    </>
  )
}
