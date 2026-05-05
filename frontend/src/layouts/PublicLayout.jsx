import React from 'react'
import { Outlet } from 'react-router-dom'

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-cream">
      <Outlet />
    </div>
  )
}
