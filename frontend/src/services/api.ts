import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('finpad_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 (expired token) globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('finpad_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// === Auth API ===
export const authApi = {
  requestOTP: (phone: string) =>
    api.post('/auth/request-otp', { phone }),

  verifyOTP: (phone: string, otp: string) =>
    api.post('/auth/verify-otp', { phone, otp }),

  refreshToken: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),

  getMe: () =>
    api.get('/auth/me'),
}

// === Expenses API ===
export const expensesApi = {
  create: (data: { amount: number; description?: string; category_id?: number; expense_date?: string }) =>
    api.post('/expenses/', data),

  list: (params?: { start_date?: string; end_date?: string; category_id?: number; limit?: number; offset?: number }) =>
    api.get('/expenses/', { params }),

  get: (id: number) =>
    api.get(`/expenses/${id}`),

  summary: (period: 'daily' | 'weekly' | 'monthly' = 'monthly', target_date?: string) =>
    api.get('/expenses/summary', { params: { period, target_date } }),

  update: (id: number, data: Partial<{ amount: number; description: string; category_id: number; expense_date: string }>) =>
    api.put(`/expenses/${id}`, data),

  delete: (id: number) =>
    api.delete(`/expenses/${id}`),

  getCategories: () =>
    api.get('/expenses/categories'),

  // === AI-Powered Features ===
  aiStatus: () =>
    api.get('/expenses/ai/status'),

  aiParse: (text: string) =>
    api.post('/expenses/ai/parse', { text }),

  aiScanReceipt: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/expenses/ai/receipt', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  aiSmartCreate: (data: {
    text?: string
    amount?: number
    description?: string
    category_id?: number
    expense_date?: string
    use_ai?: boolean
  }) => api.post('/expenses/ai/smart', data),
}

// === Categories API ===
export const categoriesApi = {
  list: () =>
    api.get('/categories'),

  create: (data: { name: string; icon?: string; color?: string }) =>
    api.post('/categories', data),
}

// === Education API ===
export const educationApi = {
  getDailyTip: () =>
    api.get('/education/tips'),

  getTipHistory: () =>
    api.get('/education/tips/history'),
}

// === Gamification API ===
export const gamificationApi = {
  getBadges: () =>
    api.get('/gamification/badges'),

  getMyBadges: () =>
    api.get('/gamification/badges/mine'),

  getStats: () =>
    api.get('/gamification/stats'),
}

export default api
