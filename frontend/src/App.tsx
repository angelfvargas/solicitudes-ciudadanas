import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import { RequireRole } from './auth/RequireRole'
import { Layout } from './components/Layout'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'
import { NewRequestPage } from './pages/NewRequestPage'
import { RegisterPage } from './pages/RegisterPage'
import { RequestDetailPage } from './pages/RequestDetailPage'
import { RequestListPage } from './pages/RequestListPage'
import { UsersPage } from './pages/UsersPage'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/registro" element={<RegisterPage />} />
          <Route element={<RequireRole><Layout /></RequireRole>}>
            <Route index element={<DashboardPage />} />
            <Route path="solicitudes" element={<RequestListPage />} />
            <Route path="solicitudes/nueva" element={<RequireRole roles={['citizen']}><NewRequestPage /></RequireRole>} />
            <Route path="solicitudes/:id" element={<RequestDetailPage />} />
            <Route path="usuarios" element={<RequireRole roles={['admin']}><UsersPage /></RequireRole>} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
