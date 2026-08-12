const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

type ApiErrorPayload = {
  error?: {
    code?: string
    message?: string
    details?: unknown
  }
}

type RequestOptions = {
  token: string
  method?: 'GET' | 'POST' | 'DELETE'
  body?: unknown
  fallbackMessage: string
  fallbackCode: string
}

export class ApiRequestError extends Error {
  code: string
  status: number
  details: unknown

  constructor(
    message: string,
    code: string,
    status: number,
    details: unknown = null,
  ) {
    super(message)
    this.name = 'ApiRequestError'
    this.code = code
    this.status = status
    this.details = details
  }
}

export async function requestJson<ResponseData>(
  path: string,
  {
    token,
    method = 'GET',
    body,
    fallbackMessage,
    fallbackCode,
  }: RequestOptions,
): Promise<ResponseData> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  })

  let payload: ResponseData & ApiErrorPayload

  try {
    payload = (await response.json()) as ResponseData & ApiErrorPayload
  } catch {
    throw new ApiRequestError(
      fallbackMessage,
      fallbackCode,
      response.status,
    )
  }

  if (!response.ok) {
    throw new ApiRequestError(
      payload.error?.message || fallbackMessage,
      payload.error?.code || fallbackCode,
      response.status,
      payload.error?.details,
    )
  }

  return payload
}
