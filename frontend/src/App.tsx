import './App.css'

import { AuthProvider, useAuth } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import AppLayout from './layouts/AppLayout'
import AdminDashboardPage from './pages/AdminDashboardPage'
import AdvisorDashboardPage from './pages/AdvisorDashboardPage'
import LoginPage from './pages/LoginPage'
import RoleWorkspacePage from './pages/RoleWorkspacePage'
import StudentDashboardPage from './pages/StudentDashboardPage'

function AppContent() {
  const { isAuthenticated, user } = useAuth()

  if (!isAuthenticated || !user) {
    return <LoginPage />
  }

  let workspace

  if (user.role === 'student') {
    workspace = <StudentDashboardPage />
  } else if (user.role === 'advisor') {
    workspace = <AdvisorDashboardPage />
  } else if (
    user.role === 'department-admin' ||
    user.role === 'system-admin'
  ) {
    workspace = <AdminDashboardPage />
  } else {
    workspace = <RoleWorkspacePage />
  }

  return <AppLayout>{workspace}</AppLayout>
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
