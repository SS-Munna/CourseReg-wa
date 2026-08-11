from app.models.advisor import Advisor
from app.models.audit_log import AuditLog
from app.models.completed_course import CompletedCourse, CompletionStatus
from app.models.course import Course
from app.models.course_prerequisite import CoursePrerequisite
from app.models.department import Department
from app.models.instructor import Instructor
from app.models.notification import Notification
from app.models.program import Program
from app.models.registration import Registration, RegistrationStatus
from app.models.semester import Semester
from app.models.student import Student
from app.models.user import User
from app.models.waitlist_entry import WaitlistEntry, WaitlistStatus


__all__ = [
    "Advisor",
    "AuditLog",
    "CompletedCourse",
    "CompletionStatus",
    "Course",
    "CoursePrerequisite",
    "Department",
    "Instructor",
    "Notification",
    "Program",
    "Registration",
    "RegistrationStatus",
    "Semester",
    "Student",
    "User",
    "WaitlistEntry",
    "WaitlistStatus",
]
