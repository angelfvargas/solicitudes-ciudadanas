import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError } from '../api/client'
import { authApi } from '../api/services'
import type { RegisterData } from '../api/types'
import { Alert, Field } from '../components/ui'
import { hasErrors, rules, type Errors } from '../utils/validation'

type Form = RegisterData & { confirm: string }

const DOCUMENT_TYPES = [
  ['CC', 'Cédula de ciudadanía'], ['CE', 'Cédula de extranjería'], ['TI', 'Tarjeta de identidad'], ['PA', 'Pasaporte'],
]

function validate(f: Form): Errors<Form> {
  return {
    first_name: rules.name(f.first_name),
    last_name: rules.name(f.last_name),
    document_number: rules.document(f.document_type, f.document_number),
    email: rules.required(f.email) || rules.email(f.email),
    password: rules.password(f.password),
    confirm: f.confirm === f.password ? '' : 'Las contraseñas no coinciden',
  }
}

export function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState<Form>({
    first_name: '', last_name: '', document_type: 'CC', document_number: '', email: '', password: '', confirm: '',
  })
  const [errors, setErrors] = useState<Errors<Form>>({})
  const [serverError, setServerError] = useState('')
  const [sending, setSending] = useState(false)

  const set = (key: keyof Form) => (e: { target: { value: string } }) => {
    setForm({ ...form, [key]: e.target.value })
    if (errors[key]) setErrors({ ...errors, [key]: '' }) // el error se quita al corregir
  }

  async function submit(e: FormEvent) {
    e.preventDefault()
    const found = validate(form)
    setErrors(found)
    if (hasErrors(found)) return
    setSending(true)
    setServerError('')
    try {
      const { confirm: _confirm, ...data } = form
      await authApi.register(data)
      navigate('/login', { state: { registered: true } })
    } catch (err) {
      if (err instanceof ApiError) {
        setServerError(err.message)
        // errores por campo que devuelve el backend (validación del servidor)
        setErrors(Object.fromEntries(err.fields.map((f) => [f.field, f.message])) as Errors<Form>)
      } else setServerError('Error inesperado')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="card auth-card wide" onSubmit={submit} noValidate>
        <h1>Crear cuenta</h1>
        <p className="muted">Registro para ciudadanos</p>
        <Alert>{serverError}</Alert>
        <div className="grid-2">
          <Field label="Nombre" error={errors.first_name}><input value={form.first_name} onChange={set('first_name')} autoComplete="given-name" /></Field>
          <Field label="Apellido" error={errors.last_name}><input value={form.last_name} onChange={set('last_name')} autoComplete="family-name" /></Field>
          <Field label="Tipo de documento">
            <select value={form.document_type} onChange={set('document_type')}>
              {DOCUMENT_TYPES.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
            </select>
          </Field>
          <Field label="Número de documento" error={errors.document_number}><input value={form.document_number} onChange={set('document_number')} /></Field>
        </div>
        <Field label="Correo electrónico" error={errors.email}><input type="email" value={form.email} onChange={set('email')} autoComplete="email" /></Field>
        <div className="grid-2">
          <Field label="Contraseña" error={errors.password} hint="Mínimo 8 caracteres, con letras y números">
            <input type="password" value={form.password} onChange={set('password')} autoComplete="new-password" />
          </Field>
          <Field label="Confirmar contraseña" error={errors.confirm}>
            <input type="password" value={form.confirm} onChange={set('confirm')} autoComplete="new-password" />
          </Field>
        </div>
        <button className="btn btn-primary btn-block" disabled={sending}>{sending ? 'Creando…' : 'Crear cuenta'}</button>
        <p className="center">¿Ya tiene cuenta? <Link to="/login">Inicie sesión</Link></p>
      </form>
    </div>
  )
}
