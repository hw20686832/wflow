import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || 'http://localhost:8888/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  response => {
    return response
  },
  error => {
    if (error.response) {
      const { status, data } = error.response
      
      if (status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        ElMessage.error('Session expired. Please login again.')
      } else if (data && data.error) {
        ElMessage.error(data.error)
      } else {
        ElMessage.error('An error occurred. Please try again.')
      }
    } else if (error.request) {
      ElMessage.error('Network error. Please check your connection.')
    } else {
      ElMessage.error('An error occurred. Please try again.')
    }
    
    return Promise.reject(error)
  }
)

export default api
