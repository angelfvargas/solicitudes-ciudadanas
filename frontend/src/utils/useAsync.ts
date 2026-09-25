import { useCallback, useEffect, useState } from 'react'
import { ApiError } from '../api/client'

// Carga datos de la API manejando los estados de carga y error de forma uniforme.
export function useAsync<T>(loader: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(loader, deps)

  const reload = useCallback(() => {
    setLoading(true)
    setError('')
    load()
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : 'Error inesperado'))
      .finally(() => setLoading(false))
  }, [load])

  useEffect(reload, [reload])
  return { data, error, loading, reload }
}
