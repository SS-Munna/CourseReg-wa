import './App.css'

import { AuthProvider, useAuth } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import AppLayout from './layouts/AppLayout'
import LoginPage from './pages/LoginPage'
import CourseCatalogPage from './pages/CourseCatalogPage'

function AppContent() {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return (
    <AppLayout>
      <CourseCatalogPage />
    </AppLayout>
  )
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