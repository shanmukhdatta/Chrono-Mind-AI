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
            background: '#FDFAF7',
            color: '#1A1A2E',
            border: '1px solid rgba(232, 168, 124, 0.3)',
            borderRadius: '16px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
            fontSize: '14px',
          },
          success: { iconTheme: { primary: '#E8A87C', secondary: '#FDFAF7' } },
          error: { iconTheme: { primary: '#ef4444', secondary: '#fff' } },
        }}
      />
      <AppWithAuth />
    </BrowserRouter>
  </React.StrictMode>,
)
