const SIMPLE_EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function isValidEmail(value: string): boolean {
  const normalized = value.trim()
  return normalized.length <= 254 && SIMPLE_EMAIL_PATTERN.test(normalized)
}

export function isTrimmedLengthBetween(
  value: string,
  minimum: number,
  maximum: number,
): boolean {
  const length = value.trim().length
  return length >= minimum && length <= maximum
}

export function parseIntegerInRange(
  value: string,
  minimum: number,
  maximum: number,
): number | null {
  if (!/^\d+$/.test(value.trim())) {
    return null
  }

  const parsed = Number(value)

  if (!Number.isSafeInteger(parsed) || parsed < minimum || parsed > maximum) {
    return null
  }

  return parsed
}
