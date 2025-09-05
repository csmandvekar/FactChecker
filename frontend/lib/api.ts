import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// File upload
export const uploadFile = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/public/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

// Analyze file
export const analyzeFile = async (fileId: string, fileType: string) => {
  // For public flow, analysis is started automatically on upload; return status
  return { started: true }
}

// Get file status
export const getFileStatus = async (fileId: string) => {
  const response = await api.get(`/api/upload/status/${fileId}`)
  return response.data
}

// Get report
export const getReport = async (fileId: string) => {
  const response = await api.get(`/api/report/${fileId}`)
  return response.data
}

// List reports
export const listReports = async (params?: {
  skip?: number
  limit?: number
  file_type?: string
  verdict?: string
}) => {
  const response = await api.get('/api/reports', { params })
  return response.data
}

// Download report
export const downloadReport = async (fileId: string, format: string = 'json') => {
  const response = await api.get(`/api/report/${fileId}/download`, {
    params: { format },
    responseType: format === 'json' ? 'json' : 'blob',
  })
  return response.data
}

// Authentication
export const login = async (email: string, password: string) => {
  const formData = new FormData()
  formData.append('username', email)
  formData.append('password', password)

  const response = await api.post('/api/token', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })

  const { access_token } = response.data
  localStorage.setItem('auth_token', access_token)
  return response.data
}

export const register = async (userData: {
  email: string
  username: string
  password: string
  full_name?: string
}) => {
  const response = await api.post('/api/register', userData)
  return response.data
}

export const getCurrentUser = async () => {
  const response = await api.get('/api/me')
  return response.data
}

export const logout = async () => {
  try {
    await api.post('/api/logout')
  } finally {
    localStorage.removeItem('auth_token')
  }
}

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health')
  return response.data
}

// Market Intelligence API
export const getAnnouncements = async (params?: {
  skip?: number
  limit?: number
  status?: string
  company_symbol?: string
}) => {
  const response = await api.get('/api/intelligence/announcements', { params })
  return response.data
}

export const getAnnouncementDetails = async (announcementId: number) => {
  const response = await api.get(`/api/intelligence/announcements/${announcementId}`)
  return response.data
}

export const factCheckContent = async (data: {
  text_content?: string
  file?: File
}) => {
  const formData = new FormData()
  if (data.text_content) {
    formData.append('text_content', data.text_content)
  }
  if (data.file) {
    formData.append('file', data.file)
  }

  const response = await api.post('/api/intelligence/fact-check', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const getCompanies = async (params?: {
  skip?: number
  limit?: number
}) => {
  const response = await api.get('/api/intelligence/companies', { params })
  return response.data
}

export const getIntelligenceStats = async () => {
  const response = await api.get('/api/intelligence/stats')
  return response.data
}

export const analyzeAnnouncement = async (announcementId: number) => {
  const response = await api.post(`/api/intelligence/analyze/${announcementId}`)
  return response.data
}

export default api
