// Único punto por donde el frontend habla con el backend: agrega el token, convierte los
// errores de la API en ApiError y avisa cuando la sesión expiró.

export interface FieldError { field: string; message: string }

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly fields: FieldError[]

  constructor(status: number, message: string, code = 'error', fields: FieldError[] = []) {
    super(message)
    this.status = status
    this.code = code
    this.fields = fields
  }
}

const TOKEN_KEY = 'vennex.token'
let onUnauthorized: () => void = () => {}

export const tokenStore = {
  // sessionStorage: el token se borra al cerrar la pestaña.
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (token: string) => sessionStorage.setItem(TOKEN_KEY, token),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
}

export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler
}

type Query = Record<string, string | number | undefined | null>

export async function api<T>(path: string, options: { method?: string; body?: unknown; query?: Query } = {}): Promise<T> {
  const params = new URLSearchParams()
  Object.entries(options.query ?? {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') params.set(k, String(v))
  })
  const url = `/api${path}${params.size ? `?${params}` : ''}`
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = tokenStore.get()
  if (token) headers.Authorization = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(url, {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
  } catch {
    throw new ApiError(0, 'No se pudo conectar con el servidor. Revise su conexión.')
  }

  if (response.ok) return (await response.json()) as T

  const data = await response.json().catch(() => ({}))
  if (response.status === 401 && token) onUnauthorized()
  throw new ApiError(response.status, data.detail ?? 'Ocurrió un error inesperado.', data.code, data.fields ?? [])
}
