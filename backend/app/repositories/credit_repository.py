from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.program import Program
from app.models.registration import Registration, RegistrationStatus
from app.models.student import Student
from app.schemas.credit import CreditLoadValidation


ACTIVE_CREDIT_STATUSES = (
    RegistrationStatus.DRAFT.value,
    RegistrationStatus.PENDING.value,
    RegistrationStatus.APPROVED.value,
)


class CreditRepositoryError(RuntimeError):
    """Raised when a student's credit load cannot be calculated."""


class InvalidCreditLoadError(ValueError):
    def __init__(self, validation: CreditLoadValidation):
        super().__init__(validation.message)
        self.validation = validation


def selected_credit_total_query(
    db: Session,
    *,
    student_id: UUID,
):
    return (
        db.query(func.coalesce(func.sum(Course.credits), 0))
        .select_from(Registration)
        .join(Course, Registration.section_id == Course.id)
        .filter(
            Registration.student_id == student_id,
            Registration.registration_status.in_(
                ACTIVE_CREDIT_STATUSES
            ),
        )
    )


def build_credit_load_validation(
    *,
    selected_credits: int,
    minimum_credit: int,
    maximum_credit: int,
) -> CreditLoadValidation:
    if selected_credits < minimum_credit:
        minimum_shortfall = minimum_credit - selected_credits
        return CreditLoadValidation(
            selected_credits=selected_credits,
            minimum_credit=minimum_credit,
            maximum_credit=maximum_credit,
            validation_status="below_minimum",
            is_valid=False,
            minimum_shortfall=minimum_shortfall,
            maximum_excess=0,
            message=(
                "Final submission requires at least "
                f"{minimum_credit} credits; {selected_credits} "
                "credits are currently selected."
            ),
        )

    if selected_credits > maximum_credit:
        maximum_excess = selected_credits - maximum_credit
        return CreditLoadValidation(
            selected_credits=selected_credits,
            minimum_credit=minimum_credit,
            maximum_credit=maximum_credit,
            validation_status="above_maximum",
            is_valid=False,
            minimum_shortfall=0,
            maximum_excess=maximum_excess,
            message=(
                "Final submission allows at most "
                f"{maximum_credit} credits; {selected_credits} "
                "credits are currently selected."
            ),
        )

    return CreditLoadValidation(
        selected_credits=selected_credits,
        minimum_credit=minimum_credit,
        maximum_credit=maximum_credit,
        validation_status="within_range",
        is_valid=True,
        minimum_shortfall=0,
        maximum_excess=0,
        message="The selected credit load is within the allowed range.",
    )


def get_credit_load_validation(
    db: Session,
    *,
    student_id: UUID,
) -> CreditLoadValidation:
    try:
        limits = (
            db.query(
                Program.minimum_credit,
                Program.maximum_credit,
            )
            .select_from(Student)
            .join(Program, Student.program_id == Program.id)
            .filter(Student.id == student_id)
            .one_or_none()
        )

        if limits is None:
            raise CreditRepositoryError(
                "The student program credit limits are unavailable."
            )

        selected_credits = int(
            selected_credit_total_query(
                db,
                student_id=student_id,
            ).scalar()
            or 0
        )

        return build_credit_load_validation(
            selected_credits=selected_credits,
            minimum_credit=int(limits.minimum_credit),
            maximum_credit=int(limits.maximum_credit),
        )

    except CreditRepositoryError:
        raise
    except Exception as error:
        raise CreditRepositoryError(str(error)) from error


def require_valid_credit_load(
    db: Session,
    *,
    student_id: UUID,
) -> CreditLoadValidation:
    validation = get_credit_load_validation(
        db,
        student_id=student_id,
    )

    if not validation.is_valid:
        raise InvalidCreditLoadError(validation)

    return validation
