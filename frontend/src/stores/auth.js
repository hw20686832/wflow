import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  
  const login = async (username, password) => {
    try {
      const response = await api.post('/auth/login', { username, password })
      token.value = response.data.token
      user.value = response.data.user
      localStorage.setItem('token', token.value)
      localStorage.setItem('user', JSON.stringify(user.value))
      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    }
  }
  
  const register = async (username, password, email) => {
    try {
      const response = await api.post('/auth/register', { username, password, email })
      return true
    } catch (error) {
      console.error('Registration failed:', error)
      return false
    }
  }
  
  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      token.value = ''
      user.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
  
  const checkAuth = async () => {
    if (!token.value) {
      return false
    }
    
    try {
      const response = await api.get('/user')
      user.value = response.data.user
      localStorage.setItem('user', JSON.stringify(user.value))
      return true
    } catch (error) {
      console.error('Auth check failed:', error)
      token.value = ''
      user.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      return false
    }
  }
  
  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    logout,
    checkAuth
  }
})
