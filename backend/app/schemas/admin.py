from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.schemas.common import PaginatedResponse, SuccessResponse


AdminAccountStatus = Literal["pending", "active", "suspended", "rejected"]
ProvisionableStaffRole = Literal["advisor", "department-admin"]


class AdminUserData(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    account_status: str
    profile_status: Literal["linked", "missing", "not-required"]
    created_at: datetime


class AdminOverviewData(BaseModel):
    total_users: int = Field(..., ge=0)
    active_students: int = Field(..., ge=0)
    active_advisors: int = Field(..., ge=0)
    pending_staff: int = Field(..., ge=0)
    suspended_accounts: int = Field(..., ge=0)
    department_admins: int = Field(..., ge=0)
    unlinked_students: int = Field(..., ge=0)


class AdminOverviewResponse(SuccessResponse[AdminOverviewData]):
    pass


class AdminUserListResponse(PaginatedResponse[AdminUserData]):
    pass


class DepartmentData(BaseModel):
    id: UUID
    code: str
    name: str


class DepartmentListResponse(SuccessResponse[list[DepartmentData]]):
    pass


class CreateDepartmentRequest(BaseModel):
    code: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=2, max_length=255)


class DepartmentResponse(SuccessResponse[DepartmentData]):
    pass


class ProgramData(BaseModel):
    id: UUID
    department_id: UUID
    department_code: str
    code: str
    name: str
    minimum_credit: int
    maximum_credit: int


class ProgramListResponse(SuccessResponse[list[ProgramData]]):
    pass


class CreateProgramRequest(BaseModel):
    department_id: UUID
    code: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=2, max_length=255)
    minimum_credit: int = Field(..., ge=0, le=60)
    maximum_credit: int = Field(..., ge=0, le=60)

    @model_validator(mode="after")
    def validate_credit_range(self):
        if self.maximum_credit < self.minimum_credit:
            raise ValueError(
                "maximum_credit must be greater than or equal to minimum_credit"
            )
        return self


class ProgramResponse(SuccessResponse[ProgramData]):
    pass


class AdvisorOptionData(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    email: str
    employee_number: str
    department_id: UUID
    department_code: str


class AdvisorOptionListResponse(SuccessResponse[list[AdvisorOptionData]]):
    pass


class CreateStudentProfileRequest(BaseModel):
    program_id: UUID
    advisor_id: UUID
    student_number: str = Field(..., min_length=2, max_length=64)
    current_trimester: int = Field(..., ge=1, le=30)


class StudentProfileData(BaseModel):
    student_id: UUID
    user_id: UUID
    student_number: str
    program_id: UUID
    advisor_id: UUID
    current_trimester: int
    academic_status: str


class StudentProfileResponse(SuccessResponse[StudentProfileData]):
    pass


class CreateStaffAccountRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: ProvisionableStaffRole
    account_status: Literal["pending", "active"] = "active"
    department_id: UUID | None = None
    employee_number: str | None = Field(
        default=None,
        min_length=2,
        max_length=64,
    )

    @model_validator(mode="after")
    def validate_advisor_profile(self):
        if self.role == "advisor":
            if self.department_id is None:
                raise ValueError(
                    "department_id is required for advisor accounts"
                )
            if not self.employee_number or not self.employee_number.strip():
                raise ValueError(
                    "employee_number is required for advisor accounts"
                )

        return self


class AdminUserResponse(SuccessResponse[AdminUserData]):
    pass


class UpdateAccountAccessRequest(BaseModel):
    account_status: AdminAccountStatus
