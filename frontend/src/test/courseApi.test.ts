import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  fetchCourses,
  fetchSectionAvailability,
} from '../services/courseApi'
import type { Course, SectionAvailability } from '../types/course'

const course: Course = {
  course_id: 'cse-401-a',
  code: 'CSE 401',
  title: 'Artificial Intelligence',
  department: 'CSE',
  semester: 'Spring 2027',
  instructor: 'Dr. Sultana',
  credits: 3,
  capacity: 35,
  available_seats: 18,
  is_mandatory: false,
  level: 'Undergraduate',
  section: 'A',
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('course API', () => {
  it('maps every catalogue filter to the backend query contract', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ success: true, data: [course] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await fetchCourses({
      search: '  artificial intelligence  ',
      department: 'CSE',
      semester: 'Spring 2027',
      level: 'Undergraduate',
      availableOnly: true,
      courseType: 'elective',
    })

    const url = new URL(fetchMock.mock.calls[0][0] as string)
    expect(url.pathname).toBe('/api/courses')
    expect(Object.fromEntries(url.searchParams)).toEqual({
      search: 'artificial intelligence',
      department: 'CSE',
      semester: 'Spring 2027',
      level: 'Undergraduate',
      available_only: 'true',
      is_mandatory: 'false',
    })
  })

  it('loads current section availability from the detail endpoint', async () => {
    const availability: SectionAvailability = {
      ...course,
      enrollment: 17,
      is_full: false,
    }
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ success: true, data: availability }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(fetchSectionAvailability('cse/401 a')).resolves.toEqual(
      availability,
    )
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/courses/cse%2F401%20a/availability',
    )
  })
})
