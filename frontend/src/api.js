import axios from 'axios'

const apiBaseUrl = import.meta.env.VITE_API_URL || 'https://app-scrapper-acy0.onrender.com'
const api = axios.create({ baseURL: apiBaseUrl })
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
api.interceptors.response.use((response) => response, async (error) => {
  if (error.response?.status === 401 && localStorage.getItem('refresh')) {
    try {
      const { data } = await axios.post(`${apiBaseUrl}/api/auth/refresh/`, { refresh: localStorage.getItem('refresh') })
      localStorage.setItem('access', data.access)
      error.config.headers.Authorization = `Bearer ${data.access}`
      return api(error.config)
    } catch { localStorage.clear() }
  }
  return Promise.reject(error)
})
export default api
