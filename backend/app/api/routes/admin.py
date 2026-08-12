from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.errors import (
    REQUEST_VALIDATION_ERROR_RESPONSE,
    STANDARD_ERROR_RESPONSE,
)
from app.authorization import UserRole, require_roles
from app.database import get_db
from app.models.advisor import Advisor
from app.models.department import Department
from app.models.program import Program
from app.models.student import Student
from app.models.user import User
from app.repositories.user_repository import find_user_by_email
from app.schemas.admin import (
    AdminOverviewData,
    AdminOverviewResponse,
    AdminUserData,
    AdminUserListResponse,
    AdminUserResponse,
    AdvisorOptionData,
    AdvisorOptionListResponse,
    CreateDepartmentRequest,
    CreateProgramRequest,
    CreateStaffAccountRequest,
    CreateStudentProfileRequest,
    DepartmentData,
    DepartmentListResponse,
    DepartmentResponse,
    ProgramData,
    ProgramListResponse,
    ProgramResponse,
    StudentProfileData,
    StudentProfileResponse,
    UpdateAccountAccessRequest,
)
from app.schemas.common import PaginationMeta
from app.security import hash_password


router = APIRouter(
    prefix="/api/admin",
    tags=["Department Administration"],
)

require_admin = require_roles(
    UserRole.DEPARTMENT_ADMIN,
    UserRole.SYSTEM_ADMIN,
)

VISIBLE_TO_DEPARTMENT_ADMIN = (
    UserRole.STUDENT.value,
    UserRole.ADVISOR.value,
)


def _user_data(user: User) -> AdminUserData:
    if user.role == UserRole.STUDENT.value:
        profile_status = "linked" if user.student is not None else "missing"
    elif user.role == UserRole.ADVISOR.value:
        profile_status = "linked" if user.advisor is not None else "missing"
    else:
        profile_status = "not-required"

    return AdminUserData(
        id=user.id,
        name=user.full_name,
        email=user.email,
        role=user.role,
        account_status=user.account_status,
        profile_status=profile_status,
        created_at=user.created_at,
    )


def _forbidden(
    message: str,
    *,
    code: str = "ADMIN_ACTION_NOT_ALLOWED",
) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": code,
            "message": message,
        },
    )


def _target_or_404(db: Session, user_id: UUID) -> User:
    target = db.get(User, user_id)

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ADMIN_USER_NOT_FOUND",
                "message": "The requested user account was not found.",
            },
        )

    return target


def _ensure_can_manage(
    actor: User,
    target: User,
) -> None:
    if actor.id == target.id:
        raise _forbidden(
            "You cannot change the access state of your own account.",
            code="SELF_ACCESS_CHANGE_NOT_ALLOWED",
        )

    if actor.role == UserRole.DEPARTMENT_ADMIN.value:
        if target.role != UserRole.ADVISOR.value:
            raise _forbidden(
                "Department administrators can manage advisor access only."
            )
        return

    if target.role == UserRole.SYSTEM_ADMIN.value:
        raise _forbidden(
            "System administrator accounts cannot be changed here."
        )


@router.get(
    "/overview",
    response_model=AdminOverviewResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
    },
)
def get_admin_overview(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)

    if current_user.role == UserRole.DEPARTMENT_ADMIN.value:
        query = query.filter(User.role.in_(VISIBLE_TO_DEPARTMENT_ADMIN))

    users = query.all()

    return AdminOverviewResponse(
        data=AdminOverviewData(
            total_users=len(users),
            active_students=sum(
                user.role == UserRole.STUDENT.value
                and user.account_status == "active"
                for user in users
            ),
            active_advisors=sum(
                user.role == UserRole.ADVISOR.value
                and user.account_status == "active"
                for user in users
            ),
            pending_staff=sum(
                user.role
                in {
                    UserRole.ADVISOR.value,
                    UserRole.DEPARTMENT_ADMIN.value,
                }
                and user.account_status == "pending"
                for user in users
            ),
            suspended_accounts=sum(
                user.account_status == "suspended"
                for user in users
            ),
            department_admins=sum(
                user.role == UserRole.DEPARTMENT_ADMIN.value
                and user.account_status == "active"
                for user in users
            ),
            unlinked_students=sum(
                user.role == UserRole.STUDENT.value
                and user.student is None
                for user in users
            ),
        )
    )


@router.get(
    "/users",
    response_model=AdminUserListResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: (
            REQUEST_VALIDATION_ERROR_RESPONSE
        ),
    },
)
def list_admin_users(
    role: str | None = Query(default=None, max_length=50),
    account_status: str | None = Query(
        default=None,
        alias="status",
        max_length=50,
    ),
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)

    if current_user.role == UserRole.DEPARTMENT_ADMIN.value:
        query = query.filter(User.role.in_(VISIBLE_TO_DEPARTMENT_ADMIN))

    if role:
        query = query.filter(User.role == role)

    if account_status:
        query = query.filter(User.account_status == account_status)

    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                User.full_name.ilike(pattern),
                User.email.ilike(pattern),
            )
        )

    total_items = query.count()
    users = (
        query.order_by(User.created_at.desc(), User.email.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AdminUserListResponse(
        data=[_user_data(user) for user in users],
        pagination=PaginationMeta.from_total(
            page=page,
            page_size=page_size,
            total_items=total_items,
        ),
    )


@router.get(
    "/departments",
    response_model=DepartmentListResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
    },
)
def list_departments(
    _current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    departments = (
        db.query(Department)
        .order_by(Department.department_code.asc())
        .all()
    )

    return DepartmentListResponse(
        data=[
            DepartmentData(
                id=department.id,
                code=department.department_code,
                name=department.department_name,
            )
            for department in departments
        ]
    )


@router.post(
    "/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_409_CONFLICT: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: (
            REQUEST_VALIDATION_ERROR_RESPONSE
        ),
    },
)
def create_department(
    payload: CreateDepartmentRequest,
    _current_user: User = Depends(
        require_roles(UserRole.SYSTEM_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    code = payload.code.strip().upper()
    existing = (
        db.query(Department)
        .filter(func.lower(Department.department_code) == code.lower())
        .first()
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "DEPARTMENT_CODE_ALREADY_EXISTS",
                "message": "A department already uses this code.",
            },
        )

    department = Department(
        department_code=code,
        department_name=payload.name.strip(),
    )
    db.add(department)
    db.commit()
    db.refresh(department)

    return DepartmentResponse(
        data=DepartmentData(
            id=department.id,
            code=department.department_code,
            name=department.department_name,
        )
    )


@router.get(
    "/programs",
    response_model=ProgramListResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
    },
)
def list_programs(
    _current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    programs = (
        db.query(Program)
        .join(Department)
        .order_by(
            Department.department_code.asc(),
            Program.program_code.asc(),
        )
        .all()
    )

    return ProgramListResponse(
        data=[
            ProgramData(
                id=program.id,
                department_id=program.department_id,
                department_code=program.department.department_code,
                code=program.program_code,
                name=program.program_name,
                minimum_credit=program.minimum_credit,
                maximum_credit=program.maximum_credit,
            )
            for program in programs
        ]
    )


@router.post(
    "/programs",
    response_model=ProgramResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_409_CONFLICT: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: (
            REQUEST_VALIDATION_ERROR_RESPONSE
        ),
    },
)
def create_program(
    payload: CreateProgramRequest,
    _current_user: User = Depends(
        require_roles(UserRole.SYSTEM_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    department = db.get(Department, payload.department_id)

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DEPARTMENT_NOT_FOUND",
                "message": "The selected department was not found.",
            },
        )

    code = payload.code.strip().upper()
    existing = (
        db.query(Program)
        .filter(func.lower(Program.program_code) == code.lower())
        .first()
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "PROGRAM_CODE_ALREADY_EXISTS",
                "message": "A program already uses this code.",
            },
        )

    program = Program(
        department=department,
        program_code=code,
        program_name=payload.name.strip(),
        minimum_credit=payload.minimum_credit,
        maximum_credit=payload.maximum_credit,
    )
    db.add(program)
    db.commit()
    db.refresh(program)

    return ProgramResponse(
        data=ProgramData(
            id=program.id,
            department_id=program.department_id,
            department_code=department.department_code,
            code=program.program_code,
            name=program.program_name,
            minimum_credit=program.minimum_credit,
            maximum_credit=program.maximum_credit,
        )
    )


@router.get(
    "/advisors",
    response_model=AdvisorOptionListResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
    },
)
def list_advisor_options(
    _current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    advisors = (
        db.query(Advisor)
        .join(User)
        .join(Department)
        .filter(User.account_status == "active")
        .order_by(User.full_name.asc())
        .all()
    )

    return AdvisorOptionListResponse(
        data=[
            AdvisorOptionData(
                id=advisor.id,
                user_id=advisor.user_id,
                name=advisor.user.full_name,
                email=advisor.user.email,
                employee_number=advisor.employee_number,
                department_id=advisor.department_id,
                department_code=advisor.department.department_code,
            )
            for advisor in advisors
        ]
    )


@router.post(
    "/students/{user_id}/profile",
    response_model=StudentProfileResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_409_CONFLICT: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: (
            REQUEST_VALIDATION_ERROR_RESPONSE
        ),
    },
)
def create_student_profile(
    payload: CreateStudentProfileRequest,
    user_id: UUID = Path(...),
    _current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = _target_or_404(db, user_id)

    if user.role != UserRole.STUDENT.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "STUDENT_ACCOUNT_REQUIRED",
                "message": "Only a student account can receive a student profile.",
            },
        )

    if user.student is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "STUDENT_PROFILE_ALREADY_EXISTS",
                "message": "This student account already has an academic profile.",
            },
        )

    program = db.get(Program, payload.program_id)
    advisor = db.get(Advisor, payload.advisor_id)

    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PROGRAM_NOT_FOUND",
                "message": "The selected program was not found.",
            },
        )

    if advisor is None or advisor.user.account_status != "active":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ADVISOR_NOT_FOUND",
                "message": "The selected active advisor was not found.",
            },
        )

    if advisor.department_id != program.department_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "ADVISOR_PROGRAM_DEPARTMENT_MISMATCH",
                "message": (
                    "The selected advisor and program must belong to "
                    "the same department."
                ),
            },
        )

    student_number = payload.student_number.strip().upper()
    existing_number = (
        db.query(Student)
        .filter(func.lower(Student.student_number) == student_number.lower())
        .first()
    )

    if existing_number is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "STUDENT_NUMBER_ALREADY_EXISTS",
                "message": "A student profile already uses this student number.",
            },
        )

    student = Student(
        user=user,
        program=program,
        advisor=advisor,
        student_number=student_number,
        current_trimester=payload.current_trimester,
        academic_status="active",
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    return StudentProfileResponse(
        data=StudentProfileData(
            student_id=student.id,
            user_id=student.user_id,
            student_number=student.student_number,
            program_id=student.program_id,
            advisor_id=student.advisor_id,
            current_trimester=student.current_trimester,
            academic_status=student.academic_status,
        )
    )


@router.post(
    "/staff",
    response_model=AdminUserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_409_CONFLICT: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: (
            REQUEST_VALIDATION_ERROR_RESPONSE
        ),
    },
)
def create_staff_account(
    payload: CreateStaffAccountRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if (
        current_user.role == UserRole.DEPARTMENT_ADMIN.value
        and payload.role != UserRole.ADVISOR.value
    ):
        raise _forbidden(
            "Department administrators can provision advisor accounts only."
        )

    if find_user_by_email(db, str(payload.email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "EMAIL_ALREADY_REGISTERED",
                "message": "An account with this email already exists.",
            },
        )

    department = None

    if payload.role == UserRole.ADVISOR.value:
        department = db.get(Department, payload.department_id)

        if department is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "DEPARTMENT_NOT_FOUND",
                    "message": "The selected department was not found.",
                },
            )

        employee_number = payload.employee_number.strip()

        existing_employee = (
            db.query(Advisor)
            .filter(
                func.lower(Advisor.employee_number)
                == employee_number.lower()
            )
            .first()
        )

        if existing_employee is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "EMPLOYEE_NUMBER_ALREADY_REGISTERED",
                    "message": (
                        "An advisor profile already uses this employee number."
                    ),
                },
            )

    user = User(
        full_name=payload.name.strip(),
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        account_status=payload.account_status,
    )
    db.add(user)
    db.flush()

    if payload.role == UserRole.ADVISOR.value:
        db.add(
            Advisor(
                user=user,
                department=department,
                employee_number=payload.employee_number.strip(),
            )
        )

    db.commit()
    db.refresh(user)

    return AdminUserResponse(data=_user_data(user))


@router.patch(
    "/users/{user_id}/access",
    response_model=AdminUserResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: STANDARD_ERROR_RESPONSE,
        status.HTTP_403_FORBIDDEN: STANDARD_ERROR_RESPONSE,
        status.HTTP_404_NOT_FOUND: STANDARD_ERROR_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: (
            REQUEST_VALIDATION_ERROR_RESPONSE
        ),
    },
)
def update_user_access(
    payload: UpdateAccountAccessRequest,
    user_id: UUID = Path(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = _target_or_404(db, user_id)
    _ensure_can_manage(current_user, target)

    target.account_status = payload.account_status
    db.commit()
    db.refresh(target)

    return AdminUserResponse(data=_user_data(target))
