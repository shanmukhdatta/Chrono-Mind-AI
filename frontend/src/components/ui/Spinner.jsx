import React from 'react'

export function Spinner({ size = 'md', className = '' }) {
  const sizes = { sm: 'h-4 w-4 border-2', md: 'h-8 w-8 border-2', lg: 'h-12 w-12 border-[3px]' }
  return (
    <div className={`${sizes[size]} animate-spin rounded-full border-peach border-t-transparent ${className}`} />
  )
}
