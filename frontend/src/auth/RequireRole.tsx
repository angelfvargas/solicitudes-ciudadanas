import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import type { RoleCode } from '../api/types'
import { useAuth } from './AuthContext'

// Oculta pantallas que el rol no usa. Es solo experiencia de usuario: la seguridad real
// está en el backend, que valida el rol y la pertenencia en cada petición.
export function RequireRole({ roles, children }: { roles?: RoleCode[]; children: ReactNode }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <p className="muted center">Cargando…</p>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (roles && !roles.includes(user.role.code)) return <Navigate to="/" replace />
  return <>{children}</>
}
