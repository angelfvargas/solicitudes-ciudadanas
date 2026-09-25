import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export function Layout() {
  const { user, logout, hasRole } = useAuth()
  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar-inner">
          <span className="brand">Solicitudes Ciudadanas</span>
          <nav className="nav">
            <NavLink to="/" end>Inicio</NavLink>
            <NavLink to="/solicitudes" end>{hasRole('citizen') ? 'Mis solicitudes' : hasRole('official') ? 'Asignadas' : 'Solicitudes'}</NavLink>
            {hasRole('citizen') && <NavLink to="/solicitudes/nueva">Nueva solicitud</NavLink>}
            {hasRole('admin') && <NavLink to="/usuarios">Usuarios</NavLink>}
          </nav>
          <div className="user-box">
            <span className="user-name">{user?.full_name} <small className="muted">· {user?.role.name}</small></span>
            <button className="btn btn-ghost btn-sm" onClick={logout}>Salir</button>
          </div>
        </div>
      </header>
      <main className="container">
        <Outlet />
      </main>
    </div>
  )
}
