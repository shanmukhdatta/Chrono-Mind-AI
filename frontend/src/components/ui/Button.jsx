import React from 'react'

export function Button({ children, onClick, variant = 'primary', className = '', disabled = false, type = 'button', ...props }) {
  const base = 'inline-flex min-h-10 items-center justify-center rounded-lg px-5 py-2 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-peach'
  const variants = {
    primary: 'bg-peach text-white hover:bg-peach-dark',
    outline: 'border border-slate-300 bg-white text-dark hover:bg-slate-50',
    ghost: 'text-dark-muted hover:bg-slate-100 hover:text-dark',
    danger: 'bg-red-600 text-white hover:bg-red-700',
  }
  return <button type={type} onClick={onClick} disabled={disabled} className={base + ' ' + (variants[variant] || variants.primary) + ' ' + className} {...props}>{children}</button>
}
