import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? '/api'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT on every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle 401 → logout
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.dispatchEvent(new Event('auth:expired'))
    }
    const detail = err.response?.data?.detail
    return Promise.reject(typeof detail === 'string' ? detail : err.message ?? 'Erro desconhecido')
  }
)

const api = {
  get: <T>(url: string, params?: Record<string, unknown>) =>
    apiClient.get<T>(url, { params }).then((r) => r.data),

  post: <T>(url: string, data?: unknown) =>
    apiClient.post<T>(url, data).then((r) => r.data),

  postForm: <T>(url: string, data: URLSearchParams | string) =>
    apiClient.post<T>(url, data, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }).then((r) => r.data),

  put: <T>(url: string, data?: unknown) =>
    apiClient.put<T>(url, data).then((r) => r.data),

  patch: <T>(url: string, data?: unknown) =>
    apiClient.patch<T>(url, data).then((r) => r.data),

  delete: <T>(url: string) =>
    apiClient.delete<T>(url).then((r) => r.data),

  upload: <T>(url: string, formData: FormData) =>
    apiClient.post<T>(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data),
}

export default api
