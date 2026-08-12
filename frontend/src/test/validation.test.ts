import { describe, expect, it } from 'vitest'

import {
  isTrimmedLengthBetween,
  isValidEmail,
  parseIntegerInRange,
} from '../utils/validation'

describe('frontend validation helpers', () => {
  it('accepts ordinary email addresses and rejects malformed values', () => {
    expect(isValidEmail(' student@example.com ')).toBe(true)
    expect(isValidEmail('student.example.com')).toBe(false)
    expect(isValidEmail('student@')).toBe(false)
    expect(isValidEmail('student @example.com')).toBe(false)
  })

  it('validates trimmed text boundaries', () => {
    expect(isTrimmedLengthBetween('  CSE  ', 2, 32)).toBe(true)
    expect(isTrimmedLengthBetween(' A ', 2, 32)).toBe(false)
    expect(isTrimmedLengthBetween('ABCDE', 2, 4)).toBe(false)
  })

  it('parses only whole numbers inside the requested range', () => {
    expect(parseIntegerInRange('30', 1, 30)).toBe(30)
    expect(parseIntegerInRange('0', 1, 30)).toBeNull()
    expect(parseIntegerInRange('31', 1, 30)).toBeNull()
    expect(parseIntegerInRange('2.5', 1, 30)).toBeNull()
    expect(parseIntegerInRange('abc', 1, 30)).toBeNull()
  })
})
