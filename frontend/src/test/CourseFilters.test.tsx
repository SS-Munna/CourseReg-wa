import { useState } from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import CourseFilters from '../components/CourseFilters'
import type { CourseFilters as CourseFilterValues } from '../types/course'

function FilterHarness({ onApply }: { onApply: () => void }) {
  const [filters, setFilters] = useState<CourseFilterValues>({
    courseType: 'all',
  })

  return (
    <CourseFilters
      filters={filters}
      departments={['CSE', 'EEE']}
      semesters={['Fall 2026', 'Spring 2027']}
      levels={['Graduate', 'Undergraduate']}
      onFiltersChange={setFilters}
      onApplyFilters={onApply}
      onClearFilters={() => setFilters({ courseType: 'all' })}
    />
  )
}

describe('CourseFilters', () => {
  it('supports level, elective, availability, search, and Enter submission', async () => {
    const user = userEvent.setup()
    const onApply = vi.fn()
    render(<FilterHarness onApply={onApply} />)

    await user.type(screen.getByLabelText('Search'), 'database')
    await user.selectOptions(screen.getByLabelText('Department'), 'CSE')
    await user.selectOptions(screen.getByLabelText('Level'), 'Graduate')
    await user.selectOptions(screen.getByLabelText('Course type'), 'elective')
    await user.click(screen.getByLabelText('Available only'))
    await user.keyboard('{Enter}')

    expect(screen.getByLabelText('Search')).toHaveValue('database')
    expect(screen.getByLabelText('Department')).toHaveValue('CSE')
    expect(screen.getByLabelText('Level')).toHaveValue('Graduate')
    expect(screen.getByLabelText('Course type')).toHaveValue('elective')
    expect(screen.getByLabelText('Available only')).toBeChecked()
    expect(onApply).toHaveBeenCalledTimes(1)
  })
})
