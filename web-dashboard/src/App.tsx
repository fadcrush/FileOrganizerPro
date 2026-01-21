import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'

// Pages
import Dashboard from './pages/Dashboard'
import FilesView from './pages/FilesView'
import OrganizeView from './pages/OrganizeView'
import DuplicatesView from './pages/DuplicatesView'
import AnalyticsView from './pages/AnalyticsView'
import SettingsView from './pages/SettingsView'
import LoginPage from './pages/LoginPage'

// Layout
import MainLayout from './components/layout/MainLayout'

// Store
import { useAuthStore } from './store/authStore'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            path="/"
            element={
              <PrivateRoute>
                <MainLayout />
              </PrivateRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="files" element={<FilesView />} />
            <Route path="organize" element={<OrganizeView />} />
            <Route path="duplicates" element={<DuplicatesView />} />
            <Route path="analytics" element={<AnalyticsView />} />
            <Route path="settings" element={<SettingsView />} />
          </Route>
        </Routes>
      </BrowserRouter>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1a1f3a',
            color: '#fff',
            border: '1px solid rgba(0, 247, 255, 0.3)',
          },
        }}
      />
    </QueryClientProvider>
  )
}

export default App
