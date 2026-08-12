import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import CourseDetailsModal from '../components/CourseDetailsModal'
import { fetchSectionAvailability } from '../services/courseApi'
import type { Course } from '../types/course'

vi.mock('../services/courseApi', () => ({
  fetchSectionAvailability: vi.fn(),
}))

const course: Course = {
  course_id: 'cse-301-a',
  code: 'CSE 301',
  title: 'Database Systems',
  department: 'CSE',
  semester: 'Fall 2026',
  instructor: 'Dr. Hasan',
  credits: 3,
  capacity: 40,
  available_seats: 15,
  is_mandatory: true,
  level: 'Undergraduate',
  description: 'Database design and SQL.',
  prerequisites: ['CSE 201'],
  section: 'A',
  schedule: [
    {
      day: 'Tuesday',
      start_time: '11:00',
      end_time: '12:30',
      room: 'CSE-401',
    },
  ],
}

describe('CourseDetailsModal', () => {
  it('refreshes live seats, exposes all section details, and closes with Escape', async () => {
    vi.mocked(fetchSectionAvailability).mockResolvedValue({
      ...course,
      available_seats: 4,
      enrollment: 36,
      is_full: false,
    })
    const onClose = vi.fn()
    const user = userEvent.setup()

    render(<CourseDetailsModal course={course} onClose={onClose} />)

    expect(screen.getByRole('dialog', { name: 'Database Systems' })).toBeVisible()
    expect(screen.getByText('Dr. Hasan')).toBeVisible()
    expect(screen.getByText('CSE 201')).toBeVisible()
    expect(screen.getByText('CSE-401')).toBeVisible()

    await waitFor(() => {
      expect(screen.getByText(/4 available · 36 enrolled/)).toBeVisible()
      expect(screen.getByText('Live data')).toBeVisible()
    })

    await user.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalledTimes(1)
  })
})
