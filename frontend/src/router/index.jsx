import React, { Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { AppShell } from '../layouts/AppShell'
import { Spinner } from '../components/ui/Spinner'

const Landing   = lazy(() => import('../pages/Landing'))
const Dashboard = lazy(() => import('../pages/Dashboard'))
const Calendar  = lazy(() => import('../pages/Calendar'))
const Assistant = lazy(() => import('../pages/Assistant'))
const RecurrenceV2 = lazy(() => import('../pages/RecurrenceV2'))
const NotificationsV2 = lazy(() => import('../pages/NotificationsV2'))
const FocusV2 = lazy(() => import('../pages/FocusV2'))
const DashboardV2 = lazy(() => import('../pages/DashboardV2'))
const TasksV2 = lazy(() => import('../pages/TasksV2'))
const AssistantV2 = lazy(() => import('../pages/AssistantV2'))
const CalendarV2 = lazy(() => import('../pages/CalendarV2'))
const ApprovalCenter = lazy(() => import('../pages/ApprovalCenter'))
const PlanPreview = lazy(() => import('../pages/PlanPreview'))
const PlanningSettings = lazy(() => import('../pages/PlanningSettings'))
const Goals     = lazy(() => import('../pages/Goals'))
const Profile   = lazy(() => import('../pages/Profile'))

function PageLoader() {
  return (
    <div className="min-h-screen bg-cream flex items-center justify-center">
      <div className="text-center">
        <Spinner size="lg" />
        <p className="text-dark-muted text-sm mt-4">Loading ChronoMind...</p>
      </div>
    </div>
  )
}

function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuthStore()
  if (isLoading) return <PageLoader />
  if (!isAuthenticated) return <Navigate to="/" replace />
  return children
}

function PublicRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuthStore()
  if (isLoading) return <PageLoader />
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return children
}

export default function AppRouter() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/" element={<PublicRoute><Landing /></PublicRoute>} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <AppShell><Dashboard /></AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/calendar"
          element={
            <ProtectedRoute>
              <AppShell><Calendar /></AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/assistant"
          element={
            <ProtectedRoute>
              <AppShell><Assistant /></AppShell>
            </ProtectedRoute>
          }
        />
        <Route
          path="/goals"
          element={<ProtectedRoute><AppShell><Goals /></AppShell></ProtectedRoute>}
        />
        <Route
          path="/planning"
          element={<ProtectedRoute><AppShell><PlanPreview /></AppShell></ProtectedRoute>}
        />
        <Route
          path="/recurrence-v2"
          element={<ProtectedRoute><AppShell><RecurrenceV2 /></AppShell></ProtectedRoute>}
        />
        <Route
          path="/notifications-v2"
          element={<ProtectedRoute><AppShell><NotificationsV2 /></AppShell></ProtectedRoute>}
        />
        <Route
          path="/focus-v2"
          element={<ProtectedRoute><AppShell><FocusV2 /></AppShell></ProtectedRoute>}
        />
        <Route
          path="/dashboard-v2"
          element={<ProtectedRoute><AppShell><DashboardV2 /></AppShell></ProtectedRoute>}
        />
        <Route
          path="/tasks-v2"
          element={<ProtectedRoute><AppShell><TasksV2 /></AppShell></ProtectedRoute>}
        />
        <Route
          path="/assistant-v2"
          element={<ProtectedRoute><AppShell><AssistantV2 /></AppShell></ProtectedRoute>}
        />
        <Route
          path="/calendar-v2"
          element={<ProtectedRoute><AppShell><CalendarV2 /></AppShell></ProtectedRoute>}
        />
        <Route
          path="/approvals"
          element={<ProtectedRoute><AppShell><ApprovalCenter /></AppShell></ProtectedRoute>}
        />
        <Route
          path="/preferences"
          element={<ProtectedRoute><AppShell><PlanningSettings /></AppShell></ProtectedRoute>}
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <AppShell><Profile /></AppShell>
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}
