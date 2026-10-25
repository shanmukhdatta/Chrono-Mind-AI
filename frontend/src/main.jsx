import React, { useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import AppRouter from './router/index.jsx'
import { useAuth } from './hooks/useAuth.js'
import './styles/globals.css'

function AppWithAuth() {
  const { initAuth } = useAuth()
  useEffect(() => {
    const unsubscribe = initAuth()
    return () => unsubscribe && unsubscribe()
  }, [])
  return <AppRouter />
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3500,
          style: {
            background: '#FFFFFF',
            color: '#0F172A',
            border: '1px solid #E2E8F0',
            borderRadius: '10px',
            boxShadow: '0 1px 2px rgba(15,23,42,0.06)',
            fontSize: '14px',
          },
          success: { iconTheme: { primary: '#2563EB', secondary: '#FFFFFF' } },
          error: { iconTheme: { primary: '#ef4444', secondary: '#fff' } },
        }}
      />
      <AppWithAuth />
    </BrowserRouter>
  </React.StrictMode>,
)
