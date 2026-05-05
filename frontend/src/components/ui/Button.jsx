import React from 'react'

export function Button({ children, onClick, variant = 'primary', className = '', disabled = false, type = 'button', ...props }) {
  const base = 'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-peach/40'
  const variants = {
    primary: 'bg-peach text-white hover:bg-peach-dark shadow-peach px-5 py-2.5',
    outline: 'border-2 border-peach text-peach hover:bg-peach hover:text-white px-5 py-2.5',
    ghost: 'text-dark-muted hover:bg-gray-100 hover:text-dark px-3 py-2',
    danger: 'bg-red-500 text-white hover:bg-red-600 px-5 py-2.5',
  }
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${variants[variant] || variants.primary} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
