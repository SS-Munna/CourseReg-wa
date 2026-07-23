import './App.css'

import { ThemeProvider } from './context/ThemeContext'
import AppLayout from './layouts/AppLayout'
import CourseCatalogPage from './pages/CourseCatalogPage'

function App() {
  return (
    <ThemeProvider>
      <AppLayout>
        <CourseCatalogPage />
      </AppLayout>
    </ThemeProvider>
  )
}

export default App