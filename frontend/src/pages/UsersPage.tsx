import { useState } from 'react'
import { usersApi } from '../api/services'
import { Alert } from '../components/ui'
import { formatDate } from '../utils/format'
import { useAsync } from '../utils/useAsync'

export function UsersPage() {
  const [role, setRole] = useState('')
  const users = useAsync(() => usersApi.list(role || undefined), [role])

  return (
    <>
      <div className="page-head">
        <h1>Usuarios</h1>
        <select value={role} onChange={(e) => setRole(e.target.value)} aria-label="Filtrar por rol">
          <option value="">Todos los roles</option>
          <option value="citizen">Ciudadanos</option>
          <option value="official">Funcionarios</option>
          <option value="admin">Administradores</option>
        </select>
      </div>
      <Alert>{users.error}</Alert>
      {users.data && (
        <div className="card table-card">
          <table className="table">
            <thead><tr><th>Nombre</th><th>Correo</th><th>Documento</th><th>Rol</th><th>Estado</th><th>Registro</th></tr></thead>
            <tbody>
              {users.data.map((u) => (
                <tr key={u.id}>
                  <td data-label="Nombre">{u.full_name}</td>
                  <td data-label="Correo">{u.email}</td>
                  <td data-label="Documento">{u.document_type} {u.document_masked}</td>
                  <td data-label="Rol">{u.role.name}</td>
                  <td data-label="Estado">{u.is_active ? 'Activo' : 'Inactivo'}</td>
                  <td data-label="Registro">{formatDate(u.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
