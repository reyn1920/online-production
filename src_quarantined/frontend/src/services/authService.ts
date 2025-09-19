import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

interface LoginResponse {
  access_token: string
  token_type: string
  user: {
    id: string
    email: string
    username: string
  }
}

interface RegisterResponse {
  access_token: string
  token_type: string
  user: {
    id: string
    email: string
    username: string
  }
}

interface User {
  id: string
  email: string
  username: string
}

export const authService = {
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await api.post('/auth/login', { email, password })
    return response.data
  },

  async register(email: string, username: string, password: string): Promise<RegisterResponse> {
    const response = await api.post('/auth/register', { email, username, password })
    return response.data
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get('/auth/me')
    return response.data
  },

  async refreshToken(): Promise<{ access_token: string }> {
    const response = await api.post('/auth/refresh')
    return response.data
  },
}