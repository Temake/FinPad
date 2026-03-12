import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { authApi } from '../services/api'

// Environment-based auth bypass for testing
const BYPASS_AUTH = import.meta.env.VITE_BYPASS_AUTH === 'true'

// Mock user for testing without backend
const MOCK_USER = {
  id: '1',
  phone: '+2348012345678',
  display_name: 'Test User',
  currency: 'NGN',
  notification_enabled: true,
  daily_reminder_time: '20:00',
  whatsapp_linked: true,
  current_streak: 5,
  level: 'Beginner Saver',
}

interface User {
  id: string
  phone: string
  display_name: string | null
  currency: string
  notification_enabled: boolean
  daily_reminder_time: string | null
  whatsapp_linked: boolean
  current_streak: number
  level: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  requestOTP: (phone: string) => Promise<{ message: string; debug_otp?: string }>
  verifyOTP: (phone: string, otp: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  // Initialize with mock data if bypass is enabled
  const [user, setUser] = useState<User | null>(BYPASS_AUTH ? MOCK_USER : null)
  const [token, setToken] = useState<string | null>(() =>
    BYPASS_AUTH ? 'mock-token' : localStorage.getItem('finpad_token')
  )
  const [isLoading, setIsLoading] = useState(BYPASS_AUTH ? false : true)

  const logout = useCallback(() => {
    if (BYPASS_AUTH) return
    setToken(null)
    setUser(null)
    localStorage.removeItem('finpad_token')
    localStorage.removeItem('finpad_refresh_token')
  }, [])

  const refreshUser = useCallback(async () => {
    if (BYPASS_AUTH) return
    try {
      const res = await authApi.getMe()
      setUser(res.data)
    } catch {
      logout()
    }
  }, [logout])

  // On mount: check if token exists and fetch user
  useEffect(() => {
    // Skip initialization if bypassing auth
    if (BYPASS_AUTH) {
      console.log('Auth bypassed - using mock user')
      return
    }

    const init = async () => {
      if (token) {
        try {
          const res = await authApi.getMe()
          setUser(res.data)
        } catch {
          // Token might be expired, try refresh
          const refreshToken = localStorage.getItem('finpad_refresh_token')
          if (refreshToken) {
            try {
              const refreshRes = await authApi.refreshToken(refreshToken)
              const newToken = refreshRes.data.access_token
              setToken(newToken)
              localStorage.setItem('finpad_token', newToken)
              localStorage.setItem('finpad_refresh_token', refreshRes.data.refresh_token)
              const userRes = await authApi.getMe()
              setUser(userRes.data)
            } catch {
              logout()
            }
          } else {
            logout()
          }
        }
      }
      setIsLoading(false)
    }
    init()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const requestOTP = async (phone: string) => {
    if (BYPASS_AUTH) return { message: 'Mock OTP sent', debug_otp: '123456' }
    const res = await authApi.requestOTP(phone)
    return res.data
  }

  const verifyOTP = async (phone: string, otp: string) => {
    if (BYPASS_AUTH) return
    const res = await authApi.verifyOTP(phone, otp)
    const { access_token, refresh_token } = res.data

    setToken(access_token)
    localStorage.setItem('finpad_token', access_token)
    localStorage.setItem('finpad_refresh_token', refresh_token)

    // Fetch user profile
    const userRes = await authApi.getMe()
    setUser(userRes.data)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: BYPASS_AUTH ? true : (!!token && !!user),
        requestOTP,
        verifyOTP,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}