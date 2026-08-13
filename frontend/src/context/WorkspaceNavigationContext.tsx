import { createContext, useContext } from 'react'
import type { Dispatch, ReactNode, SetStateAction } from 'react'

export type WorkspaceSection =
  | 'all'
  | 'student-overview'
  | 'student-courses'
  | 'student-selection'
  | 'student-status'
  | 'student-waitlist'
  | 'student-timetable'
  | 'advisor-overview'
  | 'advisor-reviews'
  | 'admin-overview'
  | 'admin-users'
  | 'admin-staff'
  | 'admin-students'
  | 'admin-academic'
  | 'admin-audit'

export type WorkspaceNavigationValue = {
  activeSection: WorkspaceSection
  setActiveSection: Dispatch<SetStateAction<WorkspaceSection>>
}

const WorkspaceNavigationContext = createContext<WorkspaceNavigationValue>({
  activeSection: 'all',
  setActiveSection: () => undefined,
})

export function WorkspaceNavigationProvider({
  value,
  children,
}: {
  value: WorkspaceNavigationValue
  children: ReactNode
}) {
  return (
    <WorkspaceNavigationContext.Provider value={value}>
      {children}
    </WorkspaceNavigationContext.Provider>
  )
}

export function useWorkspaceNavigation() {
  return useContext(WorkspaceNavigationContext)
}

export function sectionIsVisible(
  activeSection: WorkspaceSection,
  section: WorkspaceSection,
) {
  return activeSection === 'all' || activeSection === section
}
