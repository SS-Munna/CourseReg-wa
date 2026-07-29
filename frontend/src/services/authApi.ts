const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

export type AuthUser = {
  id: number
  name: string
  email: string
  role: string
}

export type AuthResponse = {
  success: boolean
  token: string
  user: AuthUser
}

export type RegisterPayload = {
  name: string
  email: string
  password: string
}

export type LoginPayload = {
  email: string
  password: string
}

async function handleAuthResponse(response: Response): Promise<AuthResponse> {
  const data = await response.json()

  if (!response.ok) {
    const message =
      typeof data.detail === 'string'
        ? data.detail
        : 'Authentication request failed.'

    throw new Error(message)
  }

  return data
}

export async function registerStudent(
  payload: RegisterPayload,
): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  return handleAuthResponse(response)
}

export async function loginStudent(
  payload: LoginPayload,
): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  return handleAuthResponse(response)
}