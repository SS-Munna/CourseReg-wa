import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import type { ReactNode } from 'react'

import {
  loginStudent,
  registerStudent,
} from '../services/authApi'
import type {
  AuthUser,
  LoginPayload,
  RegisterPayload,
} from '../services/authApi'

type AuthContextValue = {
  user: AuthUser | null
  token: string | null
  isAuthenticated: boolean
  login: (payload: LoginPayload) => Promise<void>
  register: (payload: RegisterPayload) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const USER_STORAGE_KEY = 'coursepilot_user'
const TOKEN_STORAGE_KEY = 'coursepilot_token'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    const savedUser = localStorage.getItem(USER_STORAGE_KEY)
    const savedToken = localStorage.getItem(TOKEN_STORAGE_KEY)

    if (savedUser && savedToken) {
      setUser(JSON.parse(savedUser))
      setToken(savedToken)
    }
  }, [])

  const saveSession = (nextUser: AuthUser, nextToken: string) => {
    setUser(nextUser)
    setToken(nextToken)

    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(nextUser))
    localStorage.setItem(TOKEN_STORAGE_KEY, nextToken)
  }

  const login = async (payload: LoginPayload) => {
    const response = await loginStudent(payload)
    saveSession(response.user, response.token)
  }

  const register = async (payload: RegisterPayload) => {
    const response = await registerStudent(payload)
    saveSession(response.user, response.token)
  }

  const logout = () => {
    setUser(null)
    setToken(null)

    localStorage.removeItem(USER_STORAGE_KEY)
    localStorage.removeItem(TOKEN_STORAGE_KEY)
  }

  const value = useMemo(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(user && token),
      login,
      register,
      logout,
    }),
    [user, token],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used inside AuthProvider')
  }

  return context
}