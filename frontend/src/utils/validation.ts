// Validaciones del lado del cliente: dan respuesta inmediata al usuario.
// Son las mismas reglas que valida el backend (que no confía en estas).

export type Errors<T> = Partial<Record<keyof T, string>>

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/
const NAME = /^[A-Za-zÁÉÍÓÚáéíóúÑñÜü' -]{2,60}$/

export const rules = {
  required: (v: string) => (v.trim() ? '' : 'Este campo es obligatorio'),
  email: (v: string) => (EMAIL.test(v.trim()) ? '' : 'Correo electrónico inválido'),
  name: (v: string) => (NAME.test(v.trim()) ? '' : 'Solo letras, entre 2 y 60 caracteres'),
  password: (v: string) => {
    if (v.length < 8) return 'Mínimo 8 caracteres'
    if (!/[A-Za-z]/.test(v) || !/\d/.test(v)) return 'Debe tener al menos una letra y un número'
    return ''
  },
  document: (type: string, v: string) => {
    const value = v.trim().toUpperCase()
    if (type === 'CC' || type === 'TI') return /^\d{6,10}$/.test(value) ? '' : 'Entre 6 y 10 dígitos'
    return /^[A-Z0-9]{5,15}$/.test(value) ? '' : 'Entre 5 y 15 letras o números'
  },
  length: (v: string, min: number, max: number) => {
    const n = v.trim().length
    if (n < min) return `Mínimo ${min} caracteres (lleva ${n})`
    if (n > max) return `Máximo ${max} caracteres`
    return ''
  },
}

export function hasErrors<T>(errors: Errors<T>): boolean {
  return Object.values(errors).some(Boolean)
}
