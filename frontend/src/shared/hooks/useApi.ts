import { useState, useCallback, useEffect } from 'react'

interface UseApiOptions<T> {
  immediate?: boolean
  initialData?: T
}

interface UseApiState<T> {
  data: T | undefined
  loading: boolean
  error: string | null
  refetch: () => void
}

/**
 * Generic hook for fetching data from the API.
 * Usage: const { data, loading, error } = useApi(() => api.get('/api/boats'))
 */
export function useApi<T>(
  fetcher: () => Promise<T>,
  options: UseApiOptions<T> = {}
): UseApiState<T> {
  const { immediate = true, initialData } = options
  const [data, setData] = useState<T | undefined>(initialData)
  const [loading, setLoading] = useState(immediate)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetcher()
      setData(result)
    } catch (err: unknown) {
      setError(typeof err === 'string' ? err : 'Erro ao carregar dados')
    } finally {
      setLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (immediate) fetch()
  }, [fetch, immediate])

  return { data, loading, error, refetch: fetch }
}
